"""CPU-only gateway tests; listening sockets are ephemeral loopback only."""
import asyncio
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from eval_scheduler.gateway import (
    AdmissionError, Backend, ClientRoute, Gateway, GatewayService, _ForwardedResponse, create_app,
)


class Bytes(httpx.AsyncByteStream):
    def __init__(self, content=b'ok'):
        self.content = content
        self.closed = False

    async def __aiter__(self):
        yield self.content

    async def aclose(self):
        self.closed = True


def response(content=b'ok', status=200, headers=None):
    return httpx.Response(status, stream=Bytes(content), headers=headers)


def run(coro):
    return asyncio.run(coro)


def test_shared_server_loop_rejects_early_exit():
    from eval_scheduler.gateway import serve_gateway

    class Server:
        started = False

        async def serve(self, sockets):
            return

    ready = threading.Event()
    with pytest.raises(RuntimeError, match='exited during startup'):
        run(serve_gateway(Server(), object(), ready))
    assert not ready.is_set()


def test_shared_server_loop_cancellation_drains_child():
    from eval_scheduler.gateway import serve_gateway

    async def scenario():
        stopped = asyncio.Event()

        class Server:
            started = False

            async def serve(self, sockets):
                self.started = True
                try:
                    await asyncio.Event().wait()
                finally:
                    stopped.set()

        ready = asyncio.Event()
        task = asyncio.create_task(serve_gateway(Server(), object(), ready))
        await asyncio.wait_for(ready.wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert stopped.is_set()

    run(scenario())


def test_simulation_preserves_load_receipt_on_probe_failure(monkeypatch):
    from eval_scheduler import gateway_simulation as simulation
    original = simulation.payload
    monkeypatch.setattr(simulation, 'payload', lambda index: original(-2 if index == -1 else index))
    receipt = {}
    with pytest.raises(RuntimeError, match='probe ended before upstream'):
        run(simulation.simulate(8, receipt))
    assert receipt['load_passed'] is True
    assert receipt['concurrent_admitted'] == 8
    assert receipt['payload_mismatches'] == []
    assert len(receipt['requests_per_backend']) == 8
    assert receipt['pending_client_tasks_after_cleanup'] == 0
    assert receipt['probe_transport_events']


def test_simulation_small_real_http_success(caplog):
    from eval_scheduler.gateway_simulation import simulate
    receipt = run(simulate(16))
    assert receipt['passed'] and receipt['load_passed']
    assert receipt['pending_client_tasks_after_cleanup'] == 0
    assert receipt['probe_upstream_entered_seconds'] < 10
    assert not [record for record in caplog.records if record.name == 'uvicorn.error'
                and record.levelno >= 40]


def test_temporary_last_backend_eviction_waits_for_reprovision():
    async def check():
        allow = asyncio.Event()
        entered = asyncio.Event()
        calls = 0

        async def provision(key):
            nonlocal calls
            calls += 1
            if calls > 1:
                entered.set()
                await allow.wait()
            return [Backend('replica', 'http://backend', key)]

        g = Gateway(client_routes=[ClientRoute('job', 'key', 'alias')],
                    provision_backend=provision)
        await g.start()
        try:
            await g.ensure_backend('key')
            # Host holds its placement lock across drain/remove/reassignment.
            g.backends['replica'].draining = True
            await g.reset_provisioning('key')
            pending = asyncio.create_task(g.ensure_backend('key'))
            await entered.wait()
            assert not pending.done()
            assert g.provision_waiters['key'] == 1
            assert 'key' not in g.disabled_keys
            await g.drain_backend('replica')
            await g.remove_backend('replica')
            allow.set()
            await pending
            ticket = g.reserve('key', 'job')
            await g.wait_turn(ticket)
            g.release(ticket)
            assert calls == 2
            # Explicit shutdown remains a hard fence, not a residency swap.
            await g.drain_key('key')
            with pytest.raises(AdmissionError) as error:
                await g.ensure_backend('key')
            assert error.value.status == 503
        finally:
            allow.set()
            await g.aclose()
    run(check())


def test_service_real_loopback_lazy_alias_metrics_and_drain():
    """Real frontend TCP requests with a controlled, CPU-only upstream."""
    release = threading.Event()
    calls = []
    provisions = []

    async def handler(request):
        calls.append(json.loads(request.content))
        while not release.is_set():
            await asyncio.sleep(.005)
        return response(b'{"choices":[]}', headers={'content-type': 'application/json'})

    async def provision(key):
        provisions.append(key)
        return [Backend('mock', 'http://mock/v1', key, model_name='actual-model')]

    service = GatewayService(provision_backend=provision,
                             transport_factory=lambda _: httpx.MockTransport(handler)).start()
    try:
        assert service.poll() is None
        first = service.register_route('job-a', compatibility_key='key', model_alias='alias')
        second = service.register_route('job-b', compatibility_key='key', model_alias='alias')
        assert service.register_route('job-a', compatibility_key='key', model_alias='alias') == first
        with pytest.raises(ValueError):
            service.register_route('job-a', compatibility_key='other')
        with httpx.Client(trust_env=False, timeout=5) as client:
            assert client.get(first+'/models').json()['data'][0]['id'] == 'alias'
            assert client.get(first+'/health').json()['provisioned'] is False
        assert provisions == []

        def post(url):
            with httpx.Client(trust_env=False, timeout=5) as client:
                return client.post(url+'/chat/completions', json={'model': 'alias', 'messages': []})

        with ThreadPoolExecutor(max_workers=2) as workers:
            futures = [workers.submit(post, url) for url in (first, second)]
            deadline = time.monotonic()+5
            while service.snapshot()['active'] != 2 and time.monotonic() < deadline:
                time.sleep(.01)
            snapshot = service.snapshot()
            assert snapshot['active'] == 2
            assert snapshot['backends']['mock']['active_clients'] == {'job-a': 1, 'job-b': 1}
            assert provisions == ['key']
            assert all(c['model'] == 'actual-model' for c in calls)
            try:
                with pytest.raises(TimeoutError):
                    service.close(timeout=.03)
                assert service.poll() is None
            finally:
                release.set()
            assert all(f.result(timeout=5).status_code == 200 for f in futures)
        service.close(timeout=5)
        assert service.poll() == 0
    finally:
        release.set()
        service.close(timeout=5)


def test_defaults_and_no_hidden_low_concurrency():
    async def check():
        b = Backend('a', 'http://backend', 'key')
        assert b.max_num_seqs == 1024 and b.queue_limit == 2048
        g = Gateway([b]); await g.start()
        tickets = [g.reserve('key', 'client') for _ in range(129)]
        for t in tickets:
            await g.wait_turn(t)
        assert g.metrics()['a']['active'] == 129
        for t in tickets:
            g.release(t)
        await g.aclose()
    run(check())


def test_compatibility_least_loaded_and_queue_limits():
    async def check():
        g = Gateway([Backend('a', 'http://a', 'key', max_num_seqs=1, queue_capacity=1),
                     Backend('b', 'http://b', 'key', max_num_seqs=1, queue_capacity=1),
                     Backend('other', 'http://other', 'different')])
        await g.start()
        tickets = [g.reserve('key', 'c') for _ in range(4)]
        assert {t.backend.config.id for t in tickets[:2]} == {'a', 'b'}
        assert g.metrics()['other']['queued'] == 0
        with pytest.raises(AdmissionError) as e:
            g.reserve('key', 'overflow')
        assert e.value.status == 429
        with pytest.raises(AdmissionError) as e:
            g.reserve('unregistered', 'c')
        assert e.value.status == 503
        for t in tickets:
            g.release(t)
        await g.aclose()
    run(check())


def test_client_round_robin_and_queued_cancellation():
    async def check():
        g = Gateway([Backend('a', 'http://a', 'key', max_num_seqs=1)])
        await g.start()
        first = g.reserve('key', 'busy'); await g.wait_turn(first)
        a = g.reserve('key', 'a'); a.ready = True
        b = g.reserve('key', 'b'); b.ready = True
        g.release(first)
        assert a.active and not b.active
        a2 = g.reserve('key', 'a'); a2.ready = True
        g.release(a)
        assert b.active and not a2.active
        waiter = asyncio.create_task(g.wait_turn(a2))
        await asyncio.sleep(0)
        waiter.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiter
        assert a2.released and g.metrics()['a']['queued'] == 0
        g.release(b); await g.aclose()
    run(check())


def test_drain_fences_admissions_and_waits_existing_queue():
    async def check():
        g = Gateway([Backend('a', 'http://a', 'key', max_num_seqs=1)])
        await g.start()
        a = g.reserve('key', 'a'); await g.wait_turn(a)
        b = g.reserve('key', 'b'); b.ready = True
        draining = asyncio.create_task(g.drain_backend('a'))
        await asyncio.sleep(0)
        with pytest.raises(AdmissionError):
            g.reserve('key', 'c')
        with pytest.raises(RuntimeError):
            await g.remove_backend('a')
        g.release(a)
        assert b.active and not draining.done()
        g.release(b); await draining
        await g.remove_backend('a')
        assert not g.backends
        await g.aclose()
    run(check())


def test_forwarding_body_headers_paths_stream_and_failure_no_replay():
    async def check():
        calls = []
        async def handler(req):
            calls.append(req)
            if req.url.path.endswith('/completions'):
                return response(b'data: {"token":"x"}\n\ndata: [DONE]\n\n', headers={'content-type': 'text/event-stream'})
            return response(b'{"error":"busy"}', status=503)
        g = Gateway([Backend('a', 'http://a/v1', 'key')], transport_factory=lambda _: httpx.MockTransport(handler))
        app = create_app(gateway=g)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://gateway') as client:
                headers = {'x-gateway-compatibility-key': 'key', 'x-gateway-client-id': 'task',
                           'connection': 'x-remove', 'x-remove': 'private'}
                body = b'{"model":"m","stream":true,"tools":[]}'
                res = await client.post('/v1/chat/completions', content=body, headers=headers)
                assert res.status_code == 200 and res.content.endswith(b'data: [DONE]\n\n')
                assert calls[0].url.path == '/v1/chat/completions'
                assert calls[0].content == body
                assert 'x-remove' not in calls[0].headers and 'x-gateway-client-id' not in calls[0].headers
                failure = await client.get('/v1/models', headers=headers)
                assert failure.status_code == 503 and len(calls) == 2
                assert g.metrics()['a']['active'] == 0
                assert g.metrics()['a']['failures'] == 1
    run(check())


def test_transport_error_surfaced_once():
    async def check():
        calls = []
        def handler(req):
            calls.append(req)
            raise httpx.ConnectError('offline')
        app = create_app([Backend('a', 'http://a', 'key')], default_compatibility_key='key',
                         transport_factory=lambda _: httpx.MockTransport(handler))
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://gateway') as c:
                res = await c.post('/v1/completions', json={'model': 'm'})
                assert res.status_code == 502 and len(calls) == 1
                assert app.state.gateway.metrics()['a']['active'] == 0
    run(check())


def test_request_and_backend_byte_limits_cleanup():
    async def check():
        g = Gateway([Backend('a', 'http://a', 'key', max_buffered_bytes=10)], max_request_bytes=8)
        await g.start()
        a = g.reserve('key', 'a'); g.account_bytes(a, 6)
        b = g.reserve('key', 'b')
        with pytest.raises(AdmissionError) as e:
            g.account_bytes(b, 5)
        assert e.value.status == 429
        with pytest.raises(AdmissionError) as e:
            g.account_bytes(a, 3)
        assert e.value.status == 413
        g.release(a); g.release(b)
        assert g.metrics()['a']['buffered_bytes'] == 0
        await g.aclose()
    run(check())


def test_lazy_routes_singleflight_no_health_provision_and_model_alias():
    async def check():
        provisions, requests = [], []
        async def provision(key):
            provisions.append(key)
            await asyncio.sleep(.01)
            return [Backend('a', 'http://a', key, model_name='actual-model')]
        def handler(req):
            requests.append(req)
            return response(b'{"choices":[]}')
        app = create_app(client_routes=[ClientRoute('job1', 'key', 'alias'), ClientRoute('job2', 'key', 'alias')],
                         provision_backend=provision, transport_factory=lambda _: httpx.MockTransport(handler))
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://gateway') as c:
                assert (await c.get('/job1/health')).status_code == 200
                assert (await c.get('/job1/v1/models')).json()['data'][0]['id'] == 'alias'
                assert not provisions
                results = await asyncio.gather(*(c.post('/'+job+'/v1/chat/completions',
                    json={'model': 'alias', 'messages': [], 'tools': [], 'temperature': .2}) for job in ['job1', 'job2']))
                assert [r.status_code for r in results] == [200, 200]
                assert provisions == ['key'] and len(requests) == 2
                for req in requests:
                    assert json.loads(req.content) == dict(model='actual-model', messages=[], tools=[], temperature=.2)
                assert (await c.get('/unknown/v1/models')).status_code == 404
                await app.state.gateway.drain_key('key')
                assert (await c.post('/job1/v1/completions', json={'model': 'alias'})).status_code == 503
                assert len(provisions) == 1
    run(check())


def test_provision_failure_is_cached_not_replayed():
    async def check():
        calls = []
        async def provision(key):
            calls.append(key)
            raise RuntimeError('unavailable')
        app = create_app(client_routes=[ClientRoute('job', 'key', 'alias')], provision_backend=provision)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://gateway') as c:
                for _ in range(2):
                    assert (await c.post('/job/v1/completions', json={'model': 'alias'})).status_code == 503
                assert calls == ['key']
    run(check())


def test_cancel_before_backend_headers_retains_admission_until_completion():
    async def check():
        entered, finish = asyncio.Event(), asyncio.Event()
        async def handler(req):
            entered.set(); await finish.wait()
            return response()
        app = create_app([Backend('a', 'http://a', 'key', max_num_seqs=1)],
                         default_compatibility_key='key', transport_factory=lambda _: httpx.MockTransport(handler))
        async with app.router.lifespan_context(app):
            g = app.state.gateway
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://gateway') as c:
                req = asyncio.create_task(c.post('/v1/completions', json={'model': 'm'}))
                await entered.wait(); req.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await req
                assert g.metrics()['a']['active'] == 1
                draining = asyncio.create_task(g.drain_backend('a'))
                await asyncio.sleep(0); assert not draining.done()
                finish.set(); await asyncio.wait_for(draining, 1)
                assert g.metrics()['a']['active'] == 0
    run(check())


def test_stream_disconnect_drains_upstream_before_releasing():
    async def check():
        finish = asyncio.Event()
        class Slow(Bytes):
            async def __aiter__(self):
                yield b'first'
                await finish.wait()
                yield b'last'
        g = Gateway([Backend('a', 'http://a', 'key')]); await g.start()
        t = g.reserve('key', 'client'); await g.wait_turn(t)
        stream = Slow()
        upstream = httpx.Response(200, stream=stream)
        forwarded = _ForwardedResponse(upstream, g, t)
        async def send(message):
            if message['type'] == 'http.response.body':
                raise OSError('frontend disconnected')
        async def receive():
            await asyncio.Event().wait()
        from starlette.requests import ClientDisconnect
        with pytest.raises(ClientDisconnect):
            await forwarded({'type': 'http', 'asgi': {'spec_version': '2.4'}}, receive, send)
        assert g.metrics()['a']['active'] == 1
        finish.set()
        await asyncio.wait_for(g.backends['a'].idle.wait(), 1)
        assert stream.closed and g.metrics()['a']['active'] == 0
        await g.aclose()
    run(check())


def test_drain_timeout_keeps_backend_fenced():
    async def check():
        g = Gateway([Backend('a', 'http://a', 'key')]); await g.start()
        t = g.reserve('key', 'client'); await g.wait_turn(t)
        with pytest.raises(TimeoutError):
            await g.drain_backend('a', timeout=.001)
        assert g.metrics()['a']['draining'] and g.metrics()['a']['active'] == 1
        with pytest.raises(AdmissionError):
            g.reserve('key', 'new')
        g.release(t); await g.remove_backend('a'); await g.aclose()
    run(check())


@pytest.mark.parametrize('concurrent_cancel', [False, True])
def test_real_asgi_disconnect_removes_queued_request_without_forwarding(concurrent_cancel):
    async def check():
        calls = []
        g = Gateway([Backend('a', 'http://a', 'key', max_num_seqs=1)],
                    transport_factory=lambda _: httpx.MockTransport(lambda r: calls.append(r) or response()))
        app = create_app(gateway=g, default_compatibility_key='key')
        async with app.router.lifespan_context(app):
            holder = g.reserve('key', 'holder'); await g.wait_turn(holder)
            disconnect = asyncio.Event()
            sent = []
            sent_body = False
            async def receive():
                nonlocal sent_body
                if not sent_body:
                    sent_body = True
                    return {'type': 'http.request', 'body': b'{}', 'more_body': False}
                await disconnect.wait()
                if concurrent_cancel:
                    task.cancel('external shutdown')
                return {'type': 'http.disconnect'}
            async def send(message):
                sent.append(message)
            scope = dict(type='http', asgi={'version': '3.0'}, method='POST',
                         scheme='http', path='/v1/completions', raw_path=b'/v1/completions',
                         query_string=b'', headers=[], server=('localhost', 1), client=('localhost', 2))
            task = asyncio.create_task(app(scope, receive, send))
            for _ in range(100):
                if g.metrics()['a']['queued']:
                    break
                await asyncio.sleep(0)
            assert g.metrics()['a']['queued'] == 1
            disconnect.set()
            if concurrent_cancel:
                with pytest.raises(asyncio.CancelledError):
                    await asyncio.wait_for(task, 1)
                assert not sent
            else:
                await asyncio.wait_for(task, 1)
                assert sent[0]['status'] == 499
            assert g.metrics()['a']['queued'] == 0 and not calls
            g.release(holder)
    run(check())


def test_shutdown_cleans_detached_stream_and_pending_read():
    async def check():
        entered = asyncio.Event()
        class Never(Bytes):
            async def __aiter__(self):
                entered.set()
                await asyncio.Event().wait()
                yield b'never'
        g = Gateway([Backend('a', 'http://a', 'key')]); await g.start()
        t = g.reserve('key', 'client'); await g.wait_turn(t)
        stream = Never(); forwarded = _ForwardedResponse(httpx.Response(200, stream=stream), g, t)
        reader = asyncio.create_task(anext(forwarded.chunks()))
        await entered.wait(); reader.cancel()
        with pytest.raises(asyncio.CancelledError):
            await reader
        g.cleanup(t, forwarded.finish())
        await asyncio.sleep(0)
        await asyncio.wait_for(g.aclose(), 1)
        assert stream.closed and t.released and not g.cleanup_tasks
        assert forwarded.pending.done()
    run(check())
