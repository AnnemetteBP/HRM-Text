"""Resume the paused DFM14 campaign after five minutes of all-GPU idle."""
import os
from pathlib import Path
import subprocess
import time

import psutil

from dfm14.continue_training import (
    PLAN, PREFIX, PY, PlanLock, JobStatus, read_plan, write_plan, complete,
    training_gpus_free,
)


def idle():
    result = subprocess.run(
        ['nvidia-smi', '--query-gpu=index,utilization.gpu',
         '--format=csv,noheader,nounits'], capture_output=True, text=True,
        check=True, timeout=15,
    )
    values = {int(a.strip()): int(b.strip()) for a, b in
              (line.split(',') for line in result.stdout.splitlines())}
    return all(values.get(i) == 0 for i in range(8))


def main():
    root = Path('checkpoints/dfm14/XXL-wide-paused-873000').resolve()
    tag = 'ephemeral_step_873000'
    assert complete(root, tag), 'Preserved checkpoint incomplete'
    # Snapshot exact server identities; never kill replacement processes.
    servers = []
    for proc in psutil.process_iter(['cmdline']):
        cmd = proc.info['cmdline'] or []
        if ('vllm.entrypoints.openai.api_server' in cmd
                and '/tmp/mimir-smoke-182/model' in cmd
                and '--port' in cmd
                and int(cmd[cmd.index('--port') + 1]) in range(8200, 8208)):
            servers.append(proc)
    print('Watching; server PIDs:', [p.pid for p in servers], flush=True)
    since = None
    while True:
        try:
            quiet = idle()
        except (ValueError, subprocess.SubprocessError):
            quiet = False
        since = (since if since is not None else time.monotonic()) if quiet else None
        elapsed = time.monotonic() - since if since is not None else 0
        print(time.strftime('%FT%T'), f'idle={quiet} consecutive={elapsed:.0f}/300s', flush=True)
        if elapsed >= 300:
            break
        time.sleep(10)
    targets = {}
    for proc in servers:
        if proc.is_running():
            for child in proc.children(recursive=True):
                targets[child.pid] = child
            targets[proc.pid] = proc
    for proc in targets.values():
        try:
            proc.terminate()
        except psutil.NoSuchProcess:
            pass
    _, alive = psutil.wait_procs(list(targets.values()), timeout=60)
    for proc in alive:
        proc.kill()
    print('Stopped identified vLLM servers; waiting for empty GPUs', flush=True)
    while not training_gpus_free():
        time.sleep(30)
    with PlanLock(PLAN):
        jobs = read_plan(PLAN/'plan.tsv')
        jobs = [j.with_updates(status=JobStatus.PENDING, attempt=0,
                    metadata={**j.metadata, 'resume_ckpt_path': str(root),
                              'resume_from_tag': tag})
                if j.job_id == PREFIX+'train-900000' else j for j in jobs]
        write_plan(PLAN/'plan.tsv', jobs)
    subprocess.run([PY, '-m', 'eval_scheduler', 'clear-stop', '--plan-dir', str(PLAN)], check=True)
    env = dict(os.environ, PATH=str(Path(PY).parent)+':'+os.environ['PATH'])
    with (PLAN/'runner.log').open('a') as log:
        proc = subprocess.Popen([PY, '-u', '-m', 'eval_scheduler', 'run',
            '--plan-dir', str(PLAN), '--gpus', '0,1,2,3,4,5,6,7', '--persistent-vllm'],
            env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    print('Scheduler resumed from 873000; PID', proc.pid, flush=True)


if __name__ == '__main__':
    main()
