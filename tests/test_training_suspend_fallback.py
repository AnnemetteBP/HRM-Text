import json
from pathlib import Path
import subprocess
import sys
import time
import tempfile
import unittest
from unittest.mock import patch

from training_suspend.protocol import atomic_write
from training_suspend.supervisor import restart_command, restore_or_fail, verified_checkpoint, overrides


class RecoveryTests(unittest.TestCase):
    def test_cleanup_handles_worker_sessions_without_touching_peer(self):
        from training_suspend.supervisor import stop_owned, remember_owned
        from training_suspend.protocol import process_identity
        child_code = 'import time; time.sleep(60)'
        code = ('import subprocess,sys,time; '
                f'subprocess.Popen([sys.executable,"-c",{child_code!r}],start_new_session=True); '
                'time.sleep(60)')
        peer = subprocess.Popen([sys.executable, '-c', child_code])
        proc = subprocess.Popen([sys.executable, '-c', code], start_new_session=True)
        proc.launch_identity = process_identity(proc.pid)
        try:
            for _ in range(100):
                owned = remember_owned(proc)
                if len(owned) >= 2:
                    break
                time.sleep(.01)
            self.assertGreaterEqual(len(owned), 2)
            stop_owned(proc, {'ranks': list(owned.values())})
            self.assertIsNotNone(proc.poll())
            self.assertIsNone(peer.poll())
        finally:
            if proc.poll() is None:
                stop_owned(proc)
            peer.terminate()
            peer.wait()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ready = {'job_id': 'one', 'generation': 1, 'step': 20,
                      'checkpoint': str(self.root / 'checkpoint_state_step_20.json')}
        atomic_write(self.ready['checkpoint'], {'step': 20, 'carry_policy': 'none'})
        atomic_write(self.root / 'suspend_ready.json', self.ready)
        atomic_write(self.root / 'queue.json', {'job_id': 'one', 'pending': [30, 40]})

    @patch('scripts.stop_training_at_complete_checkpoint.complete', return_value=True)
    def test_restart_preserves_training_settings_and_remaining_requests(self, _):
        atomic_write(self.root / 'suspend_after_steps', '15 50\n')
        command = ['torchrun', 'pretrain.py', 'lr=0.0003', 'wandb_run_id=same',
                   '+resume_step=1', 'resume_epoch=1', 'reset_ema_on_resume=true',
                   'stop_after_step=100', 'suspend_after_steps=[20,30]']
        result = restart_command(command, self.root, self.ready)
        for arg in ['lr=0.0003', 'wandb_run_id=same', 'resume_step=null',
                    'resume_epoch=null', 'reset_ema_on_resume=false',
                    'resume_checkpoint_tag=step_20', 'stop_after_step=100',
                    'suspend_after_steps=[30,40,50]']:
            self.assertIn(arg, result)
        self.assertNotIn('+resume_step=1', result)

    @patch('scripts.stop_training_at_complete_checkpoint.complete', return_value=False)
    def test_incomplete_checkpoint_fails_closed(self, _):
        with self.assertRaisesRegex(RuntimeError, 'Incomplete'):
            verified_checkpoint(self.ready)

    def test_mismatch_and_carry_rejected(self):
        for state in [{'step': 19, 'carry_policy': 'none'}, {'step': 20, 'carry_policy': 'per_rank'}]:
            atomic_write(self.ready['checkpoint'], state)
            with self.assertRaises(RuntimeError):
                verified_checkpoint(self.ready)

    @patch('training_suspend.supervisor.subprocess.run')
    def test_busy_gpu_defers_without_failure(self, run):
        run.return_value = subprocess.CompletedProcess([], 75)
        self.assertFalse(restore_or_fail(self.root, '/unused', 1, 1))

    @patch('training_suspend.supervisor.subprocess.run')
    def test_restore_failure_propagates_to_fallback(self, run):
        run.return_value = subprocess.CompletedProcess([], 1)
        with self.assertRaises(subprocess.CalledProcessError):
            restore_or_fail(self.root, '/unused', 1, 1)

    @patch('training_suspend.supervisor.subprocess.run')
    def test_restore_requires_rank_acknowledgement(self, run):
        run.return_value = subprocess.CompletedProcess([], 0)
        with self.assertRaises(TimeoutError):
            restore_or_fail(self.root, '/unused', 1, 0)
        atomic_write(self.root / 'resumed.json', self.ready)
        self.assertTrue(restore_or_fail(self.root, '/unused', 1, 1))

    def test_override_removes_hydra_plus_alias(self):
        self.assertEqual(overrides(['pretrain.py', '++suspend_after_steps=[1]'],
                                   {'suspend_after_steps': '[2]'}),
                         ['pretrain.py', 'suspend_after_steps=[2]'])


if __name__ == '__main__':
    unittest.main()
