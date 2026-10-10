"""CPU-only mixed-latency HTTP campaign; no GPU or production state access.

Synthetic service times are assumptions, not measured GPU performance.
Uses the actual gateway with mock upstream transport and real loopback clients.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import json
import math
from pathlib import Path
import random
import tempfile
import time

import httpx

from .gateway import Backend, GatewayService


def sample_profile(index, seed=42):
    rng = random.Random(seed + index * 1000003)
    correction = index % 2 == 1
    median = 6.0 if correction else 1.2
    delay = min(60, max(.1, rng.lognormvariate(math.log(median), .8)))
    if rng.random() < .02:
        delay = min(90, delay * 4)
    return delay, rng.random() < .01


def distribution(values):
    values = sorted(values)
    if not values:
        return {}
    return dict(mean=sum(values) / len(values), **{
        f'p{p}': values[min(len(values)-1, math.ceil(len(values)*p/100)-1)]
        for p in (50, 95, 99)}, maximum=values[-1])


async def simulate(root: Path, *, jobs=100, rows=500, active_jobs=32,
                   slots=1024, scale=1.0, seed=42, scheduler=False):
    if min(jobs, rows, active_jobs, slots) < 1 or scale <= 0:
        raise ValueError('Positive dimensions and time scale required')
    total = jobs * rows
    profiles = {2*(job*rows+row)+(job % 2): sample_profile(2*(job*rows+row)+(job % 2), seed)
                for job in range(jobs) for row in range(rows)}
    attempts, completions, served = Counter(), Counter(), Counter()
    active, peak_active = Counter(), Counter()
    sleep_lag, latencies, retries, job_results = [], [], Counter(), []
    transport_errors = Counter()
    mismatches = []
    started = time.monotonic()

    class Body(httpx.AsyncByteStream):
        def __init__(self, index, backend):
            self.index, self.backend = index, backend

        async def __aiter__(self):
            delay = profiles[self.index][0] * scale
            before = time.monotonic()
            try:
                # Headers arrive early; the lease must survive the response body.
                await asyncio.sleep(delay * .2)
                yield b'{"result":'
                await asyncio.sleep(delay * .8)
                yield str(self.index).encode() + b'}'
                sleep_lag.append(max(0, time.monotonic() - before - delay))
                completions[self.index] += 1
            finally:
                active[self.backend] -= 1

    def transport(config):
        async def handle(request):
            value = json.loads(request.content)
            index = value['seed']
            if value != {'model': 'actual', 'seed': index, 'stream': False,
                          'messages': [{'role': 'user', 'content': f'case {index}'}]}:
                mismatches.append(index)
            attempts[index] += 1
            if profiles[index][1] and attempts[index] == 1:
                await asyncio.sleep(.05 * scale)
                raise httpx.ReadError('injected pre-response transport failure')
            served[config.id] += 1
            active[config.id] += 1
            peak_active[config.id] = max(peak_active[config.id], active[config.id])
            return httpx.Response(200, stream=Body(index, config.id),
                                  headers={'content-type': 'application/json'})
        return httpx.MockTransport(handle)

    service = GatewayService([Backend(str(i), f'http://mock-{i}/v1', 'key',
        model_name='actual', max_num_seqs=slots) for i in range(8)],
        transport_factory=transport, timeout=600).start()
    urls = [service.register_route(f'job-{j}', compatibility_key='key', model_alias='alias')
            for j in range(jobs)]
    admission = asyncio.Semaphore(active_jobs)
    snapshots = []
    stop = asyncio.Event()

    async def monitor():
        with (root / 'telemetry.jsonl').open('w') as out:
            while not stop.is_set():
                snapshot = await asyncio.to_thread(service.snapshot)
                record = {'elapsed': time.monotonic()-started, **snapshot}
                snapshots.append(record)
                out.write(json.dumps(record)+'\n')
                out.flush()
                try:
                    await asyncio.wait_for(stop.wait(), timeout=1)
                except TimeoutError:
                    pass

    async def run_job(job):
        async with admission:
            begin = time.monotonic()
            concurrency = min(rows, 256 if job % 2 else 512)
            pending = iter(range(rows))
            async with httpx.AsyncClient(trust_env=False, timeout=600,
                    limits=httpx.Limits(max_connections=concurrency,
                                       max_keepalive_connections=concurrency)) as client:
                async def worker():
                    for row in pending:
                        index = 2*(job*rows+row)+(job % 2)
                        request_start = time.monotonic()
                        for attempt in range(5):
                            status = None
                            try:
                                response = await client.post(urls[job]+'/chat/completions', json={
                                    'model': 'alias', 'seed': index, 'stream': False,
                                    'messages': [{'role': 'user', 'content': f'case {index}'}]})
                                status = response.status_code
                                if status == 200:
                                    assert response.json() == {'result': index}
                                    latencies.append(time.monotonic()-request_start)
                                    break
                                if status not in (429, 500, 502, 503, 504):
                                    response.raise_for_status()
                            except httpx.TransportError as exc:
                                transport_errors[type(exc).__name__] += 1
                            retries[str(status or 'transport')] += 1
                            if attempt == 4:
                                raise RuntimeError(f'Request {index} exhausted retry budget')
                            await asyncio.sleep(min(4, .2*2**attempt) + random.Random(index+attempt).random()*.2)
                workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
                try:
                    await asyncio.gather(*workers)
                finally:
                    for worker in workers:
                        if not worker.done():
                            worker.cancel()
                    await asyncio.gather(*workers, return_exceptions=True)
            result = {'job': job, 'family': 'correction' if job % 2 else 'acceptability',
                      'rows': rows, 'start_seconds': begin-started,
                      'wall_seconds': time.monotonic()-begin}
            job_results.append(result)
            print(f'jobs {len(job_results)}/{jobs}; rows {len(latencies)}/{total}', flush=True)

    async def coordinated():
        from .cpu_budget import CpuBudget
        from .database_runner import DatabaseRunner
        from .model import Action, Job, JobStatus
        from .store import SQLiteJobStore

        # Only server ownership is mocked. Claims, dependencies, CPU leases,
        # snapshots and completion updates use the real isolated coordinator.
        class Pool:
            def configured_job(self, job):
                return job

            def snapshot_state(self):
                return {'accepting': True, 'slots': {}, 'gateway': service.snapshot()}

            def close_all(self):
                state = service.snapshot()
                assert not state['active'] and not state['queued']

            def reopen(self):
                pass

        store = SQLiteJobStore(root/'jobs.sqlite')
        eval_jobs = [Job(str(j), Action.EVAL_DFM, 'simulation', 'correction' if j % 2 else 'acceptability',
                        initial_batch=256 if j % 2 else 512,
                        metadata={'external_model': 'cpu-mock'}, log_dir=str(root/str(j)))
                     for j in range(jobs)]
        store.import_jobs(eval_jobs + [Job('merge', Action.MERGE_DFM, 'simulation', 'merge',
                                          deps=tuple(j.job_id for j in eval_jobs), log_dir=str(root/'merge'))])
        loop = asyncio.get_running_loop()
        def execute(job, *_):
            if job.action == Action.MERGE_DFM:
                assert len(job_results) == jobs
                return 0
            asyncio.run_coroutine_threadsafe(run_job(int(job.job_id)), loop).result()
            return 0
        runner = DatabaseRunner(root, store, list(range(8)), Pool(),
            cpu_budget=CpuBudget(total_cores=min(256, active_jobs*2+8), reserve_cores=8),
            max_clients=active_jobs, execute=execute, headroom=lambda *_: True,
            poll_interval=.05)
        outcome = await asyncio.to_thread(runner.run)
        states = Counter(job.status.value for job in store.load_jobs())
        receipt['coordinator'] = {'outcome': outcome, 'states': dict(states),
                                  'cpu_cores_released': runner.cpu_budget.available_cores == runner.cpu_budget.capacity}
        assert outcome == 'done' and all(job.status == JobStatus.DONE for job in store.load_jobs())

    observer = asyncio.create_task(monitor())
    receipt = {'passed': False, 'scope': 'CPU gateway transport and client scheduling; not DatabaseRunner or GPU parity',
               'settings': dict(jobs=jobs, rows=rows, active_jobs=active_jobs, slots=slots, scale=scale, seed=seed, scheduler=scheduler),
               'latency_assumptions': 'lognormal sigma .8; medians acceptability 1.2s, correction 6s; 2% 4x tail, capped 90s; 1% first-attempt ReadError'}
    if scheduler:
        receipt['scope'] = 'Real isolated SQLite coordinator and HTTP gateway; mock server ownership/inference; no GPUs'
    tasks = [asyncio.create_task(coordinated())] if scheduler else [
        asyncio.create_task(run_job(job)) for job in range(jobs)]
    try:
        await asyncio.gather(*tasks)
        final = service.snapshot()
        assert len(completions) == total and all(v == 1 for v in completions.values())
        assert not mismatches and not final['active'] and not final['queued']
        assert all(v <= slots for v in peak_active.values())
        receipt['passed'] = True
    except BaseException as exc:
        receipt['error'] = repr(exc)
        raise
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        stop.set()
        await observer
        await asyncio.to_thread(service.close, timeout=120)
        wall = time.monotonic()-started
        receipt.update(wall_seconds=wall, rows_completed=len(latencies), rows_per_second=len(latencies)/wall,
            retries=dict(retries), transport_error_types=dict(transport_errors),
            requests_per_backend=dict(served), peak_active_per_backend=dict(peak_active),
            request_latency_seconds=distribution(latencies), sleep_overshoot_seconds=distribution(sleep_lag),
            service_seconds=distribution([p[0]*scale for p in profiles.values()]), jobs=job_results,
            mean_active=sum(s['active'] for s in snapshots)/max(1,len(snapshots)),
            peak_queued=max((s['queued'] for s in snapshots), default=0),
            payload_mismatches=len(mismatches), duplicate_completed_responses=sum(v-1 for v in completions.values()),
            pending_client_tasks=sum(not t.done() for t in tasks))
        (root/'result.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name, default in [('jobs',100), ('rows',500), ('active-jobs',32), ('slots',1024), ('seed',42)]:
        parser.add_argument('--'+name, type=int, default=default)
    parser.add_argument('--scale', type=float, default=1)
    parser.add_argument('--scheduler', action='store_true')
    args = parser.parse_args()
    root = Path(tempfile.mkdtemp(prefix='gateway-latency-', dir='/tmp'))
    print(root, flush=True)
    asyncio.run(simulate(root, **vars(args)))
    print(root/'result.json', flush=True)


if __name__ == '__main__':
    main()
