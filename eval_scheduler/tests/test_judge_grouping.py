from eval_scheduler.judge_grouping import group_judged_first
from eval_scheduler.model import Action, Job, JobStatus


def test_future_judges_first_without_suite_shutdown():
    meta = {'eval_step': 3450000}
    judge = Job('judge', Action.EVAL_DFM, 'dfm', 'generative_talemaader',
                metadata={**meta, 'judge_server_model': 'judge'})
    ordinary = Job('normal', Action.EVAL_DFM, 'dfm', 'other', metadata=meta)
    teardown = Job('teardown', Action.TEARDOWN_EVAL, 'control', 'stop',
                   deps=('judge', 'normal'), metadata=meta)
    later = Job('later', Action.EVAL_EUROEVAL, 'euroeval', 'task',
                deps=('teardown',), metadata=meta)
    current = ordinary.with_updates(job_id='current', metadata={'eval_step': 3400000},
                                    status=JobStatus.RUNNING)
    result = group_judged_first([judge, ordinary, teardown, later, current], 3450000)
    by_id = {j.job_id: j for j in result}
    gate = result[-1]
    assert gate.deps == ('judge',) and gate.deps_mode == 'terminal'
    assert gate.job_id in by_id['normal'].deps and gate.job_id in by_id['later'].deps
    assert by_id['teardown'].action == Action.TERMINAL_BARRIER
    assert by_id['current'] == current and by_id['judge'] == judge
    assert group_judged_first(result, 3450000) == result
