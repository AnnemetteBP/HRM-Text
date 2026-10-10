"""Shared server ownership with direct client connections by default.

The scheduler assigns endpoints, not individual requests. vLLM owns batching
and request queues. The former HTTP gateway remains explicit opt-in for old
comparison fixtures, never the default production transport.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
import hashlib
import asyncio
import copy
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
from threading import Condition, Event, Lock, Thread
import time
import uuid


class ServerCapacityTimeout(TimeoutError):
    """No request was submitted: admission may be retried without a job attempt."""


class ClientMonitor:
    """Never exposes or signals the gateway/server's operating-system PID."""
    shared_client = True
    pid = None

    def __init__(self, gateway, alias=None):
        self.gateway = gateway
        self.alias = alias
        self.returncode = None
        self._done = Event()

    def poll(self):
        if self.returncode is not None:
            return self.returncode
        if self.alias and isinstance(self.gateway, NativeGatewayHost) and self.gateway.client_failed(self.alias):
            return 72
        return self.gateway.poll()

    def terminate(self):
        self.returncode = 143
        self._done.set()

    def kill(self):
        self.returncode = 137
        self._done.set()

    def wait(self, timeout=None):
        if self.poll() is not None:
            return self.poll()
        deadline = None if timeout is None else time.monotonic() + timeout
        while self.poll() is None:
            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                raise subprocess.TimeoutExpired('shared-client-monitor', timeout)
            self._done.wait(min(.05, remaining) if remaining is not None else .05)
        return self.poll()


def compatibility_key(job, gpu):
    """Existing launch key plus local mutable config/tokenizer file identities."""
    from .runtime import vllm_server_key
    key = vllm_server_key(job, gpu)
    paths = [Path(key.model_path) / name for name in
             ('config.json', 'tokenizer.json', 'tokenizer_config.json', 'chat_template.jinja',
              'model.safetensors.index.json')]
    paths.extend(Path(key.model_path).glob('*.safetensors'))
    args = shlex.split(key.extra_args)
    for index, arg in enumerate(args):
        if arg in ('--tokenizer', '--chat-template') and index + 1 < len(args):
            path = Path(args[index + 1])
            paths.extend([path / 'tokenizer.json', path / 'tokenizer_config.json'] if path.is_dir() else [path])
        elif arg.startswith(('--tokenizer=', '--chat-template=')):
            path = Path(arg.split('=', 1)[1])
            paths.extend([path / 'tokenizer.json', path / 'tokenizer_config.json'] if path.is_dir() else [path])
    files = {}
    for path in paths:
        if path.is_file():
            stat = path.stat()
            files[str(path.resolve())] = [stat.st_ino, stat.st_size, stat.st_mtime_ns]
    payload = dict(launch=asdict(key), files=files,
                   artifact_identity=job.metadata.get('shared_model_identity'))
    from .managed_backend import judge_identity
    payload['judge'] = judge_identity(job)
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


@dataclass
class _Slot:
    key: str | None = None
    lease: object | None = None
    holders: int = 0
    provisioning: bool = False
    tainted: bool = False
    clients: dict = field(default_factory=dict)
    capacity: int = 0


class _ResidencyLease:
    def __init__(self, owner, gpu, lease):
        self._owner, self.gpu = owner, gpu
        self.base_url, self.model_name = lease.base_url, lease.model_name
        self.process = lease.process
        self.log_path = lease.log_path
        self.judge_base_url = getattr(lease, 'judge_base_url', None)
        self.judge_model_name = getattr(lease, 'judge_model_name', None)
        self._released = False
        self._lock = Lock()

    def release(self, *, confirmed=True):
        if not confirmed:
            return  # Unknown upstream work must continue to block eviction/drain.
        with self._lock:
            if self._released:
                return
            with self._owner._condition:
                self._owner._slots[self.gpu].holders -= 1
                self._released = True
                self._owner._condition.notify_all()


class SharedServerPool:
    def __init__(self, plan_dir, gpus, gateway=None, event=lambda message: None, *,
                 backend=None, snapshot=None, max_requests_per_gpu=1024,
                 acquire_timeout=600, drain_timeout=600, server_affinity=None):
        from .runtime import gpu_snapshot
        from .managed_backend import ManagedBackend
        self.gpus = tuple(gpus)
        self.event = event
        self.plan_dir = Path(plan_dir)
        if not self.gpus or len(set(self.gpus)) != len(self.gpus) or max_requests_per_gpu < 1:
            raise ValueError('Unique GPUs and positive request capacity required')
        self.gateway = NativeGatewayHost(self) if gateway == 'proxy' else gateway
        self.backend = backend if backend is not None else ManagedBackend(Path(plan_dir), event)
        self.snapshot = snapshot or gpu_snapshot
        self.capacity = max_requests_per_gpu
        self.server_affinity = set(server_affinity if server_affinity is not None else os.sched_getaffinity(0))
        if not self.server_affinity:
            raise ValueError('Nonempty server CPU affinity required')
        self.acquire_timeout, self.drain_timeout = acquire_timeout, drain_timeout
        self._condition = Condition()
        self._slots = {gpu: _Slot() for gpu in self.gpus}
        self._accepting = True
        self._executor = ThreadPoolExecutor(max_workers=len(self.gpus), thread_name_prefix='shared-provision',
                                            initializer=self._server_affinity)

    def _server_affinity(self):
        os.sched_setaffinity(0, self.server_affinity)

    @staticmethod
    def _validate_job(job):
        from .managed_backend import judge_identity, judge_reserve
        if judge_identity(job):
            if judge_reserve(job) <= 0 or int(job.metadata.get('judge_max_concurrency', 32)) < 1:
                raise ValueError('Positive judge reserve and concurrency required')

    def configured_job(self, job):
        from .runtime import vllm_server_extra_args
        self._validate_job(job)
        extra = vllm_server_extra_args(job)
        args = shlex.split(extra)
        if not any(a == '--max-num-seqs' or a.startswith('--max-num-seqs=') for a in args):
            extra += f' --max-num-seqs {self.capacity}'
        return job.with_updates(metadata={**job.metadata, 'vllm_extra_args': extra.strip()})

    def preflight(self, jobs):
        """Database runner must call before claiming jobs; no servers start."""
        return [self.configured_job(job) for job in jobs]

    def request_capacity(self, job):
        from .runtime import vllm_server_extra_args
        args = shlex.split(vllm_server_extra_args(job))
        result = self.capacity
        for index, arg in enumerate(args):
            if arg == '--max-num-seqs':
                result = int(args[index + 1])
            elif arg.startswith('--max-num-seqs='):
                result = int(arg.split('=', 1)[1])
        if result < 1:
            raise ValueError('Positive --max-num-seqs required')
        return result

    def _provision(self, job, gpu, key):
        from .runtime import vllm_server_key
        from .managed_backend import judge_reserve
        slot = self._slots[gpu]
        try:
            if slot.lease is not None:
                self.backend.release_gpu(gpu, 'shared_idle_replacement')
            free, _, total = self.snapshot(gpu)
            utilization = vllm_server_key(job, gpu).gpu_memory_utilization
            required = max(int(job.metadata.get('min_gpu_free_mib') or 0),
                           math.ceil(float(total) * utilization) + judge_reserve(job))
            if not 0 < utilization <= 1 or float(free) < required:
                raise RuntimeError(f'Insufficient shared server startup headroom on GPU {gpu}')
            from .ownership import process_owner
            with process_owner(self.plan_dir/'owners'/'servers', gpu=gpu, compatibility_key=key):
                lease = self.backend.acquire(job, gpu)
        except BaseException:
            with self._condition:
                slot.key, slot.lease, slot.provisioning = None, None, False
                self._condition.notify_all()
            raise
        with self._condition:
            slot.key, slot.lease, slot.provisioning = key, lease, False
            slot.tainted = False
            slot.capacity = self.request_capacity(job)
            slot.holders += 1
            self._condition.notify_all()
        return _ResidencyLease(self, gpu, lease)

    def _acquire_residency(self, job, timeout=None, *, gpu=None):
        job = self.configured_job(job)
        deadline = time.monotonic() + (self.acquire_timeout if timeout is None else timeout)
        selected = self.gpus if gpu is None else (gpu,)
        if any(g not in self._slots for g in selected):
            raise ValueError('Unknown shared GPU')
        keys = {g: compatibility_key(job, g) for g in selected}
        with self._condition:
            while True:
                if not self._accepting:
                    raise RuntimeError('Shared pool draining for exclusive work')
                compatible = [(s.holders, gpu, s) for gpu, s in self._slots.items()
                              if gpu in keys and not s.provisioning and not s.tainted and s.key == keys[gpu]
                              and s.lease is not None and s.lease.process.poll() is None
                              and s.holders < self.capacity]
                idle = [(gpu, s) for gpu, s in self._slots.items()
                        if gpu in keys and not s.provisioning and not s.holders]
                # A loading replica must not prevent use of a ready one.
                # Least-held selection spreads subsequent clients once it loads.
                # Spread ready clients across free GPUs before sharing a busy
                # replica. Once all GPUs are occupied, reuse the least-held one.
                if compatible and (self.gateway is not None or not idle or min(s.holders for _, _, s in compatible) == 0):
                    _, gpu, slot = min(compatible, key=lambda item: item[:2])
                    slot.holders += 1
                    return _ResidencyLease(self, gpu, slot.lease)
                if idle:
                    gpu, slot = min(idle, key=lambda item: (item[1].lease is not None, item[0]))
                    slot.provisioning = True
                    slot.key = keys[gpu]
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ServerCapacityTimeout('No request slot available before deadline')
                self._condition.wait(remaining)
        # Startup never runs in a client-affinity thread or under the admission lock.
        return self._executor.submit(self._provision, job, gpu, keys[gpu]).result()

    def run_client(self, job, callback):
        job = self.configured_job(job)
        if self.gateway is None:
            return self._run_direct(job, callback)
        with self._condition:
            if not self._accepting:
                raise RuntimeError('Shared pool draining')
        alias = 'shared-' + uuid.uuid4().hex
        log = Path(job.log_dir) / f'{alias}.gateway.log'
        log.parent.mkdir(parents=True, exist_ok=True)
        log.touch()
        base_url = self.gateway.register_job(alias, job)
        monitor = ClientMonitor(self.gateway, alias)
        from .runtime import managed_judge_enabled
        monitor.judge_base_url = (base_url.removesuffix('/v1') + '-judge/v1'
                                 if managed_judge_enabled(job) else None)
        try:
            status = callback(base_url, log, monitor, alias)
            return status if status != 0 else (monitor.poll() or 0)
        finally:
            # Gateway unregister must reject new requests, not discard active leases.
            self.gateway.unregister_route(alias)

    def _run_direct(self, job, callback):
        """Hold residency, not exclusive GPU ownership, for a client session.

        A failed client may leave uncertain upstream work. Fence the replica
        from new assignments; replace it only after all existing clients leave.
        """
        lease = self._acquire_residency(job)
        token = uuid.uuid4().hex
        monitor = ClientMonitor(lease.process)
        monitor.judge_base_url = lease.judge_base_url
        monitor.judge_model_name = lease.judge_model_name
        with self._condition:
            self._slots[lease.gpu].clients[token] = job.job_id
        failed = True
        try:
            status = callback(lease.base_url, lease.log_path, monitor, lease.model_name)
            from .runtime import contains_oom
            failed = status != 0 or monitor.poll() is not None or contains_oom([lease.log_path])
            return status if status != 0 else (72 if failed else 0)
        finally:
            with self._condition:
                slot = self._slots[lease.gpu]
                slot.clients.pop(token)
                slot.tainted |= failed
                lease.release()

    def close_all(self, timeout=None):
        """Leave admissions closed on success OR timeout; never kill busy slots."""
        deadline = time.monotonic() + (self.drain_timeout if timeout is None else timeout)
        with self._condition:
            self._accepting = False
            self._condition.notify_all()
        if isinstance(self.gateway, NativeGatewayHost):
            self.gateway.drain_all(max(0, deadline - time.monotonic()))
        with self._condition:
            while any(s.holders or s.provisioning for s in self._slots.values()):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('Shared requests still active; exclusive work prohibited')
                self._condition.wait(remaining)
            self.backend.close_all()
            self._slots = {gpu: _Slot() for gpu in self.gpus}

    def reopen(self):
        """Call only after exclusive training/export has released its devices."""
        with self._condition:
            if any(s.holders or s.provisioning or s.lease for s in self._slots.values()):
                raise RuntimeError('Cannot reopen before successful drain')
            if isinstance(self.gateway, NativeGatewayHost):
                self.gateway.resume_admissions()
            self._accepting = True
            self._condition.notify_all()

    def snapshot_state(self):
        with self._condition:
            if self.gateway is None:
                slots = {g: dict(residency_holds=s.holders, provisioning=s.provisioning,
                    key=s.key, tainted=s.tainted, clients=len(s.clients),
                    job_ids=sorted(set(s.clients.values())),
                    registered_job_ids=sorted(set(s.clients.values())),
                    capacity=s.capacity, active=None, queued=None)
                    for g, s in self._slots.items()}
                totals = dict(active=None, queued=None, capacity=sum(s.capacity for s in self._slots.values()),
                    clients=sum(len(s.clients) for s in self._slots.values()),
                    job_ids=sorted({j for s in self._slots.values() for j in s.clients.values()}))
                return dict(transport='direct', accepting=self._accepting, slots=slots,
                            totals=totals, active=None, queued=None, capacity=totals['capacity'])
            result = {'accepting': self._accepting, 'slots': {
                gpu: {'residency_holds': s.holders, 'provisioning': s.provisioning, 'key': s.key}
                for gpu, s in self._slots.items()}}
        # Never wait for the ASGI loop while holding the residency condition.
        metrics = self.gateway.snapshot_cached() if isinstance(self.gateway, NativeGatewayHost) else None
        available = metrics is not None and metrics.get('available', False)
        for gpu, slot in result['slots'].items():
            backends = [b for b in (metrics or {}).get('backends', {}).values() if b.get('gpu') == gpu]
            slot.update(active=sum(b['active'] for b in backends) if available else None,
                        queued=sum(b['queued'] for b in backends) if available else None,
                        capacity=sum(b['max_num_seqs'] for b in backends) if available else None,
                        job_ids=sorted({j for b in backends for j in b.get('job_ids', [])}),
                        registered_job_ids=sorted({j for b in backends for j in b.get('registered_job_ids', [])}))
        result.update(gateway_metrics=metrics, totals={
            'active': metrics.get('active') if available else None,
            'queued': metrics.get('queued') if available else None,
            'capacity': sum(b['max_num_seqs'] for b in metrics['backends'].values()) if available else None,
            'clients': metrics.get('clients') if available else None,
            'job_ids': metrics.get('job_ids', []) if available else [],
            'provisioning_queued': sum(metrics.get('provisioning_queued', {}).values()) if available else None})
        result.update({name: result['totals'][name] for name in ('active', 'queued', 'capacity')})
        return result

    def shutdown(self, timeout=None):
        """Final-only shutdown. A failed drain deliberately leaves servers alive."""
        self.close_all(timeout)
        if isinstance(self.gateway, NativeGatewayHost) and self.gateway.server is not None:
            self.gateway.server.should_exit = True
            self.gateway.thread.join(self.drain_timeout if timeout is None else timeout)
            if self.gateway.thread.is_alive():
                raise TimeoutError('Gateway host did not stop')
        self._executor.shutdown(wait=True)


class NativeGatewayHost:
    """CPU HTTP host adapting gateway.Gateway; no GPU starts on registration.

Gateway owns individual request tickets. Pool leases here are residency holds,
released only after gateway drain/removal. Consequently neither client exits
nor a timeout can free a GPU behind another request's back.
"""
    def __init__(self, pool):
        self.pool = pool
        self._start_lock = Lock()
        self.thread = None
        self.loop = None
        self.engine = None
        self.server = None
        self.base_url = None
        self.jobs = {}
        self.resident = {}
        self.starting = {}
        self.ready = Event()
        self.error = None
        self.rebalance_errors = []
        self._rebalance_needed = False
        self.alias_jobs = {}
        self._snapshot_lock = Lock()
        self._snapshot_value = None
        self._snapshot_at = 0.0
        self._snapshot_attempt = float('-inf')
        self._snapshot_error = None

    def _start(self):
        with self._start_lock:
            if self.thread is None:
                self.thread = Thread(target=self._serve, daemon=True, name='shared-gateway')
                self.thread.start()
            if not self.ready.wait(30):
                raise TimeoutError('Gateway CPU host startup timed out')
            if self.error is not None:
                raise RuntimeError('Gateway CPU host startup failed') from self.error

    def _serve(self):
        self.pool._server_affinity()
        import socket
        import uvicorn
        from .gateway import Gateway, create_app, serve_gateway
        async def serve():
            self.loop = asyncio.get_running_loop()
            self._placement_lock = asyncio.Lock()
            self._changed = asyncio.Event()
            self._rebalance_event = asyncio.Event()
            host = self
            class NotifyingGateway(Gateway):
                def reserve(self, key, client, role='target'):
                    ticket = super().reserve(key, client, role)
                    if len(ticket.backend.tickets) > ticket.backend.config.max_num_seqs:
                        host._rebalance_event.set()
                    return ticket

                async def ensure_backend(self, key):
                    try:
                        return await super().ensure_backend(key)
                    finally:
                        host._changed.set()
                        if host._rebalance_needed:
                            host._rebalance_event.set()

                def release(self, ticket):
                    super().release(ticket)
                    host._changed.set()
                    if host._rebalance_needed:
                        host._rebalance_event.set()
            self.engine = NotifyingGateway(provision_backend=self._provision,
                provision_queue_capacity=3 * len(self.pool.gpus) * self.pool.capacity)
            rebalance_task = asyncio.create_task(self._rebalance_loop())
            sock = socket.socket()
            sock.bind(('127.0.0.1', 0))
            self.base_url = f'http://127.0.0.1:{sock.getsockname()[1]}'
            self.server = uvicorn.Server(uvicorn.Config(create_app(gateway=self.engine),
                                         log_level='warning', access_log=False))
            try:
                await serve_gateway(self.server, sock, self.ready)
            finally:
                rebalance_task.cancel()
                await asyncio.gather(rebalance_task, return_exceptions=True)
                sock.close()
        try:
            asyncio.run(serve())
        except BaseException as exc:
            self.error = exc
        finally:
            self.ready.set()

    def _call(self, coroutine, timeout=None):
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result(timeout)

    def register_job(self, alias, job):
        self._start()
        key = compatibility_key(job, self.pool.gpus[0])
        async def register():
            from .gateway import ClientRoute
            task = self.engine.provisioning.get(key)
            # Request failures must not evict servers still serving other clients.
            # Retain their counters for conservative cleanup after the group drains.
            has_clients = any(route.compatibility_key == key for route in self.engine.routes.values())
            needs_recovery = (not has_clients and any(
                state.config.compatibility_key == key and state.failures
                for state in self.engine.backends.values())) or (
                task is not None and task.done() and (task.cancelled() or task.exception() is not None))
            # Normal registration must not wait behind GPU startup; this check
            # and route registration both run on the gateway event loop.
            if needs_recovery:
                async with self._placement_lock:
                    for lease in list(self.resident.get(key, [])):
                        if any(state.failures for state in self._states(key, lease.gpu)):
                            await self._remove_gpu(key, lease.gpu)
                    task = self.engine.provisioning.get(key)
                    if task is not None and task.done() and (task.cancelled() or task.exception() is not None):
                        await self.engine.reset_provisioning(key)
            self.engine.provision_queue_capacity = max(self.engine.provision_queue_capacity,
                3 * len(self.pool.gpus) * self.pool.request_capacity(job))
            self.jobs.setdefault(key, job)
            await self.engine.register_client(ClientRoute(alias, key, alias))
            self.alias_jobs[alias] = job.job_id
            from .runtime import managed_judge_enabled, judge_served_model_name
            if managed_judge_enabled(job):
                await self.engine.register_client(ClientRoute(alias+'-judge', key,
                    judge_served_model_name(job), role='judge'))
                self.alias_jobs[alias+'-judge'] = job.job_id
        self._call(register(), self.pool.drain_timeout + 30)
        return self.base_url + '/' + alias + '/v1'

    def unregister_route(self, alias):
        async def unregister():
            removed = self.engine.routes.pop(alias, None)
            self.engine.routes.pop(alias+'-judge', None)
            if removed and not any(r.compatibility_key == removed.compatibility_key
                                   for r in self.engine.routes.values()):
                self._rebalance_needed = True
                self._rebalance_event.set()
        self._call(unregister(), 30)

    def poll(self):
        return None if self.thread is not None and self.thread.is_alive() and self.error is None else 71

    def client_failed(self, alias):
        if self.poll() is not None:
            return True
        async def read():
            route = self.engine.routes.get(alias)
            if route is None:
                return True
            key = route.compatibility_key
            task = self.engine.provisioning.get(key)
            if task is not None and task.done() and (task.cancelled() or task.exception() is not None):
                return True
            exits = [(lease.gpu, lease.process.poll()) for lease in self.resident.get(key, [])
                     if lease.process.poll() is not None]
            errors = [(state.config.id, state.failures, getattr(state, 'last_error', None))
                      for state in self.engine.backends.values()
                      if state.config.compatibility_key == key and state.failures]
            if exits:
                self.pool.event(f'SHARED_CLIENT_FAILED {alias} exits={exits} errors={errors}')
            # HTTP errors reach the requesting client as failed responses. They
            # are not proof of process death and must not poison unrelated jobs.
            return bool(exits)
        try:
            return self._call(read(), 5)
        except TimeoutError:
            # A busy broker is not evidence of a dead server. The next poll
            # still checks actual process exits and confirmed backend errors.
            return False

    def _snapshot_on_loop(self):
        snapshot = self.engine.snapshot()
        gpu_by_id = {backend.id: lease.gpu for key, leases in self.resident.items()
                     for lease in leases for backend in self._configs(key, lease)}
        live_aliases = set(self.engine.routes)
        for name, state in self.engine.backends.items():
            aliases = {ticket.client for ticket in state.tickets}
            live_aliases.update(aliases)
            registered = {a for a, r in self.engine.routes.items()
                          if r.compatibility_key == state.config.compatibility_key}
            snapshot['backends'][name].update(gpu=gpu_by_id.get(name), role=state.config.role,
                job_ids=sorted({self.alias_jobs[a] for a in aliases if a in self.alias_jobs}),
                registered_job_ids=sorted({self.alias_jobs[a] for a in registered if a in self.alias_jobs}))
        snapshot.update(clients=len(live_aliases),
                        job_ids=sorted({self.alias_jobs[a] for a in live_aliases if a in self.alias_jobs}))
        self.alias_jobs = {a: j for a, j in self.alias_jobs.items() if a in live_aliases}
        return snapshot

    def snapshot_cached(self):
        """At most one ASGI read/second; 100ms maximum wait, never under pool lock."""
        if self.thread is None:
            return dict(available=True, stale=False, age_seconds=0, backends={}, active=0,
                        queued=0, clients=0, job_ids=[], provisioning_queued={})
        now = time.monotonic()
        if now - self._snapshot_attempt >= 1 and self._snapshot_lock.acquire(blocking=False):
            try:
                if now - self._snapshot_attempt >= 1:
                    self._snapshot_attempt = now
                    async def read():
                        return self._snapshot_on_loop()
                    future = None
                    try:
                        if self.loop is None or not self.loop.is_running():
                            raise RuntimeError('Gateway loop is not running')
                        coroutine = read()
                        try:
                            future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
                        except Exception:
                            coroutine.close()
                            raise
                        self._snapshot_value = future.result(timeout=.1)
                        self._snapshot_at = time.monotonic()
                        self._snapshot_error = None
                    except Exception as exc:
                        if future is not None:
                            future.cancel()  # Read-only snapshot; no model/route side effects.
                        self._snapshot_error = type(exc).__name__
            finally:
                self._snapshot_lock.release()
        value = copy.deepcopy(self._snapshot_value) if self._snapshot_value is not None else {}
        age = time.monotonic() - self._snapshot_at if self._snapshot_value is not None else None
        value.update(available=self._snapshot_value is not None, age_seconds=age,
                     stale=self._snapshot_error is not None or age is None or age > 2,
                     error=self._snapshot_error)
        return value

    def _configs(self, key, lease):
        from .gateway import Backend
        yield Backend(id=f'{key}-{lease.gpu}', base_url=lease.base_url,
                      compatibility_key=key, model_name=lease.model_name,
                      max_num_seqs=self.pool.request_capacity(self.jobs[key]))
        if lease.judge_base_url:
            yield Backend(id=f'{key}-{lease.gpu}-judge', base_url=lease.judge_base_url,
                          compatibility_key=key, model_name=lease.judge_model_name, role='judge',
                          max_num_seqs=int(self.jobs[key].metadata.get('judge_max_concurrency', 32)))

    def _states(self, key, gpu):
        return [self.engine.backends[name] for name in (f'{key}-{gpu}', f'{key}-{gpu}-judge')
                if name in self.engine.backends]

    async def _remove(self, key):
        await self.engine.drain_key(key, self.pool.drain_timeout)
        states = [b for b in self.engine.backends.values() if b.config.compatibility_key == key]
        for lease in self.resident.get(key, []):
            if any(state.failures for state in self._states(key, lease.gpu)):
                await self._stop_failed_backend(key, lease.gpu)
        for state in states:
            await self.engine.remove_backend(state.config.id)
        for lease in self.resident.pop(key, []):
            lease.release()
        await self.engine.reset_provisioning(key)

    async def _stop_failed_backend(self, key, gpu):
        states = self._states(key, gpu)
        if any(not state.draining or state.tickets for state in states):
            raise RuntimeError('Cannot terminate backend before gateway response leases drain')
        lease = next(lease for lease in self.resident[key] if lease.gpu == gpu)
        # The pool alone owns this process. Network timeout is not proof that
        # generation stopped; confirmed process exit is the recovery boundary.
        await self.loop.run_in_executor(self.pool._executor, self.pool.backend.release_gpu,
                                        gpu, 'shared_drained_failure_cleanup')
        if lease.process.poll() is None:
            raise RuntimeError('Owned failed backend termination was not confirmed')
        with self.pool._condition:
            slot = self.pool._slots[gpu]
            slot.lease = None
            slot.key = None

    async def _remove_gpu(self, key, gpu):
        states = self._states(key, gpu)
        for state in states:
            state.draining = True
        # When removing a group's last backend, new requests should wait for
        # lazy re-provisioning, not see an explicitly disabled compatibility key.
        if len(self.resident[key]) == 1:
            await self.engine.reset_provisioning(key)
        await asyncio.gather(*(self.engine.drain_backend(state.config.id, self.pool.drain_timeout)
                               for state in states))
        if any(state.failures for state in states):
            await self._stop_failed_backend(key, gpu)
        for state in states:
            await self.engine.remove_backend(state.config.id)
        remaining = []
        for lease in self.resident[key]:
            if lease.gpu == gpu:
                lease.release()
            else:
                remaining.append(lease)
        if remaining:
            self.resident[key] = remaining
        else:
            del self.resident[key]

    async def _provision(self, key):
        from .managed_backend import judge_identity
        while True:
            async with self._placement_lock:
                occupied = {lease.gpu for leases in self.resident.values() for lease in leases}
                occupied.update(gpu for gpus in self.starting.values() for gpu in gpus)
                selected = [gpu for gpu in self.pool.gpus if gpu not in occupied]
                # A small judged shard must leave room for other configurations.
                if judge_identity(self.jobs[key]):
                    selected = selected[:1]
                self._changed.clear()
                # Provisioning waiters have not yet reserved their first ticket.
                # Do not evict their freshly started model in that admission gap.
                candidates = [] if selected else [(sum(len(s.tickets) for s in self._states(previous, lease.gpu)), previous, lease.gpu)
                              for previous, leases in self.resident.items() if previous != key
                              and not self.engine.provision_waiters.get(previous, 0)
                              for lease in leases if f'{previous}-{lease.gpu}' in self.engine.backends]
                if candidates:
                    _, previous, gpu = min(candidates)
                    await self._remove_gpu(previous, gpu)
                    selected = [gpu]
                if selected:
                    self.starting[key] = selected
                    break
            await self._changed.wait()
        # GPU selections are fenced above; slow model loading must not serialize
        # unrelated configurations or require the placement lock to complete.
        try:
            leases = await self._start_gpus(key, selected)
            async with self._placement_lock:
                self.resident.setdefault(key, []).extend(leases)
            return [config for lease in leases for config in self._configs(key, lease)]
        finally:
            async with self._placement_lock:
                self.starting.pop(key, None)
                self._changed.set()

    async def _start_gpus(self, key, selected):
        job = self.jobs[key]
        results = await asyncio.gather(*(
            self.loop.run_in_executor(None, lambda g=gpu: self.pool._acquire_residency(job, gpu=g))
            for gpu in selected), return_exceptions=True)
        leases = [r for r in results if not isinstance(r, BaseException)]
        errors = [r for r in results if isinstance(r, BaseException)]
        if errors:
            for lease in leases:
                lease.release()
            raise errors[0]
        return leases

    def _additional_replicas(self, key):
        states = [s for s in self.engine.backends.values()
                  if s.config.compatibility_key == key and not s.draining]
        needed = 0
        for role in {s.config.role for s in states}:
            group = [s for s in states if s.config.role == role]
            capacity = sum(s.config.max_num_seqs for s in group)
            excess = sum(len(s.tickets) for s in group) - capacity
            needed = max(needed, math.ceil(excess / group[0].config.max_num_seqs))
        return needed

    async def _rebalance_loop(self):
        from .gateway import Backend
        failed_targets = set()
        while True:
            await self._rebalance_event.wait()
            self._rebalance_event.clear()
            if not self.pool._accepting:
                continue
            async with self._placement_lock:
                registered = {r.compatibility_key for r in self.engine.routes.values()}
                targets = [key for key in registered if key in self.resident and key not in failed_targets
                           and key not in self.engine.disabled_keys and any(
                               b.config.compatibility_key == key and not b.draining
                               for b in self.engine.backends.values())]
                if not targets or not self.pool._accepting:
                    continue
                # One bounded pass per pressure/unregister/drain event. No
                # polling, database access, or per-request executor admission.
                target = max(targets, key=lambda k: (self._additional_replicas(k), -len(self.resident[k]), k))
                occupied = {lease.gpu for leases in self.resident.values() for lease in leases}
                occupied.update(gpu for gpus in self.starting.values() for gpu in gpus)
                selected = [gpu for gpu in self.pool.gpus if gpu not in occupied]
                try:
                    for previous in list(self.resident):
                        if previous in registered or self.engine.provision_waiters.get(previous, 0):
                            continue
                        for lease in list(self.resident.get(previous, [])):
                            if any(r.compatibility_key == previous for r in self.engine.routes.values()):
                                break
                            states = self._states(previous, lease.gpu)
                            if not states or any(s.tickets or s.draining for s in states):
                                continue
                            await self._remove_gpu(previous, lease.gpu)
                            selected.append(lease.gpu)
                    # Do not spend another cold start on a nearly finished task
                    # that already fits in its resident server's request capacity.
                    selected = selected[:self._additional_replicas(target)]
                    if selected:
                        leases = await self._start_gpus(target, selected)
                        self.resident[target].extend(leases)
                        for lease in leases:
                            for config in self._configs(target, lease):
                                await self.engine.register_backend(config)
                except Exception as exc:
                    failed_targets.add(target)
                    self.rebalance_errors.append({'key': target, 'error': repr(exc)})
                orphans = set(self.resident) - {r.compatibility_key for r in self.engine.routes.values()}
                self._rebalance_needed = any(b.tickets and b.config.compatibility_key in orphans
                                             for b in self.engine.backends.values())

    def drain_all(self, timeout):
        if self.thread is None:
            return
        async def drain():
            # Fence pending provisioning before taking its placement lock.
            self.engine.disabled_keys.update(self.jobs)
            for task in list(self.engine.provisioning.values()):
                if not task.done():
                    await asyncio.shield(task)
            async with self._placement_lock:
                for key in list(self.resident):
                    await self._remove(key)
        self._call(drain(), timeout)

    def resume_admissions(self):
        if self.thread is None:
            return
        async def resume():
            for key in self.jobs:
                # Failed provisioning stays failed until an explicit retry;
                # only the exclusive-work fence on healthy/unloaded keys clears.
                if key not in self.engine.provisioning:
                    self.engine.disabled_keys.discard(key)
        self._call(resume(), 30)
