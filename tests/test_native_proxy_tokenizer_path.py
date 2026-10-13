from pathlib import Path
import sys
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'eval_scheduler'))
from eval_scheduler import runtime
from eval_scheduler.model import Action, Job


@pytest.mark.parametrize('key', ['hf_export_dir', 'hrm_hf_export_dir', 'standard_hf_export_dir'])
def test_native_context_proxy_uses_local_tokenizer(tmp_path, monkeypatch, key):
    job = Job('proxy', Action.EVAL_EUROEVAL, 'euroeval', 'scala-en', metadata={
        'host': '127.0.0.1', 'python_bin': sys.executable,
        'euroeval_context_policy': 'native_head_tail_v1', key: '/local/export',
    })
    spawn = Mock(return_value=Mock())
    monkeypatch.setattr(runtime, 'spawn', spawn)
    monkeypatch.setattr(runtime, 'wait_for_server', Mock())
    monkeypatch.setattr(runtime, 'prepare_client_command', lambda argv, env: (argv, env))
    runtime.start_native_proxy(job, target_base_url='http://localhost:1234/v1',
                               model_name='local', run_dir=tmp_path, port_offset=0)
    argv = spawn.call_args.args[0]
    assert argv[argv.index('--prompt-tokenizer') + 1] == '/local/export'
    assert argv[argv.index('--max-context') + 1] == '4096'
