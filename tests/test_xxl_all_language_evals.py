from eval_scheduler.model import Action, Job, JobStatus
from scripts.extend_xxl_all_language_evals import extend


def test_additive_coverage_preserves_running_and_completed_and_is_idempotent():
    prefix = 'xxlw-dfm14-950000-'
    metadata = dict(dfm14_boundary=950000, ckpt_tag='step_950000',
                    dfm_log_root='logs/test', hrm_server_backend='vllm')
    export = Job(prefix+'export', Action.EXPORT_HF, 'control', 'export',
                 status=JobStatus.DONE, metadata=metadata)
    jobs = [export]
    for name in ('dala_ga', 'gec_dala_ga'):
        jobs.append(Job(prefix+name+'-inference', Action.EVAL_DFM, 'dfm', name,
            shard=0, shards=4, deps=(export.job_id,), status=JobStatus.RUNNING,
            metadata={**metadata, 'language':'ga', 'defer_dfm_export':True}))
        jobs.append(Job(prefix+name+'-merge', Action.MERGE_DFM, 'dfm', name,
                        deps=(prefix+name+'-inference',), metadata=metadata))
    for i in range(47):
        jobs.append(Job(prefix+f'done-{i}', Action.EVAL_DFM, 'dfm', f'done-{i}',
                        status=JobStatus.DONE, metadata={**metadata, 'language':f'old{i}'}))
    average = Job(prefix+'average', Action.AVERAGE, 'post', 'average',
                  metadata={**metadata, 'multilingual_manifest':'test.json'})
    barrier = Job(prefix+'barrier', Action.TERMINAL_BARRIER, 'control', 'barrier',
                  deps=(export.job_id,), deps_mode='terminal', metadata=metadata)
    jobs.extend([average, barrier])
    tasks = [dict(name=family+'_'+lang, suite=family+'_'+lang, config='test.yaml',
                  language=lang, max_tokens=32 if family=='dala' else 512)
             for lang in ('new1', 'new2') for family in ('dala','gec_dala')]
    after = extend(jobs, tasks)
    assert len(after) == len(jobs)+36
    assert all(j in after for j in jobs if j.status in (JobStatus.RUNNING, JobStatus.DONE))
    assert len(next(j for j in after if j.job_id == average.job_id).deps) == 4
    gate = next(j for j in after if j.job_id == barrier.job_id)
    assert gate.deps_mode == 'terminal' and average.job_id in gate.deps
    assert extend(after, tasks) == after
