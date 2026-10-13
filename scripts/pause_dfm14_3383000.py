"""Checkpoint-safe pause for the authorized shared/legacy benchmark."""
import os
import argparse
from pathlib import Path
import signal
import time

from dfm12.io import write_json
from dfm12.diagnostic_server import identity, pidfd_open, pidfd_signal
from scripts.stop_training_at_complete_checkpoint import complete, preserve, alive

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'logs/scheduler/multilingual100-3383000-control'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--step', type=int, default=3383000)
    parser.add_argument('--pid', type=int, default=1089820)
    args = parser.parse_args()
    work = ROOT / f'logs/scheduler/multilingual100-{args.step}-control'
    work.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'checkpoints/dfm14/XL-from-dfm13-step3250000'
    target = ROOT / f'checkpoints/preserved/dfm14-shared-benchmark-{args.step}'
    tag, pid = f'ephemeral_step_{args.step}', args.pid
    command = Path(f'/proc/{pid}/cmdline').read_bytes()
    assert b'torchrun' in command and b'data=dfm14' in command and b'stop_after_step=3400000' in command
    owner, fd = identity(pid), pidfd_open(pid)
    stop = ROOT / 'logs/scheduler/dfm12_XL_epoch11_noidentity/stop.request'
    marker = stop.read_bytes()
    write_json(work/'armed.json', dict(owner=owner, tag=tag, watcher_pid=os.getpid()))
    try:
        while not complete(source, tag):
            if not alive(pid) or identity(pid)['start_ticks'] != owner['start_ticks']:
                raise RuntimeError('Training ownership changed')
            time.sleep(1)
        preserve(source, target, tag)
        assert stop.read_bytes() == marker
        assert identity(pid)['start_ticks'] == owner['start_ticks']
        assert Path(f'/proc/{pid}/cmdline').read_bytes() == command
        pidfd_signal(fd, signal.SIGTERM)
        deadline = time.monotonic()+180
        while alive(pid):
            if time.monotonic() > deadline:
                raise RuntimeError('Training did not stop')
            time.sleep(1)
        write_json(work/'stopped.json', dict(tag=tag, checkpoint=str(source), preserved=str(target), time=time.time()))
        print('Stopped at preserved '+tag, flush=True)
    finally:
        os.close(fd)


if __name__ == '__main__':
    main()
