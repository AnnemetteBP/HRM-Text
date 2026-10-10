from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from eval_scheduler.model import Action, Job
from eval_scheduler.shared_pool import ClientMonitor, SharedServerPool as _SharedServerPool, compatibility_key


def SharedServerPool(*args, **kwargs):
    # Historical gateway tests deliberately exercise the opt-in old transport.
    if len(args) < 3:
        kwargs.setdefault('gateway', 'proxy')
    return _SharedServerPool(*args, **kwargs)


def job(tmp_path, **metadata):
    return Job(job_id='client', action=Action.EVAL_DFM, family='dfm', name='dala',
               log_dir=str(tmp_path), metadata={
                   'ckpt_tag': 'step_1', 'hrm_hf_export_dir': str(tmp_path / 'model'),
                   'host': '127.0.0.1', 'port_base': 18000, 'python_bin': 'python',
                   'vllm_gpu_memory_utilization': .8, **metadata})


def test_judged_cold_start_leaves_room_for_other_tasks(tmp_path):
    import asyncio
    from eval_scheduler.shared_pool import NativeGatewayHost
    host = NativeGatewayHost(SimpleNamespace(gpus=tuple(range(8))))
    host.jobs['judge-key'] = job(tmp_path, judge_server_model='judge').with_updates(name='generative_talemaader')
    selected = []
    async def start(key, gpus):
        selected.extend(gpus)
        return [SimpleNamespace(gpu=g) for g in gpus]
    host._start_gpus = start
    host._configs = lambda key, lease: [lease.gpu]
    async def run():
        host._placement_lock = asyncio.Lock()
        host._changed = asyncio.Event()
        return await host._provision('judge-key')
    assert asyncio.run(run()) == [0]
    assert selected == [0]


def test_different_models_start_concurrently_without_gpu_collision(tmp_path):
    import asyncio
    from eval_scheduler.shared_pool import NativeGatewayHost
    host = NativeGatewayHost(SimpleNamespace(gpus=(0, 1)))
    host.jobs = {key: job(tmp_path, judge_server_model='judge').with_updates(name='generative_talemaader')
                 for key in ('a', 'b')}
    host.engine = SimpleNamespace(provision_waiters={}, backends={})
    started = {}
    host._configs = lambda key, lease: [lease.gpu]
    async def run():
        host._placement_lock = asyncio.Lock()
        host._changed = asyncio.Event()
        both = asyncio.Event()
        async def start(key, gpus):
            started[key] = gpus
            if len(started) == 2:
                both.set()
            await asyncio.wait_for(both.wait(), 1)
            return [SimpleNamespace(gpu=g) for g in gpus]
        host._start_gpus = start
        await asyncio.gather(host._provision('a'), host._provision('b'))
    asyncio.run(run())
    assert {tuple(g) for g in started.values()} == {(0,), (1,)}
    assert not host.starting


def test_extra_replicas_require_real_queued_requests():
    from eval_scheduler.shared_pool import NativeGatewayHost
    host = NativeGatewayHost(None)
    state = SimpleNamespace(config=SimpleNamespace(compatibility_key='a', role='target', max_num_seqs=1024),
                            draining=False, tickets=set(range(32)))
    host.engine = SimpleNamespace(backends={'one': state})
    assert host._additional_replicas('a') == 0
    state.tickets = set(range(2500))
    assert host._additional_replicas('a') == 2


@pytest.fixture
def setup(tmp_path):
    backend = Mock()
    backend.acquire.side_effect = lambda j, g: SimpleNamespace(
        base_url=f'http://gpu{g}/v1', model_name=f'real-{g}', log_path=tmp_path / 'server.log',
        process=SimpleNamespace(poll=lambda: None))
    gateway = Mock()
    gateway.poll.return_value = None
    gateway.register_job.return_value = 'http://gateway/v1'
    pool = SharedServerPool(tmp_path, [0], gateway, backend=backend,
                            snapshot=lambda g: (100, 0, 100), max_requests_per_gpu=2)
    yield pool, backend, gateway
    pool._executor.shutdown(wait=True)


def test_lazy_client_registration_no_gpu_reservation(setup, tmp_path):
    pool, backend, gateway = setup
    def callback(url, log, monitor, alias):
        assert url == 'http://gateway/v1' and log.exists()
        assert monitor.shared_client and monitor.pid is None
        assert alias.startswith('shared-')
        backend.acquire.assert_not_called()
        return 0
    assert pool.run_client(job(tmp_path), callback) == 0
    gateway.unregister_route.assert_called_once()


def test_request_release_reuse_and_idempotence(setup, tmp_path):
    pool, backend, _ = setup
    one = pool._acquire_residency(job(tmp_path)); two = pool._acquire_residency(job(tmp_path))
    assert backend.acquire.call_count == 1
    one.release(); one.release()
    assert pool.snapshot_state()['slots'][0]['residency_holds'] == 1
    two.release()
    pool.close_all()
    backend.close_all.assert_called_once()


def test_no_replace_or_close_with_inflight(setup, tmp_path):
    pool, backend, _ = setup
    lease = pool._acquire_residency(job(tmp_path))
    with pytest.raises(TimeoutError):
        pool._acquire_residency(job(tmp_path, ckpt_tag='step_2'), timeout=0)
    with pytest.raises(TimeoutError):
        pool.close_all(timeout=0)
    backend.release_gpu.assert_not_called(); backend.close_all.assert_not_called()
    with pytest.raises(RuntimeError, match='draining'):
        pool._acquire_residency(job(tmp_path))
    lease.release(confirmed=False)
    with pytest.raises(TimeoutError):
        pool.close_all(timeout=0)
    lease.release(); pool.close_all(); pool.reopen()
    pool._acquire_residency(job(tmp_path)).release()


def test_replace_only_idle_and_check_actual_headroom(setup, tmp_path):
    pool, backend, _ = setup
    pool._acquire_residency(job(tmp_path)).release()
    pool.snapshot = lambda g: (10, 90, 100)
    with pytest.raises(RuntimeError, match='headroom'):
        pool._acquire_residency(job(tmp_path, ckpt_tag='step_2'))
    backend.release_gpu.assert_called_once()
    assert backend.acquire.call_count == 1
    assert not pool.snapshot_state()['slots'][0]['provisioning']


def test_startup_thread_separate_from_client(setup, tmp_path):
    import threading
    pool, backend, _ = setup
    seen = []
    original = backend.acquire.side_effect
    def acquire(j, g):
        seen.append(threading.current_thread().name)
        return original(j, g)
    backend.acquire.side_effect = acquire
    pool._acquire_residency(job(tmp_path)).release()
    assert seen[0].startswith('shared-provision')


def test_singleflight_concurrent_provision(setup, tmp_path):
    pool, backend, _ = setup
    with ThreadPoolExecutor(max_workers=2) as workers:
        leases = list(workers.map(lambda _: pool._acquire_residency(job(tmp_path)), range(2)))
    assert backend.acquire.call_count == 1
    for lease in leases: lease.release()


def test_monitor_termination_is_not_gateway_termination(setup):
    _, _, gateway = setup
    one, two = ClientMonitor(gateway), ClientMonitor(gateway)
    with pytest.raises(subprocess.TimeoutExpired): one.wait(timeout=0)
    one.terminate()
    assert one.wait() == 143 and two.poll() is None
    one.kill(); assert one.wait() == 137
    gateway.terminate.assert_not_called(); gateway.kill.assert_not_called()
    gateway.poll.return_value = 71
    assert two.poll() == 71


def test_snapshot_metrics_outside_condition(setup, monkeypatch):
    from eval_scheduler.shared_pool import NativeGatewayHost
    pool, _, _ = setup
    pool.gateway = NativeGatewayHost(pool)
    def metrics():
        assert not pool._condition._is_owned()
        return {'available': True, 'stale': False, 'active': 3, 'queued': 2,
                'clients': 2, 'job_ids': ['a', 'b'], 'provisioning_queued': {'key': 4},
                'backends': {'backend': {'gpu': 0, 'active': 3, 'queued': 2, 'max_num_seqs': 1024,
                                       'job_ids': ['a'], 'registered_job_ids': ['a', 'b']}}}
    monkeypatch.setattr(pool.gateway, 'snapshot_cached', metrics)
    state = pool.snapshot_state()
    assert state['slots'][0]['active'] == 3 and state['slots'][0]['queued'] == 2
    assert state['slots'][0]['capacity'] == 1024 and state['slots'][0]['job_ids'] == ['a']
    assert state['totals']['clients'] == 2 and state['totals']['provisioning_queued'] == 4
    assert (state['active'], state['queued'], state['capacity']) == (3, 2, 1024)


def test_snapshot_cache_timeout_bounded_and_no_zero_fabrication(setup, monkeypatch):
    from concurrent.futures import Future
    from eval_scheduler.shared_pool import NativeGatewayHost
    pool, _, _ = setup
    host = NativeGatewayHost(pool); host.thread = Mock(); host.loop = Mock()
    calls = []
    def read(coroutine, loop):
        coroutine.close(); calls.append(loop)
        future = Future()
        future.set_result({'active': 7, 'queued': 1, 'backends': {}})
        return future
    monkeypatch.setattr('eval_scheduler.shared_pool.asyncio.run_coroutine_threadsafe', read)
    assert host.snapshot_cached()['active'] == 7
    assert host.snapshot_cached()['active'] == 7 and len(calls) == 1
    future = Mock()
    future.result.side_effect = TimeoutError()
    def timeout(coroutine, loop):
        coroutine.close()
        return future
    monkeypatch.setattr('eval_scheduler.shared_pool.asyncio.run_coroutine_threadsafe', timeout)
    host._snapshot_attempt = float('-inf')
    cached = host.snapshot_cached()
    future.result.assert_called_once_with(timeout=.1)
    assert cached['stale'] and cached['active'] == 7
    host._snapshot_value = None
    assert host.snapshot_cached()['available'] is False


def test_managed_judge_registration_is_lazy(setup, tmp_path):
    pool, backend, gateway = setup
    managed = job(tmp_path, judge_server_model='judge').with_updates(name='generative_talemaader')
    def callback(url, log, monitor, alias):
        assert monitor.judge_base_url == 'http://gateway-judge/v1'
        backend.acquire.assert_not_called()
        return 0
    assert pool.run_client(managed, callback) == 0
    gateway.register_job.assert_called_once()


def test_managed_pair_routes_and_drains_judge_before_replacement(tmp_path):
    import asyncio
    import httpx
    import json
    import threading
    started, finish = threading.Event(), threading.Event()
    events = []
    backend = Mock()
    backend.acquire.side_effect = lambda j, g: SimpleNamespace(
        base_url='http://target/v1', model_name='target',
        judge_base_url='http://judge/v1', judge_model_name='judge',
        log_path=tmp_path/'server.log', process=SimpleNamespace(poll=lambda: None))
    backend.release_gpu.side_effect = lambda *a: events.append('evicted')
    pool = SharedServerPool(tmp_path, [0], backend=backend, snapshot=lambda g: (180000, 0, 180000))
    managed = pool.configured_job(job(tmp_path, judge_server_model='judge', judge_model='openai/judge')
                                  .with_updates(name='generative_talemaader'))
    workers = ThreadPoolExecutor(max_workers=2)
    try:
        url = pool.gateway.register_job('one', managed)
        url2 = pool.gateway.register_job('two', managed.with_updates(metadata={**managed.metadata, 'ckpt_tag': 'step_2'}))

        class Body(httpx.AsyncByteStream):
            def __init__(self, hold):
                self.hold = hold

            async def __aiter__(self):
                if self.hold:
                    started.set()
                    while not finish.is_set():
                        await asyncio.sleep(.01)
                    events.append('judge_complete')
                yield b'{"choices":[]}'

        seen = []
        def respond(request):
            payload = json.loads(request.content)
            seen.append((request.url.host, payload['model']))
            return httpx.Response(200, stream=Body(payload.get('hold', False)))

        async def configure():
            pool.gateway.engine.transport_factory = lambda config: httpx.MockTransport(respond)
        pool.gateway._call(configure())

        def request(endpoint, model, hold=False):
            with httpx.Client(trust_env=False, timeout=10) as client:
                response = client.post(endpoint+'/chat/completions', json={'model': model, 'hold': hold})
                assert response.status_code == 200, response.text

        backend.acquire.assert_not_called()
        request(url, 'one')
        pending = workers.submit(request, url.removesuffix('/v1')+'-judge/v1', 'judge', True)
        assert started.wait(5)
        replacement = workers.submit(request, url2, 'two')
        assert 'evicted' not in events
        finish.set()
        pending.result(10)
        replacement.result(10)
        assert events.index('judge_complete') < events.index('evicted')
        assert ('judge', 'judge') in seen and ('target', 'target') in seen
        pool.gateway.unregister_route('one')
        assert 'one-judge' not in pool.gateway.engine.routes
    finally:
        finish.set()
        workers.shutdown(wait=True)
        pool.shutdown(10)


def test_key_tracks_server_args_and_mutable_tokenizer(tmp_path):
    model = tmp_path / 'model'; model.mkdir()
    tokenizer = model / 'tokenizer.json'; tokenizer.write_text('one')
    first = compatibility_key(job(tmp_path), 0)
    tokenizer.write_text('changed')
    assert compatibility_key(job(tmp_path), 0) != first
    assert compatibility_key(job(tmp_path, vllm_extra_args='--enforce-eager'), 0) != compatibility_key(job(tmp_path), 0)


def test_callback_failure_unregisters_without_stopping_server(setup, tmp_path):
    pool, backend, gateway = setup
    with pytest.raises(ValueError):
        pool.run_client(job(tmp_path), Mock(side_effect=ValueError('bad client')))
    gateway.unregister_route.assert_called_once()
    backend.close_all.assert_not_called(); backend.release_gpu.assert_not_called()


def test_capacity_and_preflight_no_gpu(tmp_path):
    pool = SharedServerPool(tmp_path, [0], Mock(), backend=Mock(), snapshot=Mock())
    try:
        configured = pool.preflight([job(tmp_path)])[0]
        assert pool.capacity == pool.request_capacity(configured) == 1024
        assert '--max-num-seqs 1024' in configured.metadata['vllm_extra_args']
        assert pool.request_capacity(job(tmp_path, vllm_extra_args='--max-num-seqs=512')) == 512
        assert pool.request_capacity(job(tmp_path, vllm_extra_args='--max-num-seqs 2048')) == 2048
        pool.backend.acquire.assert_not_called()
        pool.preflight([job(tmp_path, judge_server_model='judge').with_updates(name='generative_talemaader')])
        pool.backend.acquire.assert_not_called()
    finally:
        pool._executor.shutdown()


def test_native_startup_queue_scales_with_gpus_and_explicit_capacity(tmp_path):
    pool = SharedServerPool(tmp_path, list(range(8)), backend=Mock(), snapshot=Mock())
    try:
        pool.gateway.register_job('default', job(tmp_path))
        assert pool.gateway.engine.provision_queue_capacity == 24576
        async def failed_provision():
            import asyncio
            key = pool.gateway.engine.routes['default'].compatibility_key
            future = asyncio.get_running_loop().create_future()
            future.set_exception(RuntimeError('startup failed'))
            pool.gateway.engine.provisioning[key] = future
            return key
        failed_key = pool.gateway._call(failed_provision())
        pool.gateway.register_job('retry', job(tmp_path))
        assert failed_key not in pool.gateway.engine.provisioning
        pool.gateway.register_job('larger', job(tmp_path, vllm_extra_args='--max-num-seqs 2048'))
        assert pool.gateway.engine.provision_queue_capacity == 49152
        pool.gateway.register_job('smaller', job(tmp_path, vllm_extra_args='--max-num-seqs 512'))
        assert pool.gateway.engine.provision_queue_capacity == 49152
        pool.backend.acquire.assert_not_called()
    finally:
        pool.shutdown()


def test_normal_registration_does_not_wait_for_placement_lock(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    pool = SharedServerPool(tmp_path, [0], backend=Mock(), snapshot=Mock())
    worker = ThreadPoolExecutor(max_workers=1)
    try:
        pool.gateway._start()
        pool.gateway._call(pool.gateway._placement_lock.acquire(), 2)
        pending = worker.submit(pool.gateway.register_job, 'fast', job(tmp_path))
        assert pending.result(timeout=2).endswith('/fast/v1')
        pool.backend.acquire.assert_not_called()
    finally:
        async def unlock():
            if pool.gateway._placement_lock.locked():
                pool.gateway._placement_lock.release()
        pool.gateway._call(unlock(), 2)
        worker.shutdown(wait=True)
        pool.shutdown()


def test_provision_resets_inherited_client_affinity(setup, tmp_path):
    import os
    pool, backend, _ = setup
    original = set(os.sched_getaffinity(0))
    observed = []
    acquire = backend.acquire.side_effect
    def capture(j, g):
        observed.append(set(os.sched_getaffinity(0)))
        return acquire(j, g)
    backend.acquire.side_effect = capture
    try:
        os.sched_setaffinity(0, {min(original)})
        pool._acquire_residency(job(tmp_path)).release()
    finally:
        os.sched_setaffinity(0, original)
    assert observed == [original]


def test_native_gateway_http_lazy_two_gpus_alias_and_drain(tmp_path):
    import httpx
    backend = Mock()
    backend.acquire.side_effect = lambda j, g: SimpleNamespace(
        base_url=f'http://gpu{g}/v1', model_name=f'real-{g}', log_path=tmp_path / f'{g}.log',
        process=SimpleNamespace(poll=lambda: None))
    pool = SharedServerPool(tmp_path, [0, 1], backend=backend,
                            snapshot=lambda g: (100, 0, 100))
    seen = []
    def callback(url, log, monitor, alias):
        assert monitor.poll() is None
        with httpx.Client(trust_env=False, timeout=10) as client:
            assert client.get(url + '/models').json()['data'][0]['id'] == alias
            backend.acquire.assert_not_called()
            def respond(request):
                import json
                seen.append(json.loads(request.content)['model'])
                class Body(httpx.AsyncByteStream):
                    async def __aiter__(self):
                        yield b'{"choices":[{"message":{"content":"ok"}}]}'
                return httpx.Response(200, stream=Body(), headers={'content-type': 'application/json'})
            async def configure():
                pool.gateway.engine.transport_factory = lambda config: httpx.MockTransport(respond)
            pool.gateway._call(configure())
            for _ in range(4):
                response = client.post(url + '/chat/completions', json={'model': alias, 'messages': []})
                assert response.status_code == 200, response.text
            assert {call.args[1] for call in backend.acquire.call_args_list} == {0, 1}
            assert set(seen) == {'real-0', 'real-1'}
        return 0
    try:
        assert pool.run_client(job(tmp_path), callback) == 0
        pool.close_all(timeout=10)
        backend.close_all.assert_called_once()
        assert all(s['residency_holds'] == 0 for s in pool.snapshot_state()['slots'].values())
    finally:
        if pool.gateway.server:
            pool.gateway.server.should_exit = True
            pool.gateway.thread.join(timeout=10)
        pool._executor.shutdown()


@pytest.mark.parametrize('gpu_count', [1, 2])
def test_native_interleaved_incompatible_clients_no_503(tmp_path, gpu_count):
    import asyncio
    import httpx
    import threading
    events = []
    first_body = threading.Event()
    backend = Mock()
    backend.acquire.side_effect = lambda j, g: SimpleNamespace(
        base_url=f'http://gpu{g}/v1', model_name=j.metadata['ckpt_tag'],
        log_path=tmp_path / f'{g}.log', process=SimpleNamespace(poll=lambda: None))
    backend.release_gpu.side_effect = lambda *a: events.append('evicted')
    pool = SharedServerPool(tmp_path, range(gpu_count), backend=backend,
                            snapshot=lambda g: (100, 0, 100))
    one = pool.configured_job(job(tmp_path))
    two = pool.configured_job(job(tmp_path, ckpt_tag='step_2'))
    try:
        url1 = pool.gateway.register_job('one', one)
        url2 = pool.gateway.register_job('two', two)
        class Body(httpx.AsyncByteStream):
            async def __aiter__(self):
                first_body.set()
                await asyncio.sleep(.05)
                events.append('body_complete')
                yield b'{"choices":[]}'
        async def configure():
            pool.gateway.engine.transport_factory = lambda config: httpx.MockTransport(
                lambda request: httpx.Response(200, stream=Body()))
        pool.gateway._call(configure())
        def request(url, alias):
            with httpx.Client(trust_env=False, timeout=10) as client:
                response = client.post(url + '/chat/completions', json={'model': alias, 'messages': []})
                assert response.status_code == 200, response.text
        with ThreadPoolExecutor(max_workers=2) as workers:
            first = workers.submit(request, url1, 'one')
            assert first_body.wait(5)
            second = workers.submit(request, url2, 'two')
            first.result(timeout=10); second.result(timeout=10)
        if gpu_count == 1:
            assert events.index('body_complete') < events.index('evicted')
        for _ in range(3):
            request(url1, 'one'); request(url2, 'two')
        pool.close_all(timeout=10)
        assert pool.gateway.thread.is_alive()  # Exclusive barrier is reusable.
        pool.reopen()
        request(url1, 'one')
        pool.shutdown(timeout=10)
        assert not pool.gateway.thread.is_alive()
    finally:
        if pool.gateway.server:
            pool.gateway.server.should_exit = True
            pool.gateway.thread.join(timeout=10)
        pool._executor.shutdown()


@pytest.mark.parametrize('hold_tail', [False, True])
def test_unregister_old_group_scales_survivor_to_all_eight(tmp_path, hold_tail):
    import asyncio
    import httpx
    import json
    import threading
    started, release = threading.Event(), threading.Event()
    workers = ThreadPoolExecutor(max_workers=1)
    backend = Mock()
    backend.acquire.side_effect = lambda j, g: SimpleNamespace(
        base_url=f'http://gpu{g}/v1', model_name=j.metadata['ckpt_tag'],
        log_path=tmp_path / f'{g}.log', process=SimpleNamespace(poll=lambda: None))
    pool = SharedServerPool(tmp_path, range(8), backend=backend, snapshot=lambda g: (100, 0, 100))
    try:
        a = pool.configured_job(job(tmp_path).with_updates(job_id='old-job'))
        b = pool.configured_job(job(tmp_path, ckpt_tag='step_2').with_updates(job_id='survivor-job'))
        url_a = pool.gateway.register_job('old', a)
        url_b = pool.gateway.register_job('survivor', b)
        class Body(httpx.AsyncByteStream):
            def __init__(self, hold=False):
                self.hold = hold
            async def __aiter__(self):
                if self.hold:
                    started.set()
                    while not release.is_set():
                        await asyncio.sleep(.01)
                yield b'{"choices":[]}'
        async def configure():
            pool.gateway.engine.transport_factory = lambda config: httpx.MockTransport(
                lambda request: httpx.Response(200, stream=Body(json.loads(request.content).get('hold', False))))
        pool.gateway._call(configure())
        with httpx.Client(trust_env=False, timeout=10) as client:
            assert client.post(url_a + '/chat/completions', json={'model': 'old'}).status_code == 200
            assert client.post(url_b + '/chat/completions', json={'model': 'survivor'}).status_code == 200
            # This test exercises expansion/draining with sustained demand;
            # demand sizing itself is tested independently above.
            pool.gateway._additional_replicas = lambda key: 8
            async def residency():
                return {key: {lease.gpu for lease in value} for key, value in pool.gateway.resident.items()}
            key_a = compatibility_key(a, 0); key_b = compatibility_key(b, 0)
            before = pool.gateway._call(residency())
            assert len(before[key_a]) == 7 and len(before[key_b]) == 1
            if hold_tail:
                def hold_request():
                    with httpx.Client(trust_env=False, timeout=10) as other:
                        return other.post(url_a + '/chat/completions', json={'model': 'old', 'hold': True})
                pending = workers.submit(hold_request)
                assert started.wait(5)
                snapshot = pool.snapshot_state()
                assert snapshot['totals']['active'] >= 1
                assert snapshot['totals']['clients'] == 2
                assert snapshot['totals']['job_ids'] == ['old-job', 'survivor-job']
                assert any('old-job' in slot['job_ids'] and slot['active'] >= 1
                           for slot in snapshot['slots'].values())
            pool.gateway.unregister_route('old')
            async def expanded(count=8):
                async with asyncio.timeout(5):
                    while len(pool.gateway.resident.get(key_b, [])) != count:
                        await asyncio.sleep(.01)
                return await residency()
            if hold_tail:
                middle = pool.gateway._call(expanded(7), 10)
                assert len(middle[key_a]) == 1 and not pending.done()
                release.set()
                assert pending.result(timeout=5).status_code == 200
            after = pool.gateway._call(expanded(), 10)
            assert after == {key_b: set(range(8))}
            assert not pool.gateway.rebalance_errors
            assert client.post(url_b + '/chat/completions', json={'model': 'survivor'}).status_code == 200
        pool.shutdown(timeout=10)
    finally:
        release.set()
        workers.shutdown(wait=True)
        if pool.gateway.server:
            pool.gateway.server.should_exit = True
            pool.gateway.thread.join(timeout=10)
        pool._executor.shutdown()


@pytest.mark.parametrize('confirmed_exit,new_job', [(True, False), (False, False), (True, True)])
def test_failed_http_drain_requires_owned_exit_then_can_restart(tmp_path, confirmed_exit, new_job):
    import httpx
    backend = Mock(); processes = []
    def start(j, g):
        process = SimpleNamespace(exited=False)
        process.poll = lambda: 0 if process.exited else None
        processes.append(process)
        return SimpleNamespace(base_url='http://backend/v1', model_name='actual',
                               log_path=tmp_path / 'server.log', process=process)
    backend.acquire.side_effect = start
    pool = SharedServerPool(tmp_path, [0], backend=backend, snapshot=lambda g: (100, 0, 100))
    def stop(gpu, reason):
        assert reason == 'shared_drained_failure_cleanup'
        assert all(not b.tickets and b.draining for b in pool.gateway.engine.backends.values())
        processes[-1].exited = confirmed_exit
    backend.release_gpu.side_effect = stop
    status = [500]
    try:
        url = pool.gateway.register_job('job', pool.configured_job(job(tmp_path)))
        class Body(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield b'{"result":"test"}'
        async def configure():
            pool.gateway.engine.transport_factory = lambda config: httpx.MockTransport(
                lambda request: httpx.Response(status[0], stream=Body()))
        pool.gateway._call(configure())
        with httpx.Client(trust_env=False, timeout=10) as client:
            assert client.post(url + '/chat/completions', json={'model': 'job'}).status_code == 500
            if not confirmed_exit:
                with pytest.raises(RuntimeError, match='termination was not confirmed'):
                    pool.close_all(timeout=5)
                backend.close_all.assert_not_called()
                assert pool.snapshot_state()['slots'][0]['residency_holds'] == 1
                return
            if new_job:
                pool.gateway.unregister_route('job')
                url = pool.gateway.register_job('retry', pool.configured_job(job(tmp_path)))
                backend.close_all.assert_not_called()
            else:
                pool.close_all(timeout=5)
                pool.reopen()
            assert processes[0].exited
            backend.release_gpu.assert_called_once()
            status[0] = 200
            assert client.post(url + '/chat/completions', json={'model': 'retry' if new_job else 'job'}).status_code == 200
            assert len(processes) == 2
        pool.shutdown(timeout=5)
    finally:
        if pool.gateway.server:
            pool.gateway.server.should_exit = True
            pool.gateway.thread.join(timeout=10)
        pool._executor.shutdown()
def test_busy_gateway_health_poll_is_not_a_confirmed_failure():
    from unittest.mock import Mock
    from eval_scheduler.shared_pool import NativeGatewayHost
    host = NativeGatewayHost(None)
    host.thread = Mock()
    host.thread.is_alive.return_value = True
    def busy(coroutine, timeout):
        coroutine.close()
        raise TimeoutError('event loop busy')
    host._call = busy
    assert host.client_failed('client') is False


def test_shared_client_log_allows_request_retries(tmp_path):
    from eval_scheduler.runtime import contains_client_fatal
    log = tmp_path/'client.log'
    for transient in ('APIConnectionError', 'APITimeoutError', 'ServerDisconnectedError'):
        log.write_text(transient+' retrying request')
        assert not contains_client_fatal([log], shared_client=True)
        assert contains_client_fatal([log])
    for permanent in ('BadRequestError', 'Task interrupted'):
        log.write_text(permanent)
        assert contains_client_fatal([log], shared_client=True)


def test_transport_error_does_not_fail_or_evict_other_clients(tmp_path):
    import httpx
    backend = Mock()
    process = SimpleNamespace(exited=False)
    process.poll = lambda: 1 if process.exited else None
    backend.acquire.return_value = SimpleNamespace(
        base_url='http://backend/v1', model_name='actual',
        log_path=tmp_path / 'server.log', process=process)
    pool = SharedServerPool(tmp_path, [0], backend=backend, snapshot=lambda g: (100, 0, 100))
    try:
        configured = pool.configured_job(job(tmp_path))
        first = pool.gateway.register_job('first', configured)
        failed = [False]
        class Body(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield b'{"choices": []}'
        def response(request):
            if not failed[0]:
                failed[0] = True
                raise httpx.ReadError('transient disconnect')
            return httpx.Response(200, stream=Body())
        async def configure():
            pool.gateway.engine.transport_factory = lambda config: httpx.MockTransport(response)
        pool.gateway._call(configure())
        with httpx.Client(trust_env=False, timeout=10) as client:
            assert client.post(first + '/chat/completions', json={'model': 'first'}).status_code == 502
            assert not pool.gateway.client_failed('first')
            assert client.post(first + '/chat/completions', json={'model': 'first'}).status_code == 200
            second = pool.gateway.register_job('second', configured)
            backend.release_gpu.assert_not_called()
            assert client.post(second + '/chat/completions', json={'model': 'second'}).status_code == 200
            assert not pool.gateway.client_failed('second')
            assert backend.acquire.call_count == 1
            process.exited = True
            assert pool.gateway.client_failed('first')
            assert pool.gateway.client_failed('second')
        pool.shutdown(timeout=5)
    finally:
        if pool.gateway.server:
            pool.gateway.server.should_exit = True
            pool.gateway.thread.join(timeout=10)
        pool._executor.shutdown()
