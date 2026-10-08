import pytest
from scripts import schedule_dfm14_average_correction as c
from eval_scheduler.model import Job


def fixture():
    def job(identifier, action, status=c.JobStatus.PENDING, **metadata):
        return Job(job_id=identifier, action=action, name=identifier, family='test',
                   status=status, metadata=metadata)
    return [job('dfm14-eval-3250000-average', c.Action.AVERAGE, c.JobStatus.DONE,
                eval_step=3250000, eval_epoch=10.6),
            job('export3250', c.Action.EXPORT_HF, c.JobStatus.DONE,
                eval_step=3250000, eval_epoch=10.812711203938841),
            job('dfm14-xl-step_3300000-train', c.Action.TRAIN_UNTIL_STEP, c.JobStatus.RUNNING),
            job('wait3300', c.Action.WAIT_CHECKPOINT, eval_step=3300000)]


def test_correction_uses_actual_epoch_and_serializes_writers():
    before = fixture()
    after = c.build(before)
    assert after[:3] == before[:3]
    assert after[-1].metadata['eval_epoch'] == before[1].metadata['eval_epoch']
    assert after[-1].deps == ('dfm14-xl-step_3300000-train',)
    assert c.ID in after[3].deps
    assert after[-1].metadata['population_require_complete']


def test_no_racing_evaluation_boundary():
    before = fixture()
    before[-1] = before[-1].with_updates(status=c.JobStatus.RUNNING)
    with pytest.raises(ValueError, match='unstarted'):
        c.build(before)
