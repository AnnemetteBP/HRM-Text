import pytest

from eval_scheduler.model import Action, Job, JobStatus
from eval_scheduler.validate_suites import clone_job, compare


def test_clone_preserves_inference_but_never_syncs(tmp_path):
    source = Job('production', Action.EVAL_DFM, 'dfm', 'generative_talemaader',
                 deps=('export',), status=JobStatus.DONE, shard=2, shards=8,
                 initial_batch=32, metadata={'log_wandb': True, 'wandb_run_id': 'live',
                    'vllm_gpu_memory_utilization': .85, 'judge_server_model': 'judge',
                    'fix_mistral_regex': False, 'hrm_vllm_native_proxy': True})
    job = clone_job(source, tmp_path, 0)
    assert job.metadata['log_wandb'] is False
    assert 'wandb_run_id' not in job.metadata
    assert job.metadata['judge_server_model'] == 'judge'
    assert job.metadata['vllm_gpu_memory_utilization'] == .85
    assert job.metadata['fix_mistral_regex'] is False
    assert job.metadata['hrm_vllm_native_proxy'] is True
    assert (job.shard, job.shards, job.initial_batch) == (2, 8, 32)
    assert not job.deps and job.max_retries == 0
    assert source.metadata['log_wandb'] is True


def test_sync_and_training_not_allowed(tmp_path):
    for action in (Action.AVERAGE, Action.TRAIN_UNTIL_STEP):
        with pytest.raises(ValueError):
            clone_job(Job('unsafe', action, '', ''), tmp_path, 0)


def test_score_gate_requires_nonempty_and_exact():
    with pytest.raises(ValueError):
        compare({}, {})
    assert compare({'accuracy': .5, 'n': 10}, {'accuracy': .5, 'n': 10}) == {}
    assert 'n' in compare({'accuracy': .5, 'n': 10}, {'accuracy': .5, 'n': 9})
