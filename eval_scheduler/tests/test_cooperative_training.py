import threading

from eval_scheduler.model import Action, JobStatus
from test_database_runner import setup, job


def test_training_not_blocked_by_running_publication(tmp_path):
    publishing = threading.Event()
    trained = threading.Event()

    def execute(current, *args):
        if current.job_id == 'publish':
            publishing.set()
            assert trained.wait(3), 'CPU publication blocked training'
        elif current.job_id == 'eval':
            assert publishing.wait(3)
        elif current.job_id == 'train':
            trained.set()
        return 0

    jobs = [job('publish'), job('eval', Action.EVAL_DFM),
            job('train', Action.TRAIN_UNTIL_STEP, deps=('eval',))]
    runner, store, _ = setup(tmp_path, jobs, execute)
    assert runner.run() == 'done'
    assert all(j.status == JobStatus.DONE for j in store.load_jobs())
