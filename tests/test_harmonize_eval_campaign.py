from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'eval_scheduler'))
from eval_scheduler.model import Action, Job, JobStatus
from scripts.harmonize_xxl_eval_campaign import build, identity


def fixture():
    jobs = []
    for step in (1000000, 1050000):
        p = f'xxlw-dfm14-{step}-'
        m = dict(dfm14_boundary=step, eval_step=step, ckpt_tag=f'step_{step}',
                 log_root=f'/local/{step}/standard', dfm_log_root=f'/local/{step}/dfm',
                 euroeval_log_root=f'/local/{step}/euroeval', wandb_run_id='local-xxl',
                 vllm_gpu_memory_utilization=.9, python_bin='/local/python',
                 hrm_hf_export_dir=f'/local/{step}/hf',
                 average_prefix='headline_avg_v3')
        jobs.extend([
            Job(p+'export', Action.EXPORT_HF, 'export', 'export', metadata=m),
            Job(p+'euro', Action.EVAL_EUROEVAL, 'euroeval', 'scala-en',
                deps=(p+'export',), initial_batch=64, metadata={**m, 'defer_euroeval_merge': True}),
            Job(p+'merge', Action.MERGE_EUROEVAL, 'euroeval', 'scala-en',
                deps=(p+'euro',), metadata=m),
            Job(p+'average', Action.AVERAGE, 'post', 'average', deps=(p+'merge',), metadata=m),
            Job(p+'gate', Action.TERMINAL_BARRIER, 'control', 'gate',
                deps=(p+'euro',), deps_mode='terminal', metadata=m),
        ])
    jobs.append(Job('xxlw-dfm14-train-1050000', Action.TRAIN_UNTIL_STEP, 'train', 'training',
        deps=('xxlw-dfm14-1000000-gate',), metadata={'eval_step': 1050000, 'command': ['unchanged']}))
    remote = [
        Job('r-old', Action.MERGE_EUROEVAL, 'euroeval', 'scala-en'),
        Job('r-new', Action.EVAL_EUROEVAL, 'euroeval', 'allocine',
            metadata={'euroeval_languages': ['fr'], 'defer_euroeval_merge': True,
                      'wandb_run_id': 'wrong-xl', 'vllm_gpu_memory_utilization': .95}),
        Job('r-merge', Action.MERGE_EUROEVAL, 'euroeval', 'allocine', deps=('r-new',)),
        Job('r-average', Action.AVERAGE, 'post', 'average', deps=('r-old', 'r-merge'),
            metadata={'average_prefix': 'headline_avg_v3'}),
        Job('r-semantic', Action.AVERAGE, 'post', 'semantic', deps=('r-old', 'r-merge'),
            metadata={'average_prefix': 'headline_avg_semantic_v1',
                      'extra_average_prefixes': ['suite_avg_semantic_v1']}),
    ]
    return jobs, remote, {'mappings': {}, 'euroeval_bin': '/local/euro18'}


def test_added_protocol_keeps_local_model_and_capacity():
    jobs, reference, assets = fixture()
    result, _ = build(jobs, reference, assets, Path('/plan'))
    new = next(j for j in result if j.action == Action.EVAL_EUROEVAL and j.name == 'allocine')
    assert new.metadata['euroeval_languages'] == ['fr']
    assert new.metadata['wandb_run_id'] == 'local-xxl'
    assert new.metadata['vllm_gpu_memory_utilization'] == .9
    assert new.initial_batch == 64
    assert new.metadata['euroeval_bin'] == '/local/euro18'
    assert new.metadata['hf_export_dir'] == '/local/1000000/hf'
    assert next(j for j in result if j.action == Action.TRAIN_UNTIL_STEP) == jobs[-1]
    # Completed/running jobs and their runtime identities are never recreated.
    again, _ = build(result, reference, assets, Path('/plan'))
    assert result == again


def test_gates_ignore_failed_publication_but_wait_for_new_inference():
    jobs, reference, assets = fixture()
    result, _ = build(jobs, reference, assets, Path('/plan'))
    by_id = {j.job_id: j for j in result}
    gate = by_id['xxlw-dfm14-1000000-gate']
    assert gate.deps_mode == 'terminal'
    assert len(gate.deps) == 2
    assert all(by_id[d].action == Action.EVAL_EUROEVAL for d in gate.deps)
    avg = by_id['xxlw-dfm14-1000000-average']
    assert len(avg.deps) == 2
    assert all(by_id[d].action == Action.MERGE_EUROEVAL for d in avg.deps)


def test_defer_to_active_training_without_interrupting_it():
    jobs, reference, assets = fixture()
    jobs = [j.with_updates(status=JobStatus.DONE) if j.job_id == 'xxlw-dfm14-1000000-gate'
            else j.with_updates(status=JobStatus.RUNNING) if j.action == Action.TRAIN_UNTIL_STEP
            else j for j in jobs]
    result, _ = build(jobs, reference, assets, Path('/plan'), defer_first_to=jobs[-1].job_id)
    assert next(j for j in result if j.action == Action.TRAIN_UNTIL_STEP) == jobs[-1]
    new = next(j for j in result if j.action == Action.EVAL_EUROEVAL and j.name == 'allocine')
    assert jobs[-1].job_id in new.deps
    gate = next(j for j in result if j.job_id == 'xxlw-dfm14-1050000-gate')
    assert new.job_id in gate.deps
    assert next(j for j in result if j.job_id == jobs[4].job_id) == jobs[4]


def test_reject_unprepared_paths_and_released_boundary():
    jobs, reference, assets = fixture()
    reference[1] = reference[1].with_updates(metadata={'dfm_single_tasks_config': '/work/mimir/missing.yaml'})
    with pytest.raises(ValueError, match='Unprepared'):
        build(jobs, reference, assets, Path('/plan'))
    jobs, reference, assets = fixture()
    jobs[4] = jobs[4].with_updates(status=JobStatus.DONE)
    with pytest.raises(ValueError, match='already released'):
        build(jobs, reference, assets, Path('/plan'))


def test_expanded_average_dispatch_identity():
    j = Job('a', Action.AVERAGE, 'post', 'expanded', metadata={
        'average_prefix': 'headline_avg_dala_v2', 'multilingual_manifest': '/provenance.json'})
    assert identity(j) == ('average', 'headline_avg_dala_v2')
