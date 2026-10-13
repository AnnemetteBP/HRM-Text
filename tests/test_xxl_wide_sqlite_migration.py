import pytest

from dfm14.continue_training import PREFIX, finalize_boundary
from eval_scheduler.database_cli import publish_database_marker
from eval_scheduler.model import Action, Job, JobStatus, read_plan, write_plan
from eval_scheduler.store import SQLiteJobStore
from scripts.migrate_xxl_wide_sqlite import policies


@pytest.mark.parametrize('sqlite', [False, True])
def test_boundary_coordinates_preserve_training_and_completed_rows(tmp_path, sqlite):
    meta = {'dfm14_boundary':1000000, 'eval_step':1000000, 'keep':'unchanged'}
    jobs = [Job(PREFIX+'train', Action.TRAIN_UNTIL_STEP, 'training', 'train',
                status=JobStatus.RUNNING, metadata=meta),
            Job(PREFIX+'wait', Action.WAIT_CHECKPOINT, 'control', 'wait', metadata=meta),
            Job(PREFIX+'eval', Action.EVAL_DFM, 'dfm', 'test', metadata=meta),
            Job(PREFIX+'done', Action.EVAL_DFM, 'dfm', 'old', status=JobStatus.DONE,
                metadata=meta)]
    token = None
    if sqlite:
        store = SQLiteJobStore(tmp_path/'jobs.sqlite')
        store.import_jobs(jobs)
        token = store.claim_jobs([PREFIX+'wait'])[PREFIX+'wait'].token
        publish_database_marker(tmp_path, store.path)
    else:
        write_plan(tmp_path/'plan.tsv', jobs)
    finalize_boundary(tmp_path, 1000000, 3.125, 999999)
    rows = read_plan(tmp_path/'plan.tsv')
    assert rows[0] == jobs[0]
    assert rows[3] == jobs[3]
    for row in rows[1:3]:
        assert row.metadata == {**meta, 'eval_epoch':3.125, 'eval_step':999999}
    if sqlite:
        assert store.attempt_token(PREFIX+'wait') == token


def test_policy_changes_leave_commands_and_completed_rows_unchanged():
    prior = Job(PREFIX+'train-950000', Action.TRAIN_UNTIL_STEP, 'training', 'train',
                status=JobStatus.DONE)
    barrier = Job(PREFIX+'gate', Action.TERMINAL_BARRIER, 'control', 'gate',
                  deps=(prior.job_id,))
    future = Job(PREFIX+'train-1000000', Action.TRAIN_UNTIL_STEP, 'training', 'train',
                 deps=(barrier.job_id,), metadata={'dfm14_boundary':1000000,
                                                  'command':'unchanged command'})
    jobs = policies([prior, barrier, future], 950000)
    assert jobs[0] == prior
    assert jobs[2].metadata['command'] == future.metadata['command']
    assert jobs[2].deps == (prior.job_id, future.job_id+'-evals-terminal')
    assert jobs[-1].deps_mode == 'terminal'
    assert policies(jobs, 950000) == jobs
