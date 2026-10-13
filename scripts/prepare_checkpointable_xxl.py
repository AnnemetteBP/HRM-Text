"""Prepare the existing DFM14 XXL-wide plan for continuous checkpointable training."""
import argparse
from pathlib import Path
import shlex
import sys

from eval_scheduler.model import Action, JobStatus
from eval_scheduler.store import SQLiteJobStore
from training_suspend.protocol import read_json
from training_suspend.supervisor import overrides


def prepare(jobs, plan, control, settings):
    training = sorted((j for j in jobs if j.job_id.startswith('xxlw-dfm14-train-')
                       and j.action == Action.TRAIN_UNTIL_STEP
                       and int(j.metadata['stop_after_step']) > 1000000),
                      key=lambda j: int(j.metadata['stop_after_step']))
    if not training or any(j.status != JobStatus.PENDING for j in training):
        raise RuntimeError('Expected only pending post-1M training rows')
    if len({str(j.metadata['command']) for j in training}) != 1:
        raise RuntimeError('Future training settings differ; do not flatten an LR or architecture schedule')
    raw = shlex.split(training[0].metadata['command'])
    separator = raw.index('--')
    assignments = [s for s in raw[:separator] if '=' in s and not s.startswith('-')]
    command = raw[separator+1:]
    if 'pretrain.py' not in command:
        raise RuntimeError('Expected the standard torchrun pretrain.py command')
    boundaries = [int(j.metadata['stop_after_step']) for j in training[:-1]]
    command = assignments + overrides(command, {
        'stop_after_step': training[-1].metadata['stop_after_step'],
        'suspend_after_steps': str(boundaries).replace(' ', ''),
        'suspend_poll_interval_steps': 10, 'suspend_wait_poll_seconds': 2,
    })
    config = read_json(settings)
    changes = {}
    previous = 1000000
    by_id = {j.job_id: j for j in jobs}
    for job in training:
        target = int(job.metadata['stop_after_step'])
        co = dict(control_root=str(control), command=command, python=sys.executable,
                  launcher_settings=str(settings), cuda_checkpoint=config['cuda_checkpoint'],
                  final_boundary=job == training[-1],
                  finalize_command=[sys.executable, '-m', 'dfm14.continue_training', 'finalize',
                                    f'stop_after_step={target}'])
        changes[job.job_id] = {'metadata': {**job.metadata, 'cooperative_training': co}}
        gate = job.job_id + '-evals-terminal'
        if gate not in by_id or by_id[gate].status != JobStatus.PENDING:
            raise RuntimeError('Missing pending terminal eval gate')
        evals = tuple(j.job_id for j in jobs if j.job_id.startswith(f'xxlw-dfm14-{previous}-')
                      and j.action.value.startswith('eval_'))
        if not evals:
            raise RuntimeError(f'No inference rows for {previous}')
        changes[gate] = {'deps': evals, 'deps_mode': 'terminal'}
        previous = target
    return changes, boundaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--plan-dir', type=Path, required=True)
    parser.add_argument('--control-root', type=Path, required=True)
    parser.add_argument('--settings', type=Path, default=Path('config/training_suspend_b200.json'))
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    store = SQLiteJobStore(args.database)
    changes, boundaries = prepare(store.load_jobs(), args.plan_dir.resolve(),
                                  args.control_root.resolve(), args.settings.resolve())
    print(f'{len(changes)} pending definitions; suspensions {boundaries}')
    if not args.apply:
        return
    if store.get_admin_lock():
        raise RuntimeError('Another administrator holds the dispatch lock')
    store.set_admin_lock(True)
    try:
        changes, _ = prepare(store.load_jobs(), args.plan_dir.resolve(),
                             args.control_root.resolve(), args.settings.resolve())
        backup = args.plan_dir / 'before-cooperative-training.sqlite'
        if backup.exists():
            raise RuntimeError('Backup already exists; inspect before applying again')
        store.backup(backup)
        store.update_jobs(changes)
        store.export_tsv(args.plan_dir / 'plan.tsv')
        store.backup(args.plan_dir / 'state.backup.sqlite')
    finally:
        store.set_admin_lock(False)
    print('Prepared pending rows; active training was not edited')


if __name__ == '__main__':
    main()
