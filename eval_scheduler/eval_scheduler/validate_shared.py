"""Opt-in real-model direct-endpoint repeatability; never logs to W&B.

This is not a benchmark-suite score comparison. The receipt records explicit
memory/concurrency overrides used to coexist with other work on the node.
"""
import asyncio
import json
from pathlib import Path
import time
import zipfile

import httpx
import typer

from .model import Action, read_plan
from .runtime import gpu_snapshot, vllm_server_extra_args, vllm_model_path
from .shared_pool import SharedServerPool
from .managed_backend import judge_reserve


PROMPTS = (
    'Answer with only the integer: what is 17 + 25?',
    'Svar kort paa dansk: Hvad er fotosyntese?',
    'Summarize in one sentence: Bees pollinate flowers. This helps plants produce seeds.',
    'Return only JSON with keys language and ready, set to English and true.',
    'Correct this sentence: She go to school every day.',
    'Translate into English: Det regner i dag.',
)


def canonical(response):
    return {'choices': [{key: value for key, value in choice.items()
                         if key in ('index', 'text', 'message', 'finish_reason', 'logprobs')}
                        for choice in response['choices']],
            'usage': {key: response.get('usage', {}).get(key)
                      for key in ('prompt_tokens', 'completion_tokens', 'total_tokens')}}


async def batch(url, model, requests, concurrency):
    limit = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(timeout=600, trust_env=False) as client:
        async def request(item):
            path, payload = item
            async with limit:
                result = await client.post(url+path, json={**payload, 'model': model})
                result.raise_for_status()
                return canonical(result.json())
        start = time.monotonic()
        values = await asyncio.gather(*(request(item) for item in requests))
        return values, time.monotonic()-start


def frozen_judge_requests(path, model):
    """Replay actual scorer requests, resolving Inspect's per-sample attachments."""
    requests = []
    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if not name.startswith('samples/') or not name.endswith('.json'):
                continue
            sample = json.loads(archive.read(name))
            attachments = sample.get('attachments', {})
            def resolve(value):
                if isinstance(value, str) and value.startswith('attachment://'):
                    return attachments[value.removeprefix('attachment://')]
                if isinstance(value, list):
                    return [resolve(v) for v in value]
                if isinstance(value, dict):
                    return {k: resolve(v) for k, v in value.items()}
                return value
            for event in sample.get('events', []):
                if event.get('event') == 'model' and event.get('model') == model:
                    payload = resolve(event['call']['request'])
                    payload.pop('extra_headers', None)
                    requests.append(('/chat/completions', payload))
    if not requests:
        raise ValueError('No matching judge requests in archive')
    return requests


def main(plan: Path, job_id: str, output: Path, gpu: int = 7,
         utilization: float = .05, concurrency: int = 4, reserve_mib: int = 4096,
         comparison_concurrency: int = 1, allow_managed_judge: bool = False,
         production_settings: bool = False, judge_archive: Path | None = None):
    if output.exists():
        raise ValueError('Use a new output directory; never overwrite an evaluation')
    if not 0 < utilization < 1 or concurrency < 1 or reserve_mib < 0 or comparison_concurrency < 1:
        raise ValueError('Invalid validation resource budget')
    source = next(j for j in read_plan(plan) if j.job_id == job_id)
    if source.action not in (Action.EVAL_STANDARD, Action.EVAL_DFM, Action.EVAL_EUROEVAL):
        raise ValueError('Choose a standard, DFM, or EuroEval inference job')
    if source.metadata.get('judge_server_model') and not allow_managed_judge:
        raise ValueError('Paired judge requires --allow-managed-judge and full headroom')
    frozen = frozen_judge_requests(judge_archive, source.metadata.get('judge_model')) if judge_archive else []
    if frozen and not allow_managed_judge:
        raise ValueError('Frozen judge replay requires managed judge')
    model_path = Path(vllm_model_path(source))
    if model_path.is_absolute() and not (model_path/'config.json').is_file():
        raise ValueError('Local export is missing; no process started')
    free, _, total = gpu_snapshot(gpu)
    if float(free) < float(total)*utilization + reserve_mib + judge_reserve(source):
        raise RuntimeError('Insufficient headroom; no process started')
    extra = vllm_server_extra_args(source)
    import shlex
    args = shlex.split(extra)
    overrides = {'--max-num-seqs': str(concurrency), '--max-num-batched-tokens': '512',
                 '--max-cudagraph-capture-size': str(concurrency)}
    filtered = []
    skip = False
    for arg in args:
        if skip:
            skip = False
            continue
        name = arg.split('=', 1)[0]
        if name in overrides:
            skip = '=' not in arg
        else:
            filtered.append(arg)
    for key, value in overrides.items():
        filtered.extend((key, value))
    if production_settings:
        filtered = shlex.split(extra)
    output.mkdir(parents=True)
    job = source.with_updates(job_id='shared-transport-validation', log_dir=str(output), metadata={
        **source.metadata, 'log_wandb': False, 'min_gpu_free_mib': 0,
        'vllm_gpu_memory_utilization': utilization, 'vllm_extra_args': shlex.join(filtered)})
    requests = [('/chat/completions', {'messages': [{'role': 'user', 'content': prompt}],
                 'temperature': 0, 'seed': 123, 'max_tokens': 32}) for prompt in PROMPTS]
    requests += [('/completions', {'prompt': prompt, 'temperature': 0, 'seed': 123,
                  'max_tokens': 16, 'logprobs': 1}) for prompt in PROMPTS[:2]]
    receipt = {'source_job': source.to_row(), 'validation_job': job.to_row(),
               'gpu': gpu, 'free_mib_before': free, 'requests': requests, 'passed': False,
               'comparison_concurrency': comparison_concurrency,
               'production_settings': production_settings,
               'judge_archive': str(judge_archive) if judge_archive else None,
               'transport': 'direct', 'scope': 'direct-endpoint repeatability, not broker parity'}
    pool = SharedServerPool(output, [gpu], max_requests_per_gpu=concurrency)
    try:
        def compare(url, log, monitor, alias):
            asyncio.run(batch(url, alias, requests, comparison_concurrency))
            lease = pool._slots[gpu].lease
            # Both modes use the identical resident model and equal concurrency.
            control, _ = asyncio.run(batch(lease.base_url, lease.model_name, requests, comparison_concurrency))
            direct, direct_time = asyncio.run(batch(lease.base_url, lease.model_name, requests, comparison_concurrency))
            shared, shared_time = asyncio.run(batch(url, alias, requests, comparison_concurrency))
            mismatches = [i for i, (a,b) in enumerate(zip(direct, shared)) if a != b]
            control_mismatches = [i for i, (a,b) in enumerate(zip(control, direct)) if a != b]
            passed = not mismatches and not control_mismatches
            receipt.update(control=control, direct=direct, shared=shared, mismatches=mismatches,
                           direct_control_mismatches=control_mismatches,
                           direct_seconds=direct_time, shared_seconds=shared_time, passed=passed)
            if monitor.judge_base_url:
                judge_requests = [('/chat/completions', {'messages': [{'role': 'user', 'content': text}],
                                  'temperature': 0, 'max_tokens': 64}) for text in (
                    'Judge whether the answer is correct. Reply YES or NO. Question: 2+2? Answer: 4.',
                    'Judge whether the answer is correct. Reply YES or NO. Question: 2+2? Answer: 5.')]
                judge_direct, _ = asyncio.run(batch(lease.judge_base_url, lease.judge_model_name, judge_requests, 1))
                judge_shared, _ = asyncio.run(batch(monitor.judge_base_url, lease.judge_model_name, judge_requests, 1))
                receipt['judge'] = {'direct': judge_direct, 'shared': judge_shared,
                                    'passed': judge_direct == judge_shared,
                                    'expected_verdicts': ['YES', 'NO']}
                verdicts = [value['choices'][0]['message']['content'].strip().upper()
                            for value in judge_shared]
                receipt['judge']['passed'] &= verdicts == ['YES', 'NO']
                passed = passed and receipt['judge']['passed']
                receipt['passed'] = passed
                if frozen:
                    frozen_direct, dt = asyncio.run(batch(lease.judge_base_url, lease.judge_model_name, frozen, 32))
                    frozen_shared, st = asyncio.run(batch(monitor.judge_base_url, lease.judge_model_name, frozen, 32))
                    receipt['frozen_judge'] = {'count': len(frozen), 'passed': frozen_direct == frozen_shared,
                        'direct': frozen_direct, 'shared': frozen_shared, 'direct_seconds': dt, 'shared_seconds': st}
                    passed &= receipt['frozen_judge']['passed']
                    receipt['passed'] = passed
            return 0 if passed else 1
        status = pool.run_client(job, compare)
        if status:
            raise RuntimeError(f'Transport validation failed: status {status}')
    except BaseException as exc:
        receipt['error'] = repr(exc)
        raise
    finally:
        try:
            pool.shutdown()
        finally:
            (output/'result.json').write_text(json.dumps(receipt, indent=2)+'\n')
    typer.echo(str(output/'result.json'))


if __name__ == '__main__':
    typer.run(main)
