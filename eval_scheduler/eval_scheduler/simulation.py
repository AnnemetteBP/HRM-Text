"""Isolated CPU-only SQLite scheduler benchmark; never executes scheduler jobs.

Run: python -m eval_scheduler.simulation --output /tmp/store-simulation-new
The output directory must not exist. No live plans, GPU queries or W&B calls.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import random
import sqlite3
import statistics
import time

from .model import Action, Job, JobStatus, read_plan
from .runtime import dependencies_satisfied
from .store import SQLiteJobStore


def synthetic_jobs(count: int, seed: int) -> list[Job]:
    """Independent 16-node DAGs include transitive failure and optional gates."""
    rng = random.Random(seed)
    jobs = []
    for i in range(count):
        base, slot = i - i % 16, i % 16
        status, mode, deps = JobStatus.PENDING, 'success', ()
        action, name = Action.REPORT, f'case-{i}'
        if slot == 0:
            status = JobStatus.FAILED
        elif slot == 1:
            deps = (str(base),)
        elif slot == 2:
            deps, mode = (str(base + 1),), 'terminal'
        elif slot == 3:
            status = JobStatus.SKIPPED
        elif slot == 4:
            deps, mode = (str(base + 3),), 'terminal'
        elif slot == 5:
            action, name, status = Action.EVAL_EUROEVAL, f'valeu-{i}', JobStatus.RUNNING
        elif slot == 6:
            deps = (str(base + 5),)
        elif slot == 7:
            status = JobStatus.DONE
        elif slot == 8:
            deps = (str(base + 7),)
        elif slot > 9:
            deps = tuple(str(j) for j in range(base, i) if rng.random() < .15)
            mode = rng.choice(['success', 'terminal'])
            status = rng.choice(list(JobStatus))
        jobs.append(Job(str(i), action, 'simulation', name, deps=deps,
                        deps_mode=mode, status=status, log_dir=f'synthetic/{i}',
                        metadata={'simulation_only': True, 'payload': 'x' * 128}))
    return jobs


def _digest(ids) -> str:
    return hashlib.sha256(json.dumps(list(ids), separators=(',', ':')).encode()).hexdigest()


def _equivalence(store, jobs) -> dict:
    by_id = {j.job_id: j for j in jobs}
    cache = {}
    start = time.perf_counter()
    expected = [j.job_id for j in jobs if j.status == JobStatus.PENDING and
                dependencies_satisfied(j, jobs, jobs_by_id=by_id, failure_cache=cache)]
    legacy_seconds = time.perf_counter() - start
    start = time.perf_counter()
    actual = [j.job_id for j in store.ready_jobs()]
    sqlite_seconds = time.perf_counter() - start
    if actual != expected:
        raise AssertionError(f'readiness mismatch: expected {len(expected)}, got {len(actual)}')
    return {'equal': True, 'ready_count': len(actual), 'ordered_ids_sha256': _digest(actual),
            'legacy_seconds': legacy_seconds, 'sqlite_seconds': sqlite_seconds}


def run(output: Path, jobs: int = 40000, seed: int = 39, batch_size: int = 128) -> dict:
    if jobs < 16 or batch_size < 1:
        raise ValueError('jobs must be >=16 and batch_size >=1')
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {'schema_version': 1, 'status': 'running', 'cpu_only': True,
              'execution': 'store-only; no task execution or DatabaseRunner',
              'jobs': jobs, 'seed': seed, 'batch_size': batch_size,
              'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version,
              'output': str(output), 'timings_seconds': {}}
    timings = report['timings_seconds']
    try:
        fixture = synthetic_jobs(jobs, seed)
        report['initial_status_counts'] = dict(Counter(str(j.status) for j in fixture))
        report['fixture_sha256'] = hashlib.sha256(json.dumps(
            [j.to_row() for j in fixture], sort_keys=True).encode()).hexdigest()
        start = time.perf_counter()
        store = SQLiteJobStore(output / 'jobs.sqlite')
        store.import_jobs(fixture)
        timings['initial_import'] = time.perf_counter() - start
        report['readiness_before'] = _equivalence(store, fixture)
        start = time.perf_counter()
        selected = store.ready_jobs(limit=batch_size)
        timings['ready_bounded'] = time.perf_counter() - start
        start = time.perf_counter()
        claims = store.claim_jobs(j.job_id for j in selected)
        timings['claim_batch'] = time.perf_counter() - start
        assert list(claims) == [j.job_id for j in selected]
        start = time.perf_counter()
        reopened = SQLiteJobStore(output / 'jobs.sqlite')
        assert all(reopened.attempt_token(key) == claim.token for key, claim in claims.items())
        timings['reopen_verify_tokens'] = time.perf_counter() - start
        store = reopened
        store.set_admin_lock(True)
        assert store.get_admin_lock() and not store.claim_jobs(str(i) for i in range(jobs))
        latencies = []
        for key, claim in claims.items():
            start = time.perf_counter()
            assert store.finish(key, claim.token, {'status': 'done'})
            latencies.append(time.perf_counter() - start)
            assert not store.finish(key, claim.token, {'status': 'failed'})
        store.set_admin_lock(False)
        report['claim_count'] = len(claims)
        report['finish_latency_seconds'] = {
            'count': len(latencies), 'total': sum(latencies),
            'median': statistics.median(latencies),
            'p95': sorted(latencies)[min(len(latencies)-1, int(len(latencies)*.95))],
            'max': max(latencies)}
        start = time.perf_counter()
        store.update_jobs({key: {'log_dir': f'completed/{key}'} for key in claims})
        timings['runtime_update_batch'] = time.perf_counter() - start
        current = store.load_jobs()
        report['readiness_after'] = _equivalence(store, current)
        start = time.perf_counter()
        store.import_jobs(fixture)
        assert store.load_jobs() == current
        timings['stale_import_preserving_runtime'] = time.perf_counter() - start
        start = time.perf_counter()
        export = output / 'snapshot.tsv'
        store.export_tsv(export)
        assert read_plan(export) == current
        timings['export_and_roundtrip'] = time.perf_counter() - start
        report['export_sha256'] = hashlib.sha256(export.read_bytes()).hexdigest()
        start = time.perf_counter()
        assert SQLiteJobStore(output / 'jobs.sqlite').load_jobs() == current
        timings['reopen_and_full_load'] = time.perf_counter() - start
        report['final_status_counts'] = dict(Counter(str(j.status) for j in current))
        report['checks'] = {'legacy_readiness': True, 'persisted_tokens': True,
                            'admin_fence': True, 'stale_finish_rejected': True,
                            'runtime_log_dir_preserved': True, 'tsv_roundtrip': True}
        report['status'] = 'passed'
    except BaseException as exc:
        report['status'] = 'failed'
        report['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        temp = output / 'report.json.tmp'
        temp.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        temp.replace(output / 'report.json')
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New isolated directory; must not exist')
    parser.add_argument('--jobs', type=int, default=40000)
    parser.add_argument('--seed', type=int, default=39)
    parser.add_argument('--batch-size', type=int, default=128)
    args = parser.parse_args()
    result = run(args.output, args.jobs, args.seed, args.batch_size)
    print(json.dumps({'status': result['status'], 'report': str(args.output / 'report.json'),
                      'jobs': result['jobs'], 'timings_seconds': result['timings_seconds']}))


if __name__ == '__main__':
    main()
