"""Authorized one-shot benchmark handoff, with conditional production resume."""
import json
import os
from pathlib import Path
import subprocess
import time

from eval_scheduler.database_cli import assert_runner_stopped, publish_database_marker
from eval_scheduler.locking import PlanLock
from eval_scheduler.model import Action, JobStatus, read_plan, write_plan
from eval_scheduler.runtime import gpu_snapshot
from eval_scheduler.store import SQLiteJobStore
from scripts.stop_training_at_complete_checkpoint import complete

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT/'logs/scheduler/dfm12_XL_epoch11_noidentity'
CONTROL = ROOT/'logs/scheduler/multilingual100-3383000-control'
OUTPUT = ROOT/'logs/scheduler/multilingual100-comparison-3383000'
PYTHON = '/home/ucloud/miniforge3/envs/hrm/bin/python'
TAG = 'ephemeral_step_3383000'


def wait_stopped():
    deadline = time.monotonic()+900
    while time.monotonic() < deadline:
        if (CONTROL/'stopped.json').exists():
            try:
                assert_runner_stopped(PLAN)
                if all(float(gpu_snapshot(g)[0]) >= .98*float(gpu_snapshot(g)[2]) for g in range(8)):
                    return
            except ValueError:
                pass
        time.sleep(2)
    raise RuntimeError('Checkpoint-safe pause did not complete; no benchmark launched')


def prepare_resume():
    source = ROOT/'checkpoints/dfm14/XL-from-dfm13-step3250000'
    assert complete(source, TAG)
    with PlanLock(PLAN, exclusive=True):
        jobs = read_plan(PLAN/'plan.tsv')
        write_plan(CONTROL/'plan.before-resume.tsv', jobs)
        updated = []
        for job in jobs:
            if job.job_id == 'dfm14-xl-step_3400000-train':
                job = job.with_updates(status=JobStatus.PENDING, attempt=0,
                    metadata=dict(job.metadata, resume_from_tag=TAG, resume_ckpt_path=str(source)))
            elif job.status == JobStatus.RUNNING:
                if job.action != Action.WAIT_CHECKPOINT:
                    raise RuntimeError('Unexpected active row '+job.job_id)
                job = job.with_updates(status=JobStatus.PENDING)
            updated.append(job)
        assert any(j.job_id == 'dfm14-xl-step_3400000-train' for j in updated)
        write_plan(PLAN/'plan.tsv', updated)


def resume(shared):
    assert_runner_stopped(PLAN)
    assert all(float(gpu_snapshot(g)[0]) >= .98*float(gpu_snapshot(g)[2]) for g in range(8)), 'GPU cleanup incomplete'
    backend = 'sqlite' if shared else 'tsv'
    if shared:
        database = Path('/tmp/dfm14-production-3383000/jobs.sqlite')
        assert not database.exists() and not (PLAN/'database.json').exists()
        database.parent.mkdir(parents=True, exist_ok=True)
        with PlanLock(PLAN, exclusive=True):
            jobs = read_plan(PLAN/'plan.tsv')
            assert not any(j.status == JobStatus.RUNNING for j in jobs)
            store = SQLiteJobStore(database)
            store.import_jobs(jobs)
            store.backup(PLAN/'state.backup.sqlite')
            publish_database_marker(PLAN, database)
    (PLAN/'stop.request').unlink(missing_ok=True)
    command = [PYTHON, '-m', 'eval_scheduler', 'run', '--plan-dir', str(PLAN),
               '--backend', backend, '--gpus', '0,1,2,3,4,5,6,7', '--persistent-vllm']
    if shared:
        command += ['--max-clients', '32']
    env = dict(os.environ, PATH=str(Path(PYTHON).parent)+':'+os.environ['PATH'],
               PYTHONPATH='eval_scheduler:.')
    assert env.get('WANDB_MODE') not in ('disabled', 'offline')
    with (PLAN/f'resume-3383000-{backend}.log').open('w') as log:
        proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, start_new_session=True)
    (CONTROL/'resumed.json').write_text(json.dumps(dict(backend=backend, pid=proc.pid,
        checkpoint=TAG, command=command, time=time.time()), indent=2)+'\n')
    print('Production resumed via '+backend, proc.pid, flush=True)


def main():
    wait_stopped()
    prepare_resume()
    try:
        with (CONTROL/'benchmark.log').open('w') as log:
            code = subprocess.call([PYTHON, '-m', 'eval_scheduler.benchmark_multilingual',
                str(PLAN/'plan.tsv'), str(OUTPUT), '--max-clients', '32'], cwd=ROOT,
                stdout=log, stderr=subprocess.STDOUT)
        print('Benchmark exit', code, flush=True)
    finally:
        report = json.loads((OUTPUT/'result.json').read_text()) if (OUTPUT/'result.json').exists() else {}
        shared = report.get('modes', {}).get('shared', {}).get('complete') is True
        resume(shared)


if __name__ == '__main__':
    main()
