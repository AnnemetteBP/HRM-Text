"""Drain the current XXL-wide segment, then migrate its existing eval campaign."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'eval_scheduler'))
sys.path.insert(0, str(ROOT))
from eval_scheduler.database_cli import assert_runner_stopped
from eval_scheduler.judge_grouping import group_judged_first
from eval_scheduler.locking import PlanLock
from eval_scheduler.model import JobStatus, read_plan, write_plan
from eval_scheduler.store import SQLiteJobStore
from eval_scheduler.training_continuation import allow_failed_evals
from scripts.stop_training_at_complete_checkpoint import complete

PREFIX = 'xxlw-dfm14-'


def policies(jobs, boundary):
    revised = [j.with_updates(metadata={**j.metadata, 'eval_step':j.metadata['dfm14_boundary']})
               if j.status == JobStatus.PENDING and j.job_id.startswith(PREFIX)
               and 'dfm14_boundary' in j.metadata and 'eval_step' not in j.metadata
               else j for j in jobs]
    revised = allow_failed_evals(group_judged_first(revised, boundary), boundary)
    before = {j.job_id:j for j in jobs}
    for job in revised:
        old = before.get(job.job_id)
        if old and old != job:
            if old.status != JobStatus.PENDING or not job.job_id.startswith(PREFIX):
                raise RuntimeError('Unexpected migration change: '+job.job_id)
            # This migration must not change model, scorer, training or launch options.
            if {k:v for k,v in old.metadata.items() if k != 'eval_step'} != {
                    k:v for k,v in job.metadata.items() if k != 'eval_step'}:
                raise RuntimeError('Unexpected metadata change: '+job.job_id)
    return revised


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--plan-dir', type=Path, required=True)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--old-runner-pid', type=int, required=True)
    parser.add_argument('--boundary', type=int, default=950000)
    parser.add_argument('--monitor-pane', default='%2')
    args = parser.parse_args()
    os.chdir(ROOT)
    plan = args.plan_dir.resolve()
    env = dict(os.environ)
    cuda = Path(sys.prefix)/'lib/python3.13/site-packages/nvidia/cu13'
    env.update(CUDA_HOME=str(cuda), CONDA_PREFIX=sys.prefix,
               PATH=f'{Path(sys.executable).parent}:{cuda}/bin:'+env['PATH'])
    cli = [sys.executable, '-m', 'eval_scheduler']

    def run(*command):
        return subprocess.run(command, env=env, check=True)

    with (plan/'sqlite-migration.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (plan/'database.json').exists() or args.database.exists():
            raise RuntimeError('Already migrated or partial database exists; inspect before retry')
        process = psutil.Process(args.old_runner_pid)
        command = process.cmdline()
        if 'eval_scheduler' not in command or 'run' not in command or '--plan-dir' not in command:
            raise RuntimeError('PID is not an eval scheduler runner')
        if Path(command[command.index('--plan-dir')+1]).resolve() != plan:
            raise RuntimeError('Runner belongs to a different plan')
        run(str(cuda/'bin/nvcc'), '--version')
        run(*cli, 'stop', '--plan-dir', str(plan))
        print('Waiting for legacy runner to drain; training is not interrupted.', flush=True)
        while process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
            if not (plan/'stop.request').exists():
                raise RuntimeError('Stop request was cleared; abandoning automatic migration')
            time.sleep(30)
        with PlanLock(plan):
            assert_runner_stopped(plan)
            jobs = read_plan(plan/'plan.tsv')
            if any(j.status == JobStatus.RUNNING for j in jobs):
                raise RuntimeError('Unreconciled running rows; refusing migration')
            training = next(j for j in jobs if j.job_id == PREFIX+f'train-{args.boundary}')
            if training.status != JobStatus.DONE:
                raise RuntimeError('Boundary training did not finish successfully')
            if not complete(Path(training.metadata['ckpt_path']), f'step_{args.boundary}'):
                raise RuntimeError('Boundary checkpoint is incomplete')
            stamp = time.strftime('%Y%m%dT%H%M%S')
            write_plan(plan/f'plan.pre-sqlite-{stamp}.tsv', jobs)
            revised = policies(jobs, args.boundary)
            write_plan(plan/'plan.tsv', revised)
        run(*cli, 'database', 'preflight', '--plan-dir', str(plan))
        run(*cli, 'database', 'import', '--source', str(plan/'plan.tsv'),
            '--plan-dir', str(plan), '--database', str(args.database), '--runners-stopped')
        SQLiteJobStore(args.database).backup(plan/'state.backup.sqlite')
        run(*cli, 'clear-stop', '--plan-dir', str(plan))
        command = [*cli, 'run', '--plan-dir', str(plan), '--backend', 'sqlite',
                   '--persistent-vllm', '--gpus', '0,1,2,3,4,5,6,7',
                   '--max-clients', '64', '--server-concurrency', '1024',
                   '--cpu-cores', '256', '--reserve-cores', '8']
        with (plan/'runner-sqlite.log').open('a') as output:
            runner = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL,
                                      stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        receipt = {'runner_pid':runner.pid, 'database':str(args.database),
                   'command':command, 'migration_time':stamp, 'rows':len(revised),
                   'added_gates':len(revised)-len(jobs)}
        (plan/'sqlite-migration.json').write_text(json.dumps(receipt, indent=2)+'\n')
        monitor = shlex.join([*cli, 'monitor', '--plan-dir', str(plan), '--rich', '--interval', '30'])
        # Only replace the previously identified monitor, never an arbitrary pane.
        pane_pid = subprocess.check_output(['tmux', 'display-message', '-p', '-t',
                                           args.monitor_pane, '#{pane_pid}'], text=True).strip()
        old_monitor = psutil.Process(int(pane_pid)).cmdline()
        if 'eval_scheduler' in old_monitor and 'monitor' in old_monitor:
            run('tmux', 'respawn-pane', '-k', '-t', args.monitor_pane, monitor)
        else:
            print('Monitor pane changed; leave it untouched. Run:', monitor, flush=True)
        time.sleep(15)
        if runner.poll() is not None:
            raise RuntimeError('SQLite runner exited; inspect runner-sqlite.log')
        print('SQLite scheduler and Rich monitor started:', json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
