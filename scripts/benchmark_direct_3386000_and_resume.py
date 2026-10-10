"""One-shot authorized direct-server benchmark and resume of the current plan."""
import json
import argparse
import os
from pathlib import Path
import subprocess
import time

from eval_scheduler.database_cli import assert_runner_stopped
from eval_scheduler.model import JobStatus
from eval_scheduler.runtime import gpu_snapshot
from eval_scheduler.store import SQLiteJobStore
from scripts.stop_training_at_complete_checkpoint import complete

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT/'logs/scheduler/dfm12_XL_epoch11_noidentity'
PYTHON = '/home/ucloud/miniforge3/envs/hrm/bin/python'


def wait_idle(control, timeout=1200):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        if (control/'stopped.json').exists():
            try:
                assert_runner_stopped(PLAN)
                snapshots = [gpu_snapshot(g) for g in range(8)]
                if all(float(free) >= .98*float(total) for free, _, total in snapshots):
                    return
            except ValueError:
                pass
        time.sleep(2)
    raise RuntimeError('Training or GPU work has not stopped; refusing concurrent launch')


def prepare_resume(control, tag):
    source = ROOT/'checkpoints/dfm14/XL-from-dfm13-step3250000'
    assert complete(source, tag)
    store = SQLiteJobStore(json.loads((PLAN/'database.json').read_text())['database'])
    store.backup(control/'before-resume.sqlite')
    jobs = {j.job_id: j for j in store.load_jobs()}
    key = 'dfm14-xl-step_3400000-train'
    assert not any(j.status == JobStatus.RUNNING for j in jobs.values())
    store.update_jobs({key: dict(metadata={**jobs[key].metadata,
        'resume_from_tag': tag, 'resume_ckpt_path': str(source)})})
    store.update_jobs({key: dict(status=JobStatus.PENDING, attempt=0)})
    store.backup(PLAN/'state.backup.sqlite')
    store.export_tsv(PLAN/'plan.snapshot.tsv')


def resume(control, tag, max_clients):
    wait_idle(control, timeout=180)
    (PLAN/'stop.request').unlink(missing_ok=True)
    command = [PYTHON, '-m', 'eval_scheduler', 'run', '--plan-dir', str(PLAN),
        '--backend', 'sqlite', '--gpus', '0,1,2,3,4,5,6,7',
        '--persistent-vllm', '--max-clients', str(max_clients)]
    env = dict(os.environ, PATH=str(Path(PYTHON).parent)+':'+os.environ['PATH'],
               PYTHONPATH='eval_scheduler:.')
    assert env.get('WANDB_MODE') not in ('disabled', 'offline')
    with (PLAN/f'resume-{tag}-direct.log').open('w') as log:
        proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log,
            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    (control/'resumed.json').write_text(json.dumps(dict(pid=proc.pid,
        checkpoint=tag, command=command, time=time.time()), indent=2)+'\n')
    print('Production resumed with direct server pool', proc.pid, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--step', type=int, required=True)
    parser.add_argument('--max-clients', type=int, default=32)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    control = ROOT/f'logs/scheduler/multilingual100-{args.step}-control'
    tag = f'ephemeral_step_{args.step}'
    assert args.max_clients > 0 and not args.output.exists()
    wait_idle(control)
    prepare_resume(control, tag)
    try:
        with (control/'benchmark.log').open('w') as log:
            code = subprocess.call([PYTHON, '-m', 'eval_scheduler.benchmark_multilingual',
                str(PLAN/'plan.snapshot.tsv'), str(args.output), '--max-clients', str(args.max_clients),
                '--modes', 'direct'], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        print('Benchmark exit', code, flush=True)
    finally:
        resume(control, tag, args.max_clients)


if __name__ == '__main__':
    main()
