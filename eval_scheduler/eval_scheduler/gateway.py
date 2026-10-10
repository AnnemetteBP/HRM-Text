"""Node-local, loop-owned OpenAI forwarding without replay or server ownership.

Embed ``create_app`` in uvicorn (including ``Server.serve(sockets=[socket])``).
Use X-Gateway-Compatibility-Key and X-Gateway-Client-ID on requests, or explicitly
bind a default compatibility key when constructing the app. Registration, drain
and removal must run on the ASGI event loop; from another thread use
asyncio.run_coroutine_threadsafe. No method unloads or signals a backend server.
"""
from __future__ import annotations

import asyncio
import json
import re
import socket
import threading
import time
from collections import Counter, OrderedDict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Callable

import httpx
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse, StreamingResponse


@dataclass(frozen=True)
class Backend:
    id: str
    base_url: str
    compatibility_key: str
    max_num_seqs: int = 1024
    queue_capacity: int | None = None
    max_buffered_bytes: int = 1024**3
    headers: dict[str, str] = field(default_factory=dict)
    model_name: str | None = None
    role: str = 'target'

    def __post_init__(self):
        if not self.id or not self.compatibility_key:
            raise ValueError("Backend ID and explicit compatibility key required")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("HTTP(S) backend base URL required")
        if self.max_num_seqs < 1 or self.max_buffered_bytes < 1:
            raise ValueError("Positive capacity and byte budget required")
        if self.queue_capacity is not None and self.queue_capacity < 0:
            raise ValueError("Queue capacity must be nonnegative")

    @property
    def queue_limit(self):
        return 2 * self.max_num_seqs if self.queue_capacity is None else self.queue_capacity


@dataclass(frozen=True)
class ClientRoute:
    client_id: str
    compatibility_key: str
    model_alias: str
    role: str = 'target'

    def __post_init__(self):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', self.client_id) or self.client_id in ('v1', 'health', 'metrics'):
            raise ValueError('Safe unique client path segment required')
        if not self.compatibility_key or not self.model_alias:
            raise ValueError('Explicit compatibility key and public model alias required')


class AdmissionError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


@dataclass(eq=False)
class _Ticket:
    backend: _State
    client: str
    future: asyncio.Future
    owner: asyncio.Task
    ready: bool = False
    active: bool = False
    released: bool = False
    size: int = 0


class _State:
    def __init__(self, config: Backend, client: httpx.AsyncClient):
        self.config = config
        self.client = client
        self.queues: OrderedDict[str, deque[_Ticket]] = OrderedDict()
        self.tickets: set[_Ticket] = set()
        self.active = 0
        self.buffered_bytes = 0
        self.draining = False
        self.idle = asyncio.Event()
        self.idle.set()
        self.completed = 0
        self.failures = 0
        self.last_error = None

    @property
    def queued(self):
        return len(self.tickets) - self.active


HOP_HEADERS = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
               "te", "trailer", "transfer-encoding", "upgrade", "host"}


def _headers(headers):
    excluded = HOP_HEADERS | {s.strip().lower() for s in headers.get("connection", "").split(",")}
    return {k: v for k, v in headers.items()
            if k.lower() not in excluded and not k.lower().startswith("x-gateway-")}


class Gateway:
    """One instance per ASGI loop. Counters and queues never use SQLite or threads."""

    def __init__(self, backends=(), *, max_request_bytes: int = 64 * 1024**2,
                 timeout: float = 600, transport_factory: Callable | None = None,
                 client_routes=(), provision_backend: Callable | None = None,
                 provision_queue_capacity: int = 3072):
        if max_request_bytes < 1 or timeout <= 0:
            raise ValueError("Positive request byte limit and timeout required")
        configs = list(backends)
        if len({b.id for b in configs}) != len(configs):
            raise ValueError("Duplicate backend ID")
        self.configs = configs
        routes = list(client_routes)
        if len({r.client_id for r in routes}) != len(routes) or provision_queue_capacity < 1:
            raise ValueError('Duplicate client ID or invalid provisioning queue capacity')
        self.routes = {r.client_id: r for r in routes}
        self.provision_backend = provision_backend
        self.provision_queue_capacity = provision_queue_capacity
        self.provisioning: dict[str, asyncio.Task] = {}
        self.provision_waiters: dict[str, int] = {}
        self.disabled_keys: set[str] = set()
        self.cleanup_tasks: set[asyncio.Task] = set()
        self.max_request_bytes = max_request_bytes
        self.timeout = timeout
        self.transport_factory = transport_factory
        self.backends: dict[str, _State] = {}
        self.loop = None
        self.closing = False
        self._tie = 0

    def _check_loop(self):
        if self.loop is not asyncio.get_running_loop():
            raise RuntimeError("Gateway operation must run on its ASGI event loop")

    async def start(self):
        if self.loop is not None:
            self._check_loop()
            if self.closing:
                raise RuntimeError("Closed gateway cannot restart")
            return
        self.loop = asyncio.get_running_loop()
        for config in self.configs:
            await self.register_backend(config)

    async def register_backend(self, config: Backend):
        self._check_loop()
        if self.closing or config.id in self.backends:
            raise ValueError("Gateway closed or duplicate backend ID")
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout, connect=min(10, self.timeout)),
            limits=httpx.Limits(max_connections=config.max_num_seqs,
                               max_keepalive_connections=config.max_num_seqs),
            transport=self.transport_factory(config) if self.transport_factory else None,
            follow_redirects=False, trust_env=False,
        )
        self.backends[config.id] = _State(config, client)

    async def register_client(self, route: ClientRoute):
        self._check_loop()
        if self.closing or route.client_id in self.routes:
            raise ValueError('Closed gateway or duplicate client route')
        self.routes[route.client_id] = route

    async def _provision(self, key):
        configs = list(await self.provision_backend(key))
        if not configs or any(c.compatibility_key != key for c in configs):
            raise ValueError('Provisioner returned no matching backend')
        if len({c.id for c in configs}) != len(configs):
            raise ValueError('Provisioner returned duplicate backend IDs')
        for config in configs:
            if config.id in self.backends and self.backends[config.id].config != config:
                raise ValueError('Provisioner attempted to replace an existing backend')
        for config in configs:
            if config.id not in self.backends:
                await self.register_backend(config)

    async def ensure_backend(self, key):
        self._check_loop()
        if self.closing or key in self.disabled_keys:
            raise AdmissionError(503, 'Compatibility key is draining')
        if any(b.config.compatibility_key == key and not b.draining for b in self.backends.values()):
            return
        if self.provision_backend is None or key not in {r.compatibility_key for r in self.routes.values()}:
            raise AdmissionError(503, 'No registered provisioner for compatibility key')
        count = self.provision_waiters.get(key, 0)
        if count >= self.provision_queue_capacity:
            raise AdmissionError(429, 'Provisioning wait queue exhausted')
        self.provision_waiters[key] = count + 1
        try:
            if key not in self.provisioning:
                self.provisioning[key] = asyncio.create_task(self._provision(key))
                # Retrieve background exceptions even if every waiter disconnects.
                self.provisioning[key].add_done_callback(lambda t: None if t.cancelled() else t.exception())
            await asyncio.shield(self.provisioning[key])
        except Exception as exc:
            raise AdmissionError(503, 'Backend provisioning failed: '+type(exc).__name__) from exc
        finally:
            self.provision_waiters[key] -= 1

    async def reset_provisioning(self, key):
        """Explicit operator retry only; failed provisioning is never blindly replayed."""
        self._check_loop()
        task = self.provisioning.get(key)
        if task and not task.done():
            raise RuntimeError('Provisioning is still running')
        self.provisioning.pop(key, None)
        self.disabled_keys.discard(key)

    def reserve(self, compatibility_key: str, client: str, role: str = 'target') -> _Ticket:
        self._check_loop()
        compatible = [b for b in self.backends.values()
                      if b.config.compatibility_key == compatibility_key
                      and b.config.role == role and not b.draining]
        if self.closing or compatibility_key in self.disabled_keys or not compatible:
            raise AdmissionError(503, "No admitting backend with the requested compatibility key")
        available = [b for b in compatible
                     if len(b.tickets) < b.config.max_num_seqs + b.config.queue_limit
                     and b.buffered_bytes < b.config.max_buffered_bytes]
        if not available:
            raise AdmissionError(429, "Compatible backend request or byte capacity exhausted")
        # Round-robin exact ties; otherwise prefer normalized least load.
        self._tie += 1
        available = available[self._tie % len(available):] + available[:self._tie % len(available)]
        backend = min(available, key=lambda b: len(b.tickets)/b.config.max_num_seqs)
        ticket = _Ticket(backend, client, self.loop.create_future(), asyncio.current_task())
        backend.tickets.add(ticket)
        backend.idle.clear()
        backend.queues.setdefault(client, deque()).append(ticket)
        return ticket

    def account_bytes(self, ticket: _Ticket, count: int):
        self._check_loop()
        if count < 0:
            raise ValueError('Byte accounting increments must be nonnegative')
        if ticket.released:
            raise RuntimeError("Released ticket")
        backend = ticket.backend
        if ticket.size + count > self.max_request_bytes:
            raise AdmissionError(413, "Request body exceeds gateway byte limit")
        if backend.buffered_bytes + count > backend.config.max_buffered_bytes:
            raise AdmissionError(429, "Backend buffered request byte capacity exhausted")
        ticket.size += count
        backend.buffered_bytes += count

    def _dispatch(self, backend: _State):
        if self.closing:
            return
        while backend.active < backend.config.max_num_seqs and backend.queues:
            chosen = None
            for client, queue in list(backend.queues.items()):
                # Body uploads count against capacity, but never head-of-line block
                # another ready request while its client is still uploading.
                chosen = next((t for t in queue if t.ready), None)
                if chosen is not None:
                    queue.remove(chosen)
                    if queue:
                        backend.queues.move_to_end(client)
                    else:
                        del backend.queues[client]
                    break
            if chosen is None:
                return
            backend.active += 1
            chosen.active = True
            chosen.future.set_result(None)

    async def wait_turn(self, ticket: _Ticket):
        self._check_loop()
        ticket.ready = True
        self._dispatch(ticket.backend)
        try:
            await asyncio.shield(ticket.future)
        except BaseException:
            self.release(ticket)
            raise

    def release(self, ticket: _Ticket):
        self._check_loop()
        if ticket.released:
            return
        ticket.released = True
        backend = ticket.backend
        if ticket.active:
            backend.active -= 1
            backend.completed += 1
        else:
            queue = backend.queues[ticket.client]
            queue.remove(ticket)
            if not queue:
                del backend.queues[ticket.client]
        backend.buffered_bytes -= ticket.size
        backend.tickets.remove(ticket)
        if not ticket.future.done():
            ticket.future.cancel()
        self._dispatch(backend)
        if not backend.tickets:
            backend.idle.set()

    async def drain_backend(self, backend_id: str, timeout: float | None = None):
        """Reject new admissions; finish existing queued/active work. No unload."""
        self._check_loop()
        backend = self.backends[backend_id]
        backend.draining = True
        await asyncio.wait_for(backend.idle.wait(), timeout)

    async def drain_key(self, key: str, timeout: float | None = None):
        """Fence lazy provisioning and drain every backend for a compatibility key."""
        self._check_loop()
        self.disabled_keys.add(key)
        async def drain():
            task = self.provisioning.get(key)
            if task:
                try:
                    await asyncio.shield(task)
                except Exception:
                    pass  # Failed provisioning must not prevent draining registered endpoints.
            await asyncio.gather(*(self.drain_backend(name) for name, b in self.backends.items()
                                   if b.config.compatibility_key == key))
        await asyncio.wait_for(drain(), timeout)

    def cleanup(self, ticket, coroutine):
        task = asyncio.create_task(coroutine)
        ticket.owner = task
        self.cleanup_tasks.add(task)
        def done(completed):
            self.cleanup_tasks.discard(completed)
            if not completed.cancelled():
                completed.exception()
        task.add_done_callback(done)

    async def finish_response(self, ticket, response_task):
        response = None
        try:
            response = await response_task
            async for _ in response.aiter_raw():
                pass
        except (Exception, asyncio.CancelledError) as exc:
            ticket.backend.failures += 1
            ticket.backend.last_error = 'finish_response:' + type(exc).__name__
        finally:
            try:
                if response is not None:
                    await response.aclose()
            finally:
                self.release(ticket)

    async def remove_backend(self, backend_id: str):
        self._check_loop()
        backend = self.backends[backend_id]
        if not backend.draining or backend.tickets:
            raise RuntimeError("Backend must drain before removal/unload")
        await backend.client.aclose()
        del self.backends[backend_id]

    def metrics(self):
        self._check_loop()
        return {name: dict(compatibility_key=b.config.compatibility_key,
                          active=b.active, queued=b.queued, buffered_bytes=b.buffered_bytes,
                          draining=b.draining, max_num_seqs=b.config.max_num_seqs,
                          queue_capacity=b.config.queue_limit, completed=b.completed,
                          failures=b.failures, last_error=b.last_error,
                          active_clients=dict(Counter(t.client for t in b.tickets if t.active)),
                          queued_clients={c: len(q) for c, q in b.queues.items()},
                          clients={c: len(q) for c, q in b.queues.items()})
                for name, b in self.backends.items()}

    def snapshot(self):
        backends = self.metrics()
        return dict(backends=backends, active=sum(b['active'] for b in backends.values()),
                    queued=sum(b['queued'] for b in backends.values()),
                    provisioning_queued=dict(self.provision_waiters), closing=self.closing)

    async def aclose(self):
        self._check_loop()
        self.closing = True
        for task in self.provisioning.values():
            if not task.done():
                task.cancel()
        if self.provisioning:
            await asyncio.gather(*self.provisioning.values(), return_exceptions=True)
        owners = {t.owner for b in self.backends.values() for t in b.tickets
                  if t.owner is not asyncio.current_task()}
        for owner in owners:
            owner.cancel()
        if owners:
            await asyncio.gather(*owners, return_exceptions=True)
        # Cancel cleanup tasks created by frontend cancellation finalizers above.
        cleanup = list(self.cleanup_tasks)
        for task in cleanup:
            task.cancel()
        if cleanup:
            await asyncio.gather(*cleanup, return_exceptions=True)
        for backend in self.backends.values():
            for ticket in list(backend.tickets):
                self.release(ticket)
            await backend.client.aclose()


class _ForwardedResponse(StreamingResponse):
    def __init__(self, upstream, gateway, ticket):
        self.upstream = upstream
        self.gateway = gateway
        self.ticket = ticket
        self.iterator = upstream.aiter_raw().__aiter__()
        self.pending = None
        self.ended = False
        super().__init__(self.chunks(), status_code=upstream.status_code,
                         headers=_headers(upstream.headers))

    async def chunks(self):
        while True:
            self.pending = asyncio.create_task(anext(self.iterator))
            try:
                chunk = await asyncio.shield(self.pending)
            except StopAsyncIteration:
                self.ended = True
                self.pending = None
                return
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.ended = True
                self.ticket.backend.failures += 1
                self.ticket.backend.last_error = 'chunks:' + type(exc).__name__
                self.pending = None
                raise
            self.pending = None
            yield chunk

    async def finish(self):
        try:
            if self.pending is not None:
                try:
                    await self.pending
                except StopAsyncIteration:
                    self.ended = True
            if not self.ended:
                async for _ in self.iterator:
                    pass
        except (Exception, asyncio.CancelledError) as exc:
            self.ticket.backend.failures += 1
            self.ticket.backend.last_error = 'finish:' + type(exc).__name__
        finally:
            try:
                if self.pending is not None and not self.pending.done():
                    self.pending.cancel()
                    await asyncio.gather(self.pending, return_exceptions=True)
                await self.upstream.aclose()
            finally:
                self.gateway.release(self.ticket)

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            if self.ended:
                await self.finish()
            else:
                self.gateway.cleanup(self.ticket, self.finish())


def create_app(backends=(), *, gateway: Gateway | None = None,
               default_compatibility_key: str | None = None, **gateway_options) -> FastAPI:
    """Create an app without binding sockets or starting any server/process.

    GET /health and /metrics are local gateway state. GET /v1/models and POST
    /v1/{chat/completions,completions} forward only to explicitly compatible
    backends. Backend.base_url may end at the origin or at /v1. Forwarded bodies
    and responses (including SSE) are not tokenized or synchronously logged.
    Only registered alias rewriting parses request JSON. Limits count uploads,
    waiting requests and active response streams. Active disconnected requests
    retain admission while their upstream response is drained to completion.
    Use drain_key before unloading a lazy pool; drain_backend fences only one
    endpoint. Explicit aclose is forceful application shutdown, not graceful drain.
    Requires FastAPI, httpx and an ASGI runner in the embedding environment.
    """
    if gateway is not None and (backends or gateway_options):
        raise ValueError("Supply either gateway or backend/options, not both")
    gateway = gateway or Gateway(backends, **gateway_options)

    @asynccontextmanager
    async def lifespan(app):
        await gateway.start()
        try:
            yield
        finally:
            await gateway.aclose()

    app = FastAPI(lifespan=lifespan)
    app.state.gateway = gateway

    @app.get('/health')
    async def health():
        ready = not gateway.closing and any(not b.draining for b in gateway.backends.values())
        return JSONResponse(dict(ready=ready, backends=gateway.metrics()), status_code=200 if ready else 503)

    @app.get('/metrics')
    async def metrics():
        return gateway.snapshot()

    async def forward(request: Request):
        ticket = None
        upstream = None
        transferred = False
        response_task = None
        disconnect_watch = None
        client_disconnected = False
        disconnect_cancel = object()
        try:
            route = None
            if 'client_id' in request.path_params:
                route = gateway.routes.get(request.path_params['client_id'])
                if route is None:
                    raise AdmissionError(404, 'Unregistered client route')
            key = route.compatibility_key if route else request.headers.get('x-gateway-compatibility-key', default_compatibility_key)
            if not key:
                raise AdmissionError(400, "Explicit compatibility key required")
            if request.method == 'POST':
                await gateway.ensure_backend(key)
            ticket = gateway.reserve(key, route.client_id if route else request.headers.get('x-gateway-client-id', 'anonymous'),
                                     route.role if route else 'target')
            body = bytearray()
            async for chunk in request.stream():
                gateway.account_bytes(ticket, len(chunk))
                body.extend(chunk)
            owner = asyncio.current_task()
            async def watch_disconnect():
                nonlocal client_disconnected
                while True:
                    message = await request.receive()
                    if message['type'] == 'http.disconnect':
                        client_disconnected = True
                        owner.cancel(disconnect_cancel)
                        return
            disconnect_watch = asyncio.create_task(watch_disconnect())
            await gateway.wait_turn(ticket)
            backend = ticket.backend
            path = request.url.path
            if route:
                path = path.removeprefix('/'+route.client_id)
            base = backend.config.base_url.rstrip('/')
            if base.endswith('/v1'):
                path = path.removeprefix('/v1')
            url = base + path + ('?' + request.url.query if request.url.query else '')
            headers = _headers(request.headers)
            if route and backend.config.model_name:
                try:
                    payload = json.loads(body)
                    if not isinstance(payload, dict) or payload.get('model') != route.model_alias:
                        raise ValueError('Wrong route model alias')
                    payload['model'] = backend.config.model_name
                    body = json.dumps(payload, ensure_ascii=False).encode()
                except (ValueError, UnicodeError) as exc:
                    raise AdmissionError(400, 'Expected a JSON object with the registered model alias') from exc
                if len(body) > ticket.size:
                    gateway.account_bytes(ticket, len(body)-ticket.size)
                headers.pop('content-length', None)
            headers.update(backend.config.headers)
            req = backend.client.build_request(request.method, url, content=bytes(body), headers=headers)
            response_task = asyncio.create_task(backend.client.send(req, stream=True))
            upstream = await asyncio.shield(response_task)
            if upstream.status_code >= 500:
                backend.failures += 1
                backend.last_error = f'HTTP {upstream.status_code}'
            result = _ForwardedResponse(upstream, gateway, ticket)
            transferred = True
            return result
        except AdmissionError as exc:
            return JSONResponse({'error': {'message': str(exc), 'type': 'gateway_admission'}}, status_code=exc.status)
        except httpx.HTTPError as exc:
            if ticket:
                ticket.backend.failures += 1
                ticket.backend.last_error = type(exc).__name__
            status = 504 if isinstance(exc, httpx.TimeoutException) else 502
            return JSONResponse({'error': {'message': 'Backend request failed; not replayed',
                                            'type': type(exc).__name__}}, status_code=status)
        except asyncio.CancelledError as exc:
            if response_task is not None:
                gateway.cleanup(ticket, gateway.finish_response(ticket, response_task))
                transferred = True
            # Suppress only our disconnect cancellation. A concurrent shutdown
            # or external cancellation must still propagate to the ASGI server.
            current = asyncio.current_task()
            if (client_disconnected and exc.args == (disconnect_cancel,)
                    and current.cancelling() == 1 and not gateway.closing):
                current.uncancel()
                return JSONResponse({'error': {'type': 'client_disconnected'}}, status_code=499)
            raise
        finally:
            if disconnect_watch is not None:
                disconnect_watch.cancel()
                await asyncio.gather(disconnect_watch, return_exceptions=True)
            if not transferred:
                try:
                    if upstream is not None:
                        await upstream.aclose()
                finally:
                    if ticket is not None:
                        gateway.release(ticket)

    app.add_api_route('/v1/chat/completions', forward, methods=['POST'])
    app.add_api_route('/v1/completions', forward, methods=['POST'])
    app.add_api_route('/v1/models', forward, methods=['GET'])
    app.add_api_route('/{client_id}/v1/chat/completions', forward, methods=['POST'])
    app.add_api_route('/{client_id}/v1/completions', forward, methods=['POST'])

    async def client_status(client_id: str, models: bool):
        route = gateway.routes.get(client_id)
        if route is None:
            return JSONResponse({'error': 'Unregistered client route'}, status_code=404)
        if models:
            return {'object': 'list', 'data': [{'id': route.model_alias, 'object': 'model',
                                               'created': 0, 'owned_by': 'gateway'}]}
        return {'registered': True, 'compatibility_key': route.compatibility_key,
                'provisioned': any(b.config.compatibility_key == route.compatibility_key
                                   and not b.draining for b in gateway.backends.values()),
                'draining': route.compatibility_key in gateway.disabled_keys or gateway.closing}

    @app.get('/{client_id}/v1/models')
    async def client_models(client_id: str):
        return await client_status(client_id, True)

    @app.get('/{client_id}/health')
    @app.get('/{client_id}/v1/health')
    async def client_health(client_id: str):
        return await client_status(client_id, False)

    return app


async def serve_gateway(server, sock, ready):
    """Run a pre-bound HTTP server and signal readiness only after startup."""
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        while not server.started:
            if task.done():
                await task
                raise RuntimeError('Gateway exited during startup')
            await asyncio.sleep(.01)
        ready.set()
        await task
    finally:
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)


class GatewayService:
    """Synchronous Runner adapter around the same Gateway and FastAPI app.

    ``service = GatewayService(provision_backend=async_callback).start()``
    ``url = service.register_route('job-id', compatibility_key='exact-key',
                                  model_alias='client-model')``

    register_route returns http://127.0.0.1:<port>/job-id/v1. Registration and
    metadata/health requests never provision. Callback returns Sequence[Backend]
    and runs on the ASGI loop: the pool owner must offload blocking provisioning
    on its own executor. There is no gateway ThreadPoolExecutor or concurrency32
    default. One thread owns all async HTTP requests. poll() is Popen-shaped:
    None while alive, 0 after a clean stop, 1 on service failure.

    close(timeout) fences admissions, waits queued/active backend work, then stops
    only the frontend. Timeout leaves the service alive and fenced for inspection
    or another close attempt. No backend process is terminated or unloaded.
    """

    def __init__(self, backends=(), **gateway_options):
        self.gateway = Gateway(backends, **gateway_options)
        self.app = create_app(gateway=self.gateway)
        self.socket = None
        self.thread = None
        self.server = None
        self.error = None
        self.ready = threading.Event()
        self.stopping = False

    @property
    def base_url(self):
        if self.socket is None or self.socket.fileno() < 0:
            raise RuntimeError('Gateway service is not bound')
        return 'http://127.0.0.1:'+str(self.socket.getsockname()[1])

    def start(self, timeout: float = 30):
        import uvicorn
        if self.thread is not None:
            raise RuntimeError('Gateway service already started')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('127.0.0.1', 0))
        self.socket.listen(socket.SOMAXCONN)
        self.socket.setblocking(False)
        self.server = uvicorn.Server(uvicorn.Config(
            self.app, access_log=False, log_level='warning', lifespan='on',
            loop='asyncio', limit_concurrency=None))

        def run():
            try:
                asyncio.run(serve_gateway(self.server, self.socket, self.ready))
            except BaseException as exc:
                self.error = exc
            finally:
                self.ready.set()

        self.thread = threading.Thread(target=run, name='inference-gateway', daemon=True)
        self.thread.start()
        if not self.ready.wait(timeout):
            self.server.should_exit = True
            raise TimeoutError('Gateway startup timed out')
        if self.error is not None or not self.server.started:
            self.socket.close()
            raise RuntimeError('Gateway failed to start') from self.error
        return self

    def _call(self, factory, timeout=30):
        if self.poll() is not None or self.gateway.loop is None:
            raise RuntimeError('Gateway service is not running')
        if threading.current_thread() is self.thread:
            raise RuntimeError('Use the async Gateway API inside its event loop')
        future = asyncio.run_coroutine_threadsafe(factory(), self.gateway.loop)
        try:
            return future.result(timeout)
        except TimeoutError:
            future.cancel()
            raise

    def register_route(self, alias: str, *, compatibility_key: str,
                       model_alias: str | None = None, timeout: float = 30) -> str:
        if self.stopping:
            raise RuntimeError('Gateway service is draining')
        route = ClientRoute(alias, compatibility_key, model_alias or alias)
        async def register():
            prior = self.gateway.routes.get(alias)
            if prior is not None:
                if prior != route:
                    raise ValueError('Conflicting client route')
            else:
                await self.gateway.register_client(route)
        self._call(register, timeout)
        return self.base_url+'/'+alias+'/v1'

    def snapshot(self, timeout: float = 30):
        async def read():
            return self.gateway.snapshot()
        return self._call(read, timeout)

    def poll(self):
        if self.thread is not None and self.thread.is_alive():
            return None
        return 1 if self.error is not None or self.thread is None else 0

    def close(self, timeout: float = 30):
        if self.thread is None:
            return
        if not self.thread.is_alive():
            if self.socket:
                self.socket.close()
            return
        self.stopping = True
        deadline = time.monotonic()+timeout
        async def drain():
            keys = {r.compatibility_key for r in self.gateway.routes.values()}
            keys.update(b.config.compatibility_key for b in self.gateway.backends.values())
            self.gateway.disabled_keys.update(keys)
            await asyncio.gather(*(self.gateway.drain_key(k) for k in keys))
        self._call(drain, max(0, deadline-time.monotonic()))
        self.server.should_exit = True
        self.thread.join(max(0, deadline-time.monotonic()))
        if self.thread.is_alive():
            raise TimeoutError('Gateway frontend is still stopping')
        self.socket.close()
