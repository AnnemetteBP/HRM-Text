"""Evaluation failure must not block an otherwise valid training resume."""
from .model import Action, Job, JobStatus


def allow_failed_evals(jobs: list[Job], minimum_step: int) -> list[Job]:
    from .database_cli import validate_graph

    by_id = {job.job_id: job for job in jobs}
    changes, additions = {}, []
    for job in jobs:
        if (job.action != Action.TRAIN_UNTIL_STEP or job.status != JobStatus.PENDING
                or int(job.metadata.get('eval_step', 0)) < minimum_step):
            continue
        gate_id = job.job_id + '-evals-terminal'
        if gate_id in by_id:
            continue
        # Preserve successful training ancestry independently of eval success.
        # Stop at the nearest training ancestors, not their older campaigns.
        previous, seen, todo = set(), set(), list(job.deps)
        while todo:
            dep = todo.pop()
            if dep in seen:
                continue
            seen.add(dep)
            parent = by_id[dep]
            if parent.action == Action.TRAIN_UNTIL_STEP:
                previous.add(dep)
            else:
                todo.extend(parent.deps)
        if not previous:
            raise ValueError(f'{job.job_id}: cannot identify successful training prerequisite')
        additions.append(Job(gate_id, Action.TERMINAL_BARRIER, 'control', 'evals-terminal',
                             deps=job.deps, deps_mode='terminal',
                             metadata={'eval_step': job.metadata['eval_step']}))
        changes[job.job_id] = job.with_updates(deps=(*sorted(previous), gate_id), deps_mode='success')
    result = [changes.get(j.job_id, j) for j in jobs] + additions
    validate_graph(result)
    return result
