import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from eval_scheduler.model import Action, Job, JobStatus, write_plan
from eval_scheduler.runtime import Runner, SchedulerError, start_native_proxy, wait_for_server


class ProxyStartupTest(unittest.TestCase):
    def test_dispatch_commits_completion_and_successor_once(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = Runner(Path(directory), [0])
            first = Job(job_id='first', action=Action.EVAL_STANDARD,
                        family='standard', name='first', status=JobStatus.RUNNING)
            second = Job(job_id='second', action=Action.EVAL_STANDARD,
                         family='standard', name='second', deps=('first',))
            write_plan(runner.plan_file, [first, second])
            with patch('eval_scheduler.runtime.write_plan', wraps=write_plan) as write:
                selected, _, _ = runner.dispatch({'first': {'status': JobStatus.DONE}}, [0], 4, 8)
            self.assertEqual(write.call_count, 1)
            self.assertEqual(selected[0][0].job_id, 'second')
            self.assertEqual([j.status for j in runner.load()], [JobStatus.DONE, JobStatus.RUNNING])

    def test_plan_snapshot_observes_external_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = Runner(Path(directory), [0])
            job = Job(job_id='test', action=Action.EVAL_STANDARD, family='standard', name='test')
            write_plan(runner.plan_file, [job])
            self.assertEqual(len(runner.ready_jobs()), 1)
            with patch('eval_scheduler.runtime.read_plan', side_effect=AssertionError('redundant parse')):
                self.assertEqual(len(runner.ready_jobs()), 1)
                runner.claim_jobs(['test'])
                self.assertEqual(runner.ready_jobs(), [])
            write_plan(runner.plan_file, [job.with_updates(status=JobStatus.PENDING, initial_batch=7)])
            self.assertEqual(runner.ready_jobs()[0].initial_batch, 7)

    def test_dead_child_fails_without_polling_http_or_sleeping(self):
        child = MagicMock(returncode=1)
        child.poll.return_value = 1
        with patch('eval_scheduler.runtime.urlopen') as request, patch('eval_scheduler.runtime.time.sleep') as sleep:
            with self.assertRaisesRegex(SchedulerError, 'exited with code 1'):
                wait_for_server('http://localhost/health', process=child)
            request.assert_not_called()
            sleep.assert_not_called()

    def test_proxy_inherits_reserved_socket(self):
        child = MagicMock()
        with tempfile.TemporaryDirectory() as directory:
            job = Job(job_id='proxy-test', action=Action.EVAL_EUROEVAL,
                      family='euroeval', name='test',
                      metadata={'host': '127.0.0.1', 'python_bin': 'python'})

            def launch(argv, **kwargs):
                fd = kwargs['pass_fds'][0]
                self.assertEqual(int(argv[argv.index('--fd') + 1]), fd)
                port = int(argv[argv.index('--port') + 1])
                with socket.socket() as contender:
                    with self.assertRaises(OSError):
                        contender.bind(('127.0.0.1', port))
                return child

            with patch('eval_scheduler.runtime.subprocess.Popen', side_effect=launch), patch('eval_scheduler.runtime.wait_for_server') as wait:
                result, _, _ = start_native_proxy(job, target_base_url='http://localhost:1234/v1',
                                                  model_name='test-model', run_dir=Path(directory), port_offset=0)
                self.assertIs(result, child)
                self.assertIs(wait.call_args.kwargs['process'], child)
                self.assertEqual(wait.call_args.kwargs['expected_model'], 'test-model')
