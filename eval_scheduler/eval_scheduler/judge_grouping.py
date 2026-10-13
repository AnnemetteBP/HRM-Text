"""Plan-only judge-first grouping; never changes inference or scoring settings."""
from hashlib import sha256

from .model import Action, Job, JobStatus
from .runtime import managed_judge_enabled


INFERENCE = {Action.EVAL_STANDARD, Action.EVAL_DFM, Action.EVAL_DFM_IFEVAL,
             Action.EVAL_EUROEVAL, Action.EVAL_EUROEVAL_BATCHED_IFEVAL}


def group_judged_first(jobs: list[Job], minimum_step: int) -> list[Job]:
    from .database_cli import validate_graph

    groups = {}
    for job in jobs:
        step = job.metadata.get('eval_step')
        if step is None or int(step) < minimum_step or job.status == JobStatus.SKIPPED:
            continue
        key = (int(step), str(job.metadata.get('ckpt_path', '')),
               str(job.metadata.get('wandb_run_id', '')))
        groups.setdefault(key, []).append(job)
    changes, additions = {}, []
    ids = {j.job_id for j in jobs}
    for key, group in groups.items():
        inference = [j for j in group if j.action in INFERENCE]
        if not inference or any(j.status != JobStatus.PENDING for j in inference):
            continue
        judged = [j for j in inference if managed_judge_enabled(j)]
        if not judged:
            continue
        gate_id = f'judge-first-{key[0]}-' + sha256(repr(key).encode()).hexdigest()[:12]
        gate = Job(gate_id, Action.TERMINAL_BARRIER, 'control', 'judged-phase-complete',
                   deps=tuple(j.job_id for j in judged), deps_mode='terminal',
                   metadata={'eval_step': key[0]})
        if gate_id not in ids:
            additions.append(gate)
        else:
            changes[gate_id] = gate
        for job in inference:
            if not managed_judge_enabled(job) and gate_id not in job.deps:
                changes[job.job_id] = job.with_updates(deps=(*job.deps, gate_id))
        # The runner drains servers before exclusive training/export already.
        # Retain old suite dependency gates without destroying reusable servers.
        for job in group:
            if job.action == Action.TEARDOWN_EVAL and job.status == JobStatus.PENDING:
                changes[job.job_id] = job.with_updates(action=Action.TERMINAL_BARRIER)
    result = [changes.get(j.job_id, j) for j in jobs] + additions
    validate_graph(result)
    return result
