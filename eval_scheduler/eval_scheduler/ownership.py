"""Durable process identity evidence for explicit crash recovery, never auto-kill."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
from threading import local
import time


_owner = local()


@contextmanager
def process_owner(directory, **identity):
    previous = getattr(_owner, 'value', None)
    _owner.value = (Path(directory), identity)
    try:
        yield
    finally:
        _owner.value = previous


def process_identity(pid):
    # comm can contain spaces and parentheses; fields after the last ')' start at state.
    fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
    return {'pid': pid, 'start_ticks': int(fields[19]),
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def spawn(*args, **kwargs):
    proc = subprocess.Popen(*args, **kwargs)
    owner = getattr(_owner, 'value', None)
    if owner is None:
        return proc
    try:
        directory, identity = owner
        try:
            process = process_identity(proc.pid)
        except FileNotFoundError:
            if proc.poll() is None:
                raise
            process = {'pid': proc.pid, 'exited_before_record': True}
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f'{proc.pid}-{time.time_ns()}.json'
        temporary = path.with_suffix('.tmp')
        with temporary.open('x') as handle:
            json.dump({**identity, **process, 'owner_pid': os.getpid(), 'created_at': time.time()}, handle)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
        temporary.replace(path)
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except BaseException:
        # Never leave an unrecorded child behind after a ledger failure.
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait(timeout=10)
        raise
    return proc
