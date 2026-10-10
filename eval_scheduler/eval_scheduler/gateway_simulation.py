"""Isolated real-HTTP gateway load check; upstreams are in-memory mocks.

Run: python -m eval_scheduler.gateway_simulation --requests 4096
Writes a receipt in a newly created /tmp/gateway-simulation-* directory.
No GPU, scheduler, database, credentials, or production endpoint access.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import json
from pathlib import Path
import tempfile
import threading
import time

import httpx

from .gateway import Backend, GatewayService


class Body(httpx.AsyncByteStream):
    async def __aiter__(self):
        yield b'{"choices":[]}'


def payload(index):
    return {'model': 'alias', 'messages': [{'role': 'user', 'content': f'case {index}'}],
            'temperature': 0, 'seed': index, 'stream': False,
            'tools': [{'type': 'function', 'function': {'name': 'read',
                       'parameters': {'type': 'object', 'properties': {}}}}]}


async def simulate(count, receipt=None, checkpoint=lambda: None):
    if count < 1 or count > 8192:
        raise ValueError('Request count must be 1..8192 (eight 1024-slot backends)')
    release = asyncio.Event()
    cancel_entered = threading.Event()
    cancel_release = asyncio.Event()
    counts = Counter()
    mismatches = []
    seen = set()
    highs = {}
    receipt = receipt if receipt is not None else {}
    receipt.update(passed=False, requests=count, stage='load', backend_count=8)
    checkpoint()

    def transport(config):
        async def handler(request):
            value = json.loads(request.content)
            index = value['seed']
            expected = payload(index)
            expected['model'] = 'actual'
            if value != expected:
                mismatches.append(index)
            if index == -1:
                cancel_entered.set()
                await cancel_release.wait()
            else:
                seen.add(index)
                counts[config.id] += 1
                await release.wait()
            return httpx.Response(200, stream=Body(), headers={'content-type': 'application/json'})
        return httpx.MockTransport(handler)

    service = GatewayService([
        Backend(str(i), f'http://mock-{i}/v1', 'key', model_name='actual')
        for i in range(8)], transport_factory=transport, timeout=180).start()
    urls = [service.register_route(f'client-{i}', compatibility_key='key', model_alias='alias')
            for i in range(8)]

    def unblock(event):
        # These events are awaited only on the gateway loop, never the client
        # loop. Signal there as well: asyncio.Event is not thread-safe.
        loop = service.gateway.loop
        if loop is not None and not loop.is_closed():
            loop.call_soon_threadsafe(event.set)
    started = time.monotonic()
    tasks = []
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=180,
                limits=httpx.Limits(max_connections=count+8, max_keepalive_connections=count+8)) as client:
            async def send(i):
                result = await client.post(urls[i % 8]+'/chat/completions', json=payload(i))
                return result.status_code

            tasks = [asyncio.create_task(send(i)) for i in range(count)]
            deadline = time.monotonic()+150
            while True:
                snapshot = service.snapshot()
                for name, state in snapshot['backends'].items():
                    peak = highs.setdefault(name, {'active': 0, 'queued': 0})
                    for field in peak:
                        peak[field] = max(peak[field], state[field])
                    assert state['active'] <= 1024 and state['queued'] <= 2048
                if snapshot['active'] == count:
                    break
                if any(t.done() for t in tasks) or time.monotonic() > deadline:
                    raise RuntimeError(f'Concurrent admission incomplete: {snapshot}')
                await asyncio.sleep(.05)
            concurrent = snapshot['active']
            unblock(release)
            statuses = await asyncio.gather(*tasks)
            assert statuses == [200]*count
            assert not mismatches and len(seen) == count
            assert len(counts) == min(count, 8)
            receipt.update(load_passed=True, concurrent_admitted=concurrent,
                           requests_per_backend=dict(counts), peak_counts=highs,
                           payload_mismatches=list(mismatches), stage='close_load_pool',
                           load_elapsed_seconds=time.monotonic()-started)
            checkpoint()
            pool_close_started = time.monotonic()
        receipt['load_pool_close_seconds'] = time.monotonic()-pool_close_started
        # The cancellation invariant concerns the gateway, not selection among
        # thousands of idle client connections. Use a fresh real TCP connection
        # after closing the load pool, and record transport events for diagnosis.
        trace = []
        probe_started = time.monotonic()

        async def trace_event(name, info):
            trace.append({'event': name, 'seconds': time.monotonic()-probe_started})

        receipt.update(stage='cancellation_probe', probe_transport_events=trace)
        checkpoint()
        async with httpx.AsyncClient(trust_env=False, timeout=10,
                limits=httpx.Limits(max_connections=1, max_keepalive_connections=0)) as probe:
            cancelled = asyncio.create_task(probe.post(urls[0]+'/chat/completions',
                json=payload(-1), extensions={'trace': trace_event}))
            tasks.append(cancelled)
            deadline = time.monotonic()+10
            while not cancel_entered.is_set():
                if cancelled.done():
                    result = await cancelled
                    raise RuntimeError(f'Cancellation probe ended before upstream: {result.status_code}')
                if time.monotonic() >= deadline:
                    receipt['probe_timeout_snapshot'] = service.snapshot()
                    checkpoint()
                    raise TimeoutError('Cancellation probe did not reach upstream within 10s')
                await asyncio.sleep(.01)
            receipt['probe_upstream_entered_seconds'] = time.monotonic()-probe_started
            cancelled.cancel()
            await asyncio.gather(cancelled, return_exceptions=True)
            await asyncio.sleep(.1)
            retained = service.snapshot()['active']
            assert retained == 1, 'Cancellation released backend admission prematurely'
            try:
                service.close(timeout=.05)
            except TimeoutError:
                pass
            else:
                raise AssertionError('Drain did not wait for cancelled upstream work')
            assert service.poll() is None
            unblock(cancel_release)
            deadline = time.monotonic()+10
            while service.snapshot()['active']:
                assert time.monotonic() < deadline, 'Cancelled upstream failed to drain within 10s'
                await asyncio.sleep(.01)
        service.close(timeout=10)
        receipt.update({'passed': True, 'stage': 'complete', 'requests': count, 'concurrent_admitted': concurrent,
                'backend_count': 8, 'requests_per_backend': dict(counts),
                'peak_counts': highs, 'active_limit_per_backend': 1024,
                'queue_limit_per_backend': 2048, 'payload_mismatches': mismatches,
                'cancelled_request_retained_until_upstream_complete': retained == 1,
                'drain_timeout_then_clean_close': service.poll() == 0,
                'elapsed_seconds': time.monotonic()-started,
                'transport': 'real loopback HTTP frontend; httpx MockTransport upstream',
                'upstream_wait': 'gateway-loop asyncio.Event; no per-request polling',
                'scope': 'isolated CPU only; no production endpoints'})
        checkpoint()
        return receipt
    finally:
        unblock(release)
        unblock(cancel_release)
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        receipt['pending_client_tasks_after_cleanup'] = sum(not task.done() for task in tasks)
        service.close(timeout=10)
        checkpoint()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--requests', type=int, default=4096)
    args = parser.parse_args()
    root = Path(tempfile.mkdtemp(prefix='gateway-simulation-', dir='/tmp'))
    receipt = {}
    def checkpoint():
        temporary = root/'result.tmp'
        temporary.write_text(json.dumps(receipt, indent=2)+'\n')
        temporary.replace(root/'result.json')
    try:
        asyncio.run(simulate(args.requests, receipt, checkpoint))
    except BaseException as exc:
        receipt.update(passed=False, error_type=type(exc).__name__, error=str(exc))
        checkpoint()
        print(root/'result.json', flush=True)
        raise
    (root/'result.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(root/'result.json', flush=True)


if __name__ == '__main__':
    main()
