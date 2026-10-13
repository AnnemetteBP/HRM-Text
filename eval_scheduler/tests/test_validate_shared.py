from pathlib import Path

import pytest

from eval_scheduler import validate_shared
from eval_scheduler.model import Action, Job


def test_missing_export_refused_before_gpu_query(tmp_path, monkeypatch):
    job = Job('a', Action.EVAL_STANDARD, 'standard', 'test', metadata={
        'hrm_hf_export_dir': str(tmp_path/'missing')})
    monkeypatch.setattr(validate_shared, 'read_plan', lambda path: [job])
    monkeypatch.setattr(validate_shared, 'gpu_snapshot', lambda gpu: pytest.fail('must not query GPU'))
    with pytest.raises(ValueError, match='export is missing'):
        validate_shared.main(tmp_path/'plan.tsv', 'a', tmp_path/'result')
    assert not (tmp_path/'result').exists()


def test_managed_headroom_includes_judge_reserve(tmp_path, monkeypatch):
    model = tmp_path/'model'; model.mkdir(); (model/'config.json').write_text('{}')
    job = Job('a', Action.EVAL_DFM, 'dfm', 'generative_talemaader', metadata={
        'hrm_hf_export_dir': str(model), 'judge_server_model': 'judge'})
    monkeypatch.setattr(validate_shared, 'read_plan', lambda path: [job])
    monkeypatch.setattr(validate_shared, 'gpu_snapshot', lambda gpu: (20000, 0, 180000))
    with pytest.raises(RuntimeError, match='headroom'):
        validate_shared.main(tmp_path/'plan.tsv', 'a', tmp_path/'result', allow_managed_judge=True)
    assert not (tmp_path/'result').exists()


def test_parity_keeps_logprobs_and_token_counts():
    value = {'id': 'request-id', 'model': 'alias', 'choices': [
        {'index': 0, 'text': 'answer', 'finish_reason': 'stop', 'logprobs': {'token_logprobs': [-.1]}}],
        'usage': {'prompt_tokens': 5, 'completion_tokens': 1, 'total_tokens': 6}}
    canonical = validate_shared.canonical(value)
    assert canonical['choices'][0]['logprobs'] == {'token_logprobs': [-.1]}
    assert canonical['usage']['prompt_tokens'] == 5


def test_production_settings_preserve_server_arguments(tmp_path, monkeypatch):
    model = tmp_path/'model'; model.mkdir(); (model/'config.json').write_text('{}')
    extra = '--max-num-seqs 1024 --max-num-batched-tokens 16384 --max-cudagraph-capture-size 512'
    source = Job('a', Action.EVAL_STANDARD, 'standard', 'ARC', metadata={
        'hrm_hf_export_dir': str(model), 'vllm_extra_args': extra})
    captured = []
    class Pool:
        def __init__(self, *args, **kwargs):
            pass
        def run_client(self, job, callback):
            captured.append(job)
            return 0
        def shutdown(self):
            pass
    monkeypatch.setattr(validate_shared, 'read_plan', lambda path: [source])
    monkeypatch.setattr(validate_shared, 'gpu_snapshot', lambda gpu: (180000, 0, 180000))
    monkeypatch.setattr(validate_shared, 'vllm_server_extra_args', lambda job: extra)
    monkeypatch.setattr(validate_shared, 'SharedServerPool', Pool)
    validate_shared.main(tmp_path/'plan.tsv', 'a', tmp_path/'result', production_settings=True)
    assert captured[0].metadata['vllm_extra_args'] == extra


def test_frozen_judge_requests_resolve_attachments(tmp_path):
    import json
    import zipfile
    path = tmp_path/'test.eval'
    sample = {'attachments': {'text': 'Actual judge prompt'}, 'events': [
        {'event': 'model', 'model': 'target'},
        {'event': 'model', 'model': 'judge', 'call': {'request': {
            'messages': [{'role': 'user', 'content': 'attachment://text'}],
            'extra_headers': {'x-irid': 'old'}, 'temperature': 0, 'max_tokens': 64}}}]}
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('samples/a.json', json.dumps(sample))
    [(route, payload)] = validate_shared.frozen_judge_requests(path, 'judge')
    assert route == '/chat/completions'
    assert payload == {'messages': [{'role': 'user', 'content': 'Actual judge prompt'}],
                       'temperature': 0, 'max_tokens': 64}
    with pytest.raises(ValueError, match='No matching'):
        validate_shared.frozen_judge_requests(path, 'absent')
