"""Isolated 100-row multilingual scheduler comparison; never publishes metrics."""
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile
import threading
import time
from urllib.request import urlopen

from prometheus_client.parser import text_string_to_metric_families
import typer

from .database_cli import publish_database_marker
from .database_runner import DatabaseRunner
from .model import Action, JobStatus, read_plan, write_plan
from .runtime import Runner, gpu_snapshot, vllm_model_path
from .shared_pool import SharedServerPool
from .store import SQLiteJobStore
from .validate_suites import clone_job, compare, scores


def select_jobs(jobs):
    selected = {}
    for job in jobs:
        if (job.action != Action.EVAL_DFM or job.status != JobStatus.DONE
                or str(job.metadata.get('eval_step')) != '3350000'
                or (job.shard or 0) != 0):
            continue
        language = job.metadata.get('language')
        if not language:
            continue
        family = 'correction' if job.name.startswith('gec_dala_') else 'acceptability'
        if not job.name.startswith(('dala_', 'gec_dala_')):
            continue
        if 'dfm14_XL_step_3350000_ema_hf' not in vllm_model_path(job):
            continue
        key = (language, family)
        # Prefer the newer held-out v2 tasks where available.
        if key not in selected or '_v2_' in job.name:
            selected[key] = job
    languages = sorted({key[0] for key in selected})
    if len(languages) != 50 or len(selected) != 100:
        raise ValueError(f'Expected 50 complete language pairs, got {len(languages)}/{len(selected)}')
    return [selected[(language, family)] for language in languages
            for family in ('acceptability', 'correction')]


def scrape(lease):
    try:
        url = lease.base_url.removesuffix('/v1') + '/metrics'
        with urlopen(url, timeout=.8) as response:
            body = response.read().decode()
        values = defaultdict(float)
        for family in text_string_to_metric_families(body):
            for sample in family.samples:
                if sample.name in {
                    'vllm:kv_cache_usage_perc', 'vllm:gpu_cache_usage_perc',
                    'vllm:num_requests_running', 'vllm:num_requests_waiting',
                    'vllm:request_success_total', 'vllm:prompt_tokens_total',
                    'vllm:generation_tokens_total', 'vllm:num_preemptions_total',
                }:
                    values[sample.name] += sample.value
        return {'pid': lease.process.pid, 'values': dict(values)}
    except Exception as exc:
        return {'pid': lease.process.pid, 'error': str(exc)}


class Measurements:
    def __init__(self, path, target_pool):
        self.path, self.pool = path, target_pool
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        with self.path.open('w') as handle, ThreadPoolExecutor(max_workers=8) as workers:
            while not self.stop.is_set():
                start = time.monotonic()
                record = {'time': time.time()}
                try:
                    output = subprocess.check_output([
                        'nvidia-smi', '--query-gpu=index,memory.used,utilization.gpu',
                        '--format=csv,noheader,nounits'], text=True, timeout=3)
                    record['gpus'] = {parts[0].strip(): {
                        'memory_mib': float(parts[1]), 'utilization': float(parts[2])}
                        for parts in (line.split(',') for line in output.splitlines())}
                    with self.pool._registry_lock:
                        leases = list(self.pool._leases.items())
                    results = list(workers.map(scrape, [lease for _, lease in leases]))
                    record['servers'] = {str(gpu): result for (gpu, _), result in zip(leases, results)}
                    snapshot = self.path.parent / 'runtime.json'
                    if snapshot.exists():
                        shared = json.loads(snapshot.read_text()).get('shared', {})
                        record['broker'] = {key: {field: state.get(field) for field in
                            ('active', 'queued', 'failures', 'last_error', 'completed')}
                            for key, state in shared.get('gateway_metrics', {}).get('backends', {}).items()}
                except Exception as exc:
                    record['error'] = repr(exc)
                handle.write(json.dumps(record) + '\n')
                handle.flush()
                self.stop.wait(max(0, 1 - (time.monotonic() - start)))

    def finish(self):
        self.stop.set()
        self.thread.join()


def summarize(path, wall_seconds):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    active = [row for row in rows if any(
        server.get('values', {}).get('vllm:num_requests_running', 0) > 0
        for server in row.get('servers', {}).values())]
    counters = defaultdict(list)
    for row in rows:
        for server in row.get('servers', {}).values():
            for key, value in server.get('values', {}).items():
                if key.endswith('_total'):
                    counters[(server['pid'], key)].append(value)
    totals = defaultdict(float)
    for (_, key), values in counters.items():
        # Each PID is a fresh owned server; counters start at zero.
        totals[key] += max(values)
    windows = {}
    for name, window in [('whole_campaign', rows), ('inference_active', active)]:
        gpu_util = {str(g): [r['gpus'][str(g)]['utilization'] for r in window
                            if str(g) in r.get('gpus', {})] for g in range(8)}
        kv, running, waiting = [], [], []
        for row in window:
            for server in row.get('servers', {}).values():
                values = server.get('values', {})
                cache = values.get('vllm:kv_cache_usage_perc', values.get('vllm:gpu_cache_usage_perc'))
                if cache is not None:
                    kv.append(cache * 100)
                if values:
                    running.append(values.get('vllm:num_requests_running', 0))
                    waiting.append(values.get('vllm:num_requests_waiting', 0))
        windows[name] = {
            'samples': len(window),
            'gpu_peak_memory_mib': {str(g): max((r['gpus'][str(g)]['memory_mib']
                for r in window if 'memory_mib' in r.get('gpus', {}).get(str(g), {})), default=None) for g in range(8)},
            'gpu_mean_utilization': {g: statistics.mean(v) if v else None for g, v in gpu_util.items()},
            'gpu_zero_percent': {g: 100 * v.count(0) / len(v) if v else None for g, v in gpu_util.items()},
            'mean_kv_percent': statistics.mean(kv) if kv else None,
            'max_kv_percent': max(kv) if kv else None,
            'mean_running_per_server': statistics.mean(running) if running else None,
            'mean_waiting_per_server': statistics.mean(waiting) if waiting else None,
            'max_waiting_per_server': max(waiting) if waiting else None,
        }
    return {'windows': windows, 'sampled_counter_totals': dict(totals),
            'requests_per_wall_minute': totals['vllm:request_success_total'] * 60 / wall_seconds,
            'generated_tokens_per_wall_second': totals['vllm:generation_tokens_total'] / wall_seconds,
            'counter_note': 'Sampled maxima per server PID; final unsampled tail may be omitted.'}


def main(plan: Path, output: Path, max_clients: int = 32, modes: str = 'direct,legacy'):
    selected_modes = modes.split(',')
    if not selected_modes or len(set(selected_modes)) != len(selected_modes) or any(
            mode not in ('direct', 'shared', 'legacy') for mode in selected_modes):
        raise ValueError('Choose direct, shared (historical proxy), and/or legacy')
    if output.exists():
        raise ValueError('Use a new output directory')
    sources = select_jobs(read_plan(plan))
    for job in sources:
        if not (Path(vllm_model_path(job)) / 'config.json').exists():
            raise ValueError('Missing export')
    for gpu in range(8):
        free, _, total = gpu_snapshot(gpu)
        if float(free) < .98 * float(total):
            raise ValueError(f'GPU {gpu} occupied')
    os.environ['WANDB_MODE'] = 'disabled'
    output.mkdir(parents=True)
    write_plan(output / 'sources.tsv', sources)
    report = {'modes': {}, 'source_plan': str(plan), 'source_count': len(sources), 'max_clients': max_clients,
              'note': '50 languages x acceptability/correction shard 0; original production sample counts; no W&B.'}
    for mode in selected_modes:
        directory = output / mode
        directory.mkdir()
        jobs = [clone_job(j, directory, i) for i, j in enumerate(sources)]
        write_plan(directory / 'plan.tsv', jobs)
        event_lock = threading.Lock()
        def event(message):
            with event_lock, (directory / 'events.log').open('a') as handle:
                handle.write(f'{time.time():.3f} {message}\n')
        store = pool = None
        if mode != 'legacy':
            local = Path(tempfile.mkdtemp(prefix='multilingual-benchmark-db-'))
            store = SQLiteJobStore(local / 'jobs.sqlite')
            store.import_jobs(jobs)
            publish_database_marker(directory, store.path)
            pool = SharedServerPool(directory, list(range(8)), event=event,
                                    gateway='proxy' if mode == 'shared' else None)
            runner = DatabaseRunner(directory, store, list(range(8)), pool, event=event, max_clients=max_clients)
            target = pool.backend.target
        else:
            runner = Runner(directory, list(range(8)), persistent_vllm=True)
            target = runner.server_pool
        measurement = Measurements(directory / 'telemetry.jsonl', target)
        start = time.monotonic()
        measurement.thread.start()
        print(f'{mode} START {directory}', flush=True)
        error = None
        try:
            runner.run()
        except Exception as exc:
            error = repr(exc)
        finally:
            if pool:
                pool.shutdown()
            measurement.finish()
        elapsed = time.monotonic() - start
        final = store.load_jobs() if store else read_plan(directory / 'plan.tsv')
        result = {'wall_seconds': elapsed, 'statuses': dict(Counter(j.status.value for j in final)),
                  'error': error, 'scores': [], 'measurements': summarize(measurement.path, elapsed)}
        for job in jobs:
            try:
                result['scores'].append(scores(job))
            except Exception as exc:
                result['scores'].append({'error': repr(exc)})
        report['modes'][mode] = result
        # Legacy splits inference and CPU export into separate rows, preserving
        # the logical job ID on the export. Validate tasks, not physical row count.
        result['complete'] = (not error and {j.job_id for j in jobs} <= {j.job_id for j in final}
            and all(job.status == JobStatus.DONE for job in final)
            and all(score and 'error' not in score
                    and score.get('total_samples', 0) > 0
                    and score.get('completed_samples') == score.get('total_samples')
                    for score in result['scores']))
        (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
        print(f'{mode} END seconds={elapsed:.1f} statuses={result["statuses"]}', flush=True)
        if not result['complete']:
            raise RuntimeError(f'{mode} campaign incomplete; no subsequent benchmark will run')
    reference = report['modes'].get('legacy')
    if reference:
        report['score_differences'] = {mode: [compare(a, b) for a, b in zip(
            reference['scores'], result['scores'])]
            for mode, result in report['modes'].items() if mode != 'legacy'}
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('COMPARISON FINISHED; all owned servers closed; production remains paused', flush=True)


if __name__ == '__main__':
    typer.run(main)
