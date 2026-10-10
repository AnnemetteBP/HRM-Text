from pathlib import Path
from unittest.mock import MagicMock

import pytest

from eval_scheduler import runtime
from eval_scheduler.model import Action, Job, JobStatus
from eval_scheduler.plan import split_euroeval_postprocessing


def evaluation(tmp_path, action=Action.EVAL_EUROEVAL):
    return Job(job_id="eval", action=action, family="euroeval", name="scala-de",
               deps=("export",), log_dir=str(tmp_path), initial_batch=64,
               metadata={"hrm_server_backend": "vllm", "eval_epoch": 11.0,
                         "eval_step": 3350000, "ckpt_tag": "step_3350000",
                         "euroeval_languages": ["de"], "log_wandb": False,
                         "model_prefix": "test", "euroeval_bin": "python guard.py"})


def test_split_preserves_publication_dependencies_and_is_idempotent(tmp_path):
    original = evaluation(tmp_path)
    average = Job(job_id="average", action=Action.AVERAGE, family="average", name="all", deps=("eval",))
    rows = split_euroeval_postprocessing([original, average])
    inference, merge, average = rows
    assert inference.requires_gpu and inference.deps == ("export",)
    assert merge.action == Action.MERGE_EUROEVAL and not merge.requires_gpu
    assert merge.deps == (inference.job_id,) and average.deps == (merge.job_id,)
    assert split_euroeval_postprocessing(rows) == rows
    rows[0] = inference.with_updates(status=JobStatus.DONE)
    assert runtime.dependencies_satisfied(merge, rows)
    assert not runtime.dependencies_satisfied(average, rows)
    rows[1] = merge.with_updates(status=JobStatus.FAILED)
    assert not runtime.dependencies_satisfied(average, rows)
    rows[1] = merge.with_updates(status=JobStatus.DONE)
    assert runtime.dependencies_satisfied(average, rows)


@pytest.mark.parametrize("status", [JobStatus.DONE, JobStatus.RUNNING, JobStatus.FAILED, JobStatus.SKIPPED])
def test_no_rewriting_existing_work(tmp_path, status):
    original = evaluation(tmp_path).with_updates(status=status)
    assert split_euroeval_postprocessing([original]) == [original]


def test_optional_valeu_does_not_become_mandatory_publication(tmp_path):
    original = evaluation(tmp_path).with_updates(name="valeu-da")
    average = Job("average", Action.AVERAGE, "average", "all", deps=(original.job_id,))
    rows = split_euroeval_postprocessing([original, average])
    assert rows == [original, average]
    for state in JobStatus:
        rows[0] = original.with_updates(status=state)
        assert runtime.dependencies_satisfied(average, rows)


@pytest.mark.parametrize("action,filename", [(Action.EVAL_EUROEVAL, "merged_metrics.json"),
    (Action.EVAL_EUROEVAL_BATCHED_IFEVAL, "wandb_metrics.json")])
def test_cpu_merge_preserves_output_and_language_arguments(tmp_path, monkeypatch, action, filename):
    (tmp_path / "euroeval_benchmark_results.jsonl").write_text('{}\n')
    merge = split_euroeval_postprocessing([evaluation(tmp_path, action)])[1]
    captured = MagicMock(return_value=0)
    monkeypatch.setattr(runtime, "run_command", captured)
    assert runtime.run_job(merge, None) == 0
    argv = captured.call_args.args[0]
    assert argv[argv.index("--output") + 1] == str(tmp_path / filename)
    assert ("--language" in argv) == (action == Action.EVAL_EUROEVAL)
    assert captured.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'] == ''


def test_inference_defers_sync_but_checks_artifact(tmp_path, monkeypatch):
    inference = split_euroeval_postprocessing([evaluation(tmp_path)])[0]
    def invoke(*args, **kwargs):
        return kwargs['callback']('http://localhost/v1', tmp_path / 'server.log', MagicMock(), 'model')
    def client(*args, **kwargs):
        (tmp_path / 'euroeval_benchmark_results.jsonl').write_text('{}\n')
        return 0
    monkeypatch.setattr(runtime, 'run_with_vllm_server', invoke)
    monkeypatch.setattr(runtime, 'run_client_with_server_monitor', client)
    sync = MagicMock(side_effect=AssertionError('must not sync on GPU'))
    monkeypatch.setattr(runtime, 'run_merge_euroeval', sync)
    assert runtime.run_euroeval_openai(inference, 0, 64, None) == 0
    sync.assert_not_called()


@pytest.mark.parametrize("action,handler", [
    (Action.EVAL_EUROEVAL, 'run_euroeval_openai'),
    (Action.EVAL_EUROEVAL_BATCHED_IFEVAL, 'run_euroeval_batched_ifeval_openai')])
def test_split_plan_remains_valid_without_persistent_pool(tmp_path, monkeypatch, action, handler):
    inference = split_euroeval_postprocessing([evaluation(tmp_path, action)])[0]
    callback = MagicMock(return_value=0)
    monkeypatch.setattr(runtime, handler, callback)
    assert runtime.run_job(inference, 0) == 0
    callback.assert_called_once()


@pytest.mark.parametrize('action', [Action.EVAL_DFM, Action.EVAL_DFM_IFEVAL])
def test_dfm_export_is_cpu_only_and_preserves_provenance(tmp_path, monkeypatch, action):
    source = evaluation(tmp_path, action).with_updates(
        metadata={**evaluation(tmp_path).metadata, 'dfm_evals_dir': 'dfm-evals'})
    inference, export = split_euroeval_postprocessing([source])
    assert inference.requires_gpu and inference.metadata['defer_dfm_export']
    assert export.action == Action.EXPORT_DFM_RESULTS and not export.requires_gpu
    assert export.job_id == source.job_id and export.deps == (inference.job_id,)
    (tmp_path / 'dfm-export-context.json').write_text('{"base_url":"http://localhost:1234/v1"}')
    run = MagicMock(return_value=0)
    monkeypatch.setattr(runtime, 'run_command', run)
    assert runtime.run_job(export, None) == 0
    argv = run.call_args.args[0]
    assert argv[argv.index('--inference-base-url') + 1] == 'http://localhost:1234/v1'
    assert run.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'] == ''
    assert split_euroeval_postprocessing([inference, export]) == [inference, export]


def test_ifeval_external_defers_export(tmp_path, monkeypatch):
    source = evaluation(tmp_path, Action.EVAL_DFM_IFEVAL).with_updates(shard=0, shards=4)
    source = source.with_updates(metadata={**source.metadata, 'dfm_ifeval_config': 'unused',
                                           'dfm_evals_dir': 'dfm-evals'})
    inference = split_euroeval_postprocessing([source])[0]
    monkeypatch.setattr(runtime, 'run_with_vllm_server', lambda *a, **kw:
        kw['callback']('http://direct/v1', tmp_path/'server.log', MagicMock(), 'actual'))
    monkeypatch.setattr(runtime, 'run_client_with_server_monitor', MagicMock(return_value=0))
    export = MagicMock(side_effect=AssertionError('export must not hold server residency'))
    monkeypatch.setattr(runtime, 'run_export_dfm_results', export)
    assert runtime.run_dfm_ifeval_external(inference, 0, 64, None) == 0
    assert (tmp_path/'dfm-export-context.json').exists()
    export.assert_not_called()


def test_sqlite_split_preserves_retry_budget_and_is_atomic(tmp_path):
    from eval_scheduler.store import SQLiteJobStore
    store = SQLiteJobStore(tmp_path/'jobs.sqlite')
    source = evaluation(tmp_path, Action.EVAL_DFM).with_updates(deps=(), attempt=2)
    store.import_jobs([source])
    assert store.split_postprocessing() == 1
    inference, export = store.load_jobs()
    assert inference.attempt == 2 and export.attempt == 0
    assert export.job_id == source.job_id and export.deps == (inference.job_id,)
    assert store.split_postprocessing() == 0
    store.import_jobs([source, source.with_updates(job_id='eval-inference')], preserve_runtime=False)
    before = store.load_jobs()
    with pytest.raises(ValueError, match='already exists'):
        store.split_postprocessing()
    assert store.load_jobs() == before


def test_sqlite_split_refuses_running_and_respects_admin_lock(tmp_path):
    from eval_scheduler.store import SQLiteJobStore
    store = SQLiteJobStore(tmp_path/'jobs.sqlite')
    source = evaluation(tmp_path, Action.EVAL_DFM).with_updates(deps=())
    store.import_jobs([source])
    store.set_admin_lock(True)
    assert store.split_postprocessing() == 0
    store.set_admin_lock(False)
    claim = store.claim_jobs(['eval'])['eval']
    with pytest.raises(ValueError, match='running claims'):
        store.split_postprocessing()
    assert store.load_jobs()[0].status == JobStatus.RUNNING


def test_claim_batch_revalidates_once_and_leaves_blocked_jobs_pending(tmp_path, monkeypatch):
    from eval_scheduler.model import write_plan, read_plan
    first = evaluation(tmp_path).with_updates(job_id='first', deps=())
    second = first.with_updates(job_id='second')
    blocked = first.with_updates(job_id='blocked', deps=('first',))
    write_plan(tmp_path / 'plan.tsv', [first, second, blocked])
    original_write = runtime.write_plan
    write = MagicMock(side_effect=original_write)
    monkeypatch.setattr(runtime, 'write_plan', write)
    result = runtime.Runner(tmp_path, []).claim_jobs(['first', 'second', 'blocked'])
    assert set(result) == {'first', 'second'}
    write.assert_called_once()
    assert read_plan(tmp_path / 'plan.tsv')[-1].status == JobStatus.PENDING


def test_runner_publishes_batched_completions_before_dependants(tmp_path, monkeypatch):
    from eval_scheduler.model import read_plan, write_plan
    first = evaluation(tmp_path).with_updates(job_id='first', deps=(), action=Action.EVAL_STANDARD)
    second = first.with_updates(job_id='second')
    final = first.with_updates(job_id='final', action=Action.AVERAGE, deps=('first', 'second'))
    write_plan(tmp_path / 'plan.tsv', [first, second, final])
    seen = []
    def execute(job, *args):
        if job.job_id == 'final':
            assert all(j.status == JobStatus.DONE for j in read_plan(tmp_path / 'plan.tsv')[:2])
        seen.append(job.job_id)
        return 0
    monkeypatch.setattr(runtime, 'run_job', execute)
    monkeypatch.setattr(runtime, 'gpu_snapshot', lambda gpu: ('100', '0', '100'))
    runtime.Runner(tmp_path, [0, 1]).run()
    assert seen[-1] == 'final'
    assert all(j.status == JobStatus.DONE for j in read_plan(tmp_path / 'plan.tsv'))
