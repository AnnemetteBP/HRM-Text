from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from eval_scheduler import runtime
from eval_scheduler.managed_backend import ManagedBackend
from eval_scheduler.model import Action, Job


def managed_job(tmp_path):
    return Job('judge-test', Action.EVAL_DFM, 'dfm', 'generative_talemaader',
               log_dir=str(tmp_path), metadata={'judge_server_model': 'original-judge',
                'judge_model': 'openai/original-judge', 'host': '127.0.0.1',
                'port_base': 20000})


def test_same_judge_launcher_and_owned_pair_cleanup(tmp_path, monkeypatch):
    target = Mock()
    target.acquire.return_value = SimpleNamespace(log_path=tmp_path/'target.log',
        process=Mock(poll=Mock(return_value=None)), base_url='http://target/v1', model_name='target')
    target.release_gpu.side_effect = lambda *a: setattr(target.acquire.return_value.process.poll, 'return_value', 0)
    judge = Mock(poll=Mock(return_value=None))
    start = Mock(return_value=(judge, 'http://judge/v1', tmp_path/'judge.log'))
    monkeypatch.setattr(runtime, 'start_managed_judge', start)
    monkeypatch.setattr(runtime, 'gpu_snapshot', lambda gpu: (20000, 0, 180000))
    stop = Mock(side_effect=lambda proc: setattr(proc.poll, 'return_value', 0))
    monkeypatch.setattr(runtime, 'terminate', stop)
    backend = ManagedBackend(tmp_path, Mock(), target=target)
    job = managed_job(tmp_path)
    pair = backend.acquire(job, 3)
    assert start.call_args.args[:2] == (job, 3)
    assert pair.judge_model_name == 'original-judge'
    assert pair.poll() is None
    judge.poll.return_value = 1
    assert pair.poll() == 1
    backend.release_gpu(3, 'test')
    stop.assert_called_once_with(judge)
    target.release_gpu.assert_called_once_with(3, 'test')


def test_judge_start_failure_releases_target(tmp_path, monkeypatch):
    target = Mock()
    target.acquire.return_value.log_path = tmp_path/'target.log'
    target.acquire.return_value.process.poll.return_value = 0
    monkeypatch.setattr(runtime, 'gpu_snapshot', lambda gpu: (20000, 0, 180000))
    monkeypatch.setattr(runtime, 'start_managed_judge', Mock(side_effect=RuntimeError('failed')))
    backend = ManagedBackend(tmp_path, Mock(), target=target)
    with pytest.raises(RuntimeError, match='failed'):
        backend.acquire(managed_job(tmp_path), 0)
    target.release_gpu.assert_called_once_with(0, 'judge_start_failed')
    assert not backend.pairs


def test_shared_dfm_callback_does_not_start_local_judge(tmp_path, monkeypatch):
    job = managed_job(tmp_path).with_updates(metadata={**managed_job(tmp_path).metadata,
        'ckpt_tag': 'step_1', 'model_prefix': 'test', 'dfm_evals_dir': 'dfm-evals',
        'dfm_single_tasks_config': 'unused', 'defer_dfm_export': True})
    launch = Mock(side_effect=AssertionError('must not start a per-client GPU judge'))
    monkeypatch.setattr(runtime, 'start_managed_judge', launch)
    client = Mock(return_value=0)
    monkeypatch.setattr(runtime, 'run_client_with_server_monitor', client)
    monitor = SimpleNamespace(shared_client=True, judge_base_url='http://shared/judge/v1')
    monkeypatch.setattr(runtime, 'run_with_vllm_server',
        lambda *a, **kw: kw['callback']('http://shared/target/v1', tmp_path/'server.log', monitor, 'target'))
    assert runtime.run_dfm_external(job, 0, 32, None) == 0
    argv = client.call_args.args[0]
    assert argv[argv.index('--judge-base-url')+1] == monitor.judge_base_url
    assert argv[argv.index('--judge-model')+1] == 'openai/original-judge'
    launch.assert_not_called()


@pytest.mark.parametrize('fail', [False, True])
def test_parallel_cleanup_attempts_every_owned_gpu(tmp_path, fail):
    from threading import Barrier, Lock
    backend = ManagedBackend(tmp_path, Mock(), target=Mock())
    backend.targets = {g: object() for g in range(8)}
    barrier, lock, seen = Barrier(8), Lock(), []
    def release(gpu, reason):
        assert reason == 'shared_shutdown'
        barrier.wait(3)  # Serial shutdown would fail this barrier.
        with lock:
            seen.append(gpu)
        if fail and gpu == 0:
            raise RuntimeError('exit unconfirmed')
    backend.release_gpu = release
    if fail:
        with pytest.raises(RuntimeError, match='exit unconfirmed'):
            backend.close_all()
        backend.target.close_all.assert_not_called()
    else:
        backend.close_all()
        backend.target.close_all.assert_called_once()
    assert sorted(seen) == list(range(8))
