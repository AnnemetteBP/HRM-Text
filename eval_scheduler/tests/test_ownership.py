import json
import os
import subprocess
import sys

import pytest

from eval_scheduler.ownership import process_identity, process_owner, spawn


def test_identity_and_owner_receipt(tmp_path):
    assert process_identity(os.getpid())['start_ticks'] > 0
    with process_owner(tmp_path, job_id='a', token='attempt-1'):
        child = spawn([sys.executable, '-c', 'import time; time.sleep(30)'])
    try:
        receipt = json.loads(next(tmp_path.glob('*.json')).read_text())
        assert receipt['pid'] == child.pid
        assert receipt['start_ticks'] == process_identity(child.pid)['start_ticks']
        assert receipt['token'] == 'attempt-1'
    finally:
        child.terminate(); child.wait(timeout=10)
    # Outside the opt-in owner context there is no filesystem work.
    spawn([sys.executable, '-c', 'pass']).wait(timeout=10)
    assert len(list(tmp_path.glob('*.json'))) == 1


def test_receipt_failure_terminates_exact_owned_process(tmp_path, monkeypatch):
    bad = tmp_path/'file'; bad.write_text('not a directory')
    created = []
    original = subprocess.Popen
    def launch(*a, **kw):
        proc = original(*a, **kw); created.append(proc); return proc
    monkeypatch.setattr(subprocess, 'Popen', launch)
    with process_owner(bad, job_id='test'):
        with pytest.raises(FileExistsError):
            spawn([sys.executable, '-c', 'import time; time.sleep(30)'])
    assert len(created) == 1 and created[0].poll() is not None
