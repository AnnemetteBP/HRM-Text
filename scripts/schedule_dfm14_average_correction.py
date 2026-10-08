"""Queue the corrected 3250K population baseline in an exclusive writer window."""
from pathlib import Path

from dfm12.io import load, write_json
from scripts.schedule_dfm14_eval_extension import PLAN, Action, JobStatus, PlanLock, read_plan, write_plan, check_graph

ID = 'dfm14-xl-correct-3250k-populations-v2'
CONTROL = Path('data/dfm14/average-epoch-correction-3250k')


def build(jobs):
    if any(j.job_id == ID for j in jobs):
        raise ValueError('Correction already scheduled')
    original = next(j for j in jobs if j.job_id == 'dfm14-eval-3250000-average')
    parent = next(j for j in jobs if j.action == Action.EXPORT_HF
                  and j.metadata.get('eval_step') == 3250000)
    train = next(j for j in jobs if j.job_id == 'dfm14-xl-step_3300000-train')
    if original.status != JobStatus.DONE or parent.status != JobStatus.DONE:
        raise ValueError('Baseline inputs not finalized')
    if parent.metadata.get('dfm13_cursor_epoch_pending'):
        raise ValueError('Parent epoch is not finalized')
    correction = original.with_updates(job_id=ID, name='corrected-50-language-baseline-v2',
        deps=(train.job_id,), status=JobStatus.PENDING, attempt=0,
        log_dir=str(CONTROL / 'sync'), metadata={**original.metadata,
            'eval_epoch': parent.metadata['eval_epoch'], 'dfm13_cursor_epoch_pending': False,
            'log_wandb': True, 'population_require_complete': True})
    out = []
    gates = 0
    for job in jobs:
        if (job.action == Action.WAIT_CHECKPOINT and job.metadata.get('eval_step') == 3300000
                and job.status == JobStatus.PENDING):
            job = job.with_updates(deps=tuple(dict.fromkeys((*job.deps, ID))))
            gates += 1
        out.append(job)
    if gates != 1:
        raise ValueError('Expected one unstarted 3300K evaluation boundary')
    out.append(correction)
    check_graph(out)
    return out


def main():
    proof = load(CONTROL / 'preview.json')
    populations = proof['coverage']['populations']
    if len(populations) != 3 or not all(p['complete'] for p in populations.values()):
        raise ValueError('Corrected baseline still incomplete')
    with PlanLock(PLAN):
        before = read_plan(PLAN / 'plan.tsv')
        after = build(before)
        row = after[-1]
        if proof['row']['avg_population/epoch'] != row.metadata['eval_epoch']:
            raise ValueError('Preview epoch mismatch')
        write_plan(CONTROL / 'plan-before.tsv', before)
        write_plan(PLAN / 'plan.tsv', after)
        write_json(CONTROL / 'queued.json', dict(job_id=ID, epoch=row.metadata['eval_epoch'],
                   after='3300K training, before its evaluations', no_live_wandb_write=True))


if __name__ == '__main__':
    main()
