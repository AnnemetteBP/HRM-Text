from eval_scheduler.environments import sync_project_environments, without_project_sync
from eval_scheduler.model import Action, Job, JobStatus


def test_project_launch_bypasses_sync_only():
    command = ['uv', 'run', '--project', 'dfm-evals', 'evals', 'suite', 'test']
    result = without_project_sync(command)
    assert result == ['uv', 'run', '--no-sync', *command[2:]]
    assert without_project_sync(result) == result
    standalone = ['uv', 'run', '--no-project', '--with', 'euroeval', 'script.py']
    assert without_project_sync(standalone) == standalone


def test_sync_once_per_pending_project(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr('eval_scheduler.environments.subprocess.run',
                        lambda args, **kwargs: calls.append((args, kwargs)))
    job = Job(job_id='one', action=Action.EVAL_DFM, family='dfm', name='dala',
              metadata={'dfm_evals_dir': str(tmp_path / 'dfm-evals')})
    done = job.with_updates(job_id='done', status=JobStatus.DONE,
                            metadata={'dfm_evals_dir': str(tmp_path/'unused')})
    sync_project_environments([job, job.with_updates(job_id='two'), done], tmp_path)
    assert len(calls) == 1
    assert calls[0][0] == ['uv', 'sync', '--verbose', '--locked', '--inexact', '--project',
                            str(tmp_path/'dfm-evals')]
    assert calls[0][1]['check'] is True
