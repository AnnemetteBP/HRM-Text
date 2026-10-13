import pytest

from eval_scheduler.model import Action, Job, JobStatus
from eval_scheduler.store import SQLiteJobStore
from eval_scheduler.training_continuation import allow_failed_evals


@pytest.mark.parametrize('failed', ['eval', 'sync', 'export', 'train'])
def test_evaluation_failure_allows_resume_but_training_failure_does_not(tmp_path, failed):
    def status(name):
        return JobStatus.FAILED if name == failed else JobStatus.DONE
    jobs = [Job('train', Action.TRAIN_UNTIL_STEP, 'training', 'old', status=status('train')),
            Job('export', Action.EXPORT_HF, 'export', 'export', deps=('train',),
                status=JobStatus.PENDING if failed == 'train' else status('export')),
            Job('eval', Action.EVAL_DFM, 'dfm', 'eval', deps=('export',),
                status=status('eval') if failed not in ('train', 'export') else JobStatus.PENDING),
            Job('sync', Action.MERGE_DFM, 'dfm', 'sync', deps=('eval',),
                status=status('sync') if failed == 'sync' else JobStatus.PENDING),
            Job('next', Action.TRAIN_UNTIL_STEP, 'training', 'next', deps=('sync',),
                metadata={'eval_step': 3500000})]
    result = allow_failed_evals(jobs, 3500000)
    assert allow_failed_evals(result, 3500000) == result
    s = SQLiteJobStore(tmp_path/'jobs.sqlite');s.import_jobs(result)
    gate = 'next-evals-terminal'
    assert gate in [j.job_id for j in s.ready_jobs()]
    s.update_jobs({gate: {'status': JobStatus.DONE}})
    assert ('next' in [j.job_id for j in s.ready_jobs()]) == (failed != 'train')


def test_running_eval_is_not_bypassed(tmp_path):
    jobs = [Job('train', Action.TRAIN_UNTIL_STEP, 'training', 'old', status=JobStatus.DONE),
            Job('eval', Action.EVAL_DFM, 'dfm', 'eval', deps=('train',), status=JobStatus.RUNNING),
            Job('next', Action.TRAIN_UNTIL_STEP, 'training', 'next', deps=('eval',),
                metadata={'eval_step': 3500000})]
    s = SQLiteJobStore(tmp_path/'jobs.sqlite');s.import_jobs(allow_failed_evals(jobs,3500000))
    assert not s.ready_jobs()
