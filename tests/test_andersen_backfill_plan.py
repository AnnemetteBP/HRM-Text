from eval_scheduler.model import Action, Job, JobStatus
from scripts.schedule_andersen_xl_backfill import prepare


def test_backfill_gating_and_idempotence(tmp_path):
    gate = Job(job_id='current-train', action=Action.TRAIN_UNTIL_STEP, family='training', name='current',
               metadata={'eval_step': 3450000, 'stop_after_step': 3450000})
    following = Job(job_id='next-train', action=Action.TRAIN_UNTIL_STEP, family='training', name='next',
                    deps=(gate.job_id, 'next-train-evals-terminal'))
    barrier = Job(job_id='next-train-evals-terminal', action=Action.TERMINAL_BARRIER, family='control', name='barrier',
                  deps_mode='terminal')
    template = Job(job_id='old-eval', action=Action.EVAL_DFM,
                   name='andersen_modernization', family='dfm', status=JobStatus.SKIPPED,
                   metadata={'skip_reason': 'missing validation', 'python_bin': '/env/bin/python'})
    merge = Job(job_id='old-merge', action=Action.MERGE_DFM, name=template.name, family='dfm')
    rows = [dict(step=2500000, export='export', export_exists=True, epoch=9.04),
            dict(step=2150000, existing_result='old-result')]
    jobs, added = prepare([gate, following, barrier, template, merge], rows,
                          tmp_path, tmp_path, gate.job_id)
    assert len(added) == 2
    evaluation, merged = added
    assert evaluation.deps == (gate.job_id,)
    assert 'skip_reason' not in evaluation.metadata
    assert evaluation.metadata['eval_epoch'] == 9.04
    assert evaluation.metadata['no_ema'] is False
    assert merged.metadata['python_bin'] == '/env/bin/python'
    assert merged.deps == (evaluation.job_id,)
    updated_barrier = next(j for j in jobs if j.job_id == barrier.job_id)
    assert merged.job_id in updated_barrier.deps
    assert updated_barrier.deps_mode == 'terminal'
    assert not prepare(jobs, rows, tmp_path, tmp_path, gate.job_id)[1]
