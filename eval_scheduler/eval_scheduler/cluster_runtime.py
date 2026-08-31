from __future__ import annotations

import json
import os
import shlex
import signal
import socket
import subprocess
import sys
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Any

from .cluster_protocol import (
    ClusterClient,
    ClusterProtocolError,
    atomic_json,
    ensure_cluster_token,
    start_cluster_server,
)
from .locking import PlanLock
from .model import (
    Action,
    Capability,
    ExecutionScope,
    Job,
    JobStatus,
    append_tsv,
    read_plan,
    write_plan,
)
from .plan import plan_path
from .resources import GpuSnapshot, Lease, ResourceId, WorkerInfo
from .runtime import (
    STOP_STATUS,
    Runner,
    SchedulerError,
    VLLMServerPool,
    contains_oom,
    dependencies_satisfied,
    gpu_snapshot,
    now,
    run_job,
    split_command_environment,
    stop_requested,
    training_checkpoint_ready,
    vllm_server_key,
)

CLUSTER_SNAPSHOT = "cluster.snapshot.json"
WORKER_MANIFEST_DIR = "cluster-workers"


def _git_head(workdir: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=workdir, text=True, timeout=10
        ).strip()
    except Exception:  # noqa: BLE001 - repository metadata must not prevent worker startup
        return "unknown"


def _gpu_inventory(gpus: list[int], pool: VLLMServerPool | None = None) -> dict[int, GpuSnapshot]:
    server_state = pool.snapshot() if pool is not None else {}
    result: dict[int, GpuSnapshot] = {}
    for gpu in gpus:
        free, used, total = gpu_snapshot(gpu)
        try:
            util_text = subprocess.check_output(
                [
                    "nvidia-smi",
                    "-i",
                    str(gpu),
                    "--query-gpu=utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                text=True,
                timeout=5,
            ).strip().splitlines()[0]
            util = int(util_text)
        except Exception:  # noqa: BLE001 - monitoring must tolerate unavailable nvidia-smi
            util = None
        server = server_state.get(gpu, {})
        result[gpu] = GpuSnapshot(
            gpu_id=gpu,
            free_mib=int(free) if free != "NA" else None,
            used_mib=int(used) if used != "NA" else None,
            total_mib=int(total) if total != "NA" else None,
            utilization=util,
            server_key=str(server.get("key") or ""),
            server_utilization=float(server.get("gpu_memory_utilization") or 0.0),
        )
    return result


def _job_oom(job: Job) -> bool:
    paths = [
        Path(job.log_dir) / name
        for name in ("server.log", "dfm-evals.log", "euroeval.log", "euroeval-wrapper.log")
    ]
    if job.action.value == "eval_standard":
        paths.append(Path(job.log_dir) / f"{job.name}_shard_{job.shard}_of_{job.shards}.log")
    return contains_oom(paths)


class ClusterCoordinator:
    """Single plan owner and resource coordinator for fixed-membership workers."""

    def __init__(
        self,
        plan_dir: Path,
        *,
        bind_host: str,
        port: int,
        worker_ttl: float = 30.0,
        persistent_vllm: bool = True,
        expected_nodes: int = 0,
    ) -> None:
        self.plan_dir = plan_dir.resolve()
        self.plan_file = plan_path(self.plan_dir)
        self.bind_host = bind_host
        self.port = port
        self.worker_ttl = worker_ttl
        self.persistent_vllm = persistent_vllm
        self.expected_nodes = expected_nodes
        self.token = ensure_cluster_token(self.plan_dir)
        self.lock = Lock()
        self.plan_runner = Runner(self.plan_dir, [], persistent_vllm=False)
        self.workers: dict[str, WorkerInfo] = {}
        self.leases: dict[str, Lease] = {}
        self.lease_by_job: dict[str, str] = {}
        self.control_futures: dict[Future[tuple[str, int]], str] = {}
        self.control_pool = ThreadPoolExecutor(max_workers=12, thread_name_prefix="eval-control")
        self.mode = "evaluating"
        self.started_at = time.time()
        self.stop_event = Event()
        self.teardown_job: str | None = None
        self.teardown_pending: set[str] = set()
        self.teardown_acked: set[str] = set()
        self.server = None
        self.server_thread: Thread | None = None
        self._restore_snapshot()

    def _restore_snapshot(self) -> None:
        path = self.plan_dir / CLUSTER_SNAPSHOT
        if not path.exists():
            return
        try:
            value = json.loads(path.read_text())
            jobs = {job.job_id: job for job in self._read_jobs_locked()}
            grace_time = time.time()
            workers = {
                node_id: WorkerInfo.from_wire(worker)
                for node_id, worker in (value.get("workers") or {}).items()
            }
            for worker in workers.values():
                worker.last_heartbeat = grace_time
            leases = {
                token: Lease.from_wire(lease)
                for token, lease in (value.get("leases") or {}).items()
            }
            leases = {
                token: lease
                for token, lease in leases.items()
                if lease.job_id in jobs
                and jobs[lease.job_id].status == JobStatus.RUNNING
                and jobs[lease.job_id].attempt == lease.attempt
                and lease.worker_id in workers
            }
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return
        self.workers = workers
        self.leases = leases
        self.lease_by_job = {lease.job_id: token for token, lease in leases.items()}
        self.mode = "evaluating"

    def event(self, message: str) -> None:
        self.plan_runner.event(f"CLUSTER {message}")

    def handle(self, method: str, path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        if method not in {"GET", "POST"}:
            return 405, {"error": "method not allowed"}
        if path == "/v1/register":
            return 200, self._register(payload)
        if path == "/v1/heartbeat":
            return 200, self._heartbeat(payload)
        if path == "/v1/poll":
            return 200, self._poll(payload)
        if path == "/v1/complete":
            return 200, self._complete(payload)
        if path == "/v1/teardown-ack":
            return 200, self._teardown_ack(payload)
        if path == "/v1/event":
            return 200, self._worker_event(payload)
        if path == "/v1/snapshot":
            return 200, self.snapshot()
        if path == "/v1/admin/drain":
            return 200, self._admin_drain(payload)
        return 404, {"error": "not found"}

    def _admin_drain(self, payload: dict[str, Any]) -> dict[str, Any]:
        node_id = str(payload["node_id"])
        drained = bool(payload.get("drained", True))
        with self.lock:
            worker = self.workers.get(node_id)
            if worker is None:
                raise ClusterProtocolError(f"unknown worker: {node_id}")
            worker.drained = drained
            self.event(f"WORKER_DRAIN node_{node_id} drained_{int(drained)}")
            self._write_snapshot_locked()
        return {"ok": True, "node_id": node_id, "drained": drained}

    def _validate_worker(self, payload: dict[str, Any]) -> WorkerInfo:
        node_id = str(payload["node_id"])
        boot_id = str(payload["boot_id"])
        worker = self.workers.get(node_id)
        if worker is None:
            raise ClusterProtocolError(f"worker is not registered: {node_id}")
        if worker.boot_id != boot_id:
            raise ClusterProtocolError(f"stale worker boot id for {node_id}")
        return worker

    def _register(self, payload: dict[str, Any]) -> dict[str, Any]:
        node_id = str(payload["node_id"])
        boot_id = str(payload["boot_id"])
        capabilities = {Capability(item) for item in payload.get("capabilities", [])}
        gpus = {
            int(item["gpu_id"]): GpuSnapshot.from_wire(item)
            for item in payload.get("gpus", [])
        }
        worker = WorkerInfo(
            node_id=node_id,
            boot_id=boot_id,
            hostname=str(payload.get("hostname") or node_id),
            capabilities=capabilities,
            repo_commit=str(payload.get("repo_commit") or "unknown"),
            python=str(payload.get("python") or ""),
            environment=str(payload.get("environment") or ""),
            gpus=gpus,
            active_leases={str(item) for item in payload.get("active_leases", [])},
        )
        with self.lock:
            previous = self.workers.get(node_id)
            if previous is not None and previous.boot_id != boot_id:
                self._fence_worker_locked(previous, reason="new_boot")
            self.workers[node_id] = worker
            self.event(
                f"WORKER_REGISTER node_{node_id} boot_{boot_id} "
                f"gpus_{','.join(map(str, sorted(gpus)))} capabilities_{','.join(sorted(item.value for item in capabilities))}"
            )
            self._write_snapshot_locked()
        return {"ok": True, "worker_ttl": self.worker_ttl, "mode": self.mode}

    def _heartbeat(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            worker = self._validate_worker(payload)
            worker.last_heartbeat = time.time()
            worker.gpus = {
                int(item["gpu_id"]): GpuSnapshot.from_wire(item)
                for item in payload.get("gpus", [])
            }
            worker.active_leases = {str(item) for item in payload.get("active_leases", [])}
            for token in worker.active_leases:
                lease = self.leases.get(token)
                if lease is not None and lease.worker_boot_id == worker.boot_id:
                    self.leases[token] = Lease(
                        **{**lease.__dict__, "last_heartbeat": worker.last_heartbeat}
                    )
            self._write_snapshot_locked()
            command = self._worker_command_locked(worker)
        return {
            "ok": True,
            "mode": self.mode,
            "command": command,
            "teardown_job": self.teardown_job or "",
        }

    def _poll(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            worker = self._validate_worker(payload)
            worker.last_heartbeat = time.time()
            command = self._worker_command_locked(worker)
            if command:
                return {"command": command, "mode": self.mode}
            if self.mode != "evaluating" or stop_requested(self.plan_dir) or worker.drained:
                return {"command": "wait", "mode": self.mode}
            assignment = self._assign_locked(worker)
            if assignment is None:
                return {"command": "wait", "mode": self.mode}
            return {"command": "run", "mode": self.mode, **assignment}

    def _worker_command_locked(self, worker: WorkerInfo) -> str:
        if self.teardown_job and worker.node_id in self.teardown_pending:
            return "teardown"
        if self.mode == "stopped":
            return "stop"
        if self.mode in {"draining", "training"}:
            return "wait"
        return ""

    def _assign_locked(self, worker: WorkerInfo) -> dict[str, Any] | None:
        jobs = self._read_jobs_locked()
        ready = [
            job
            for job in jobs
            if job.status == JobStatus.PENDING
            and dependencies_satisfied(job, jobs)
            and job.resolved_execution_scope == ExecutionScope.GPU
            and job.resolved_capability in worker.capabilities
            and (not job.node_selector or job.node_selector == worker.node_id)
        ]
        if not ready:
            return None
        leased_resources = {
            resource
            for lease in self.leases.values()
            for resource in lease.resources
        }
        candidates: list[tuple[int, int, int, Job]] = []
        for job_index, job in enumerate(ready):
            if job.resolved_gpu_count != 1:
                continue
            minimum = int(job.metadata.get("min_gpu_free_mib") or 0)
            for gpu_id, snapshot in worker.gpus.items():
                resource = ResourceId(worker.node_id, gpu_id)
                if resource in leased_resources:
                    continue
                if snapshot.free_mib is None:
                    continue
                effective_free = snapshot.free_mib
                compatible = 0
                if snapshot.server_key:
                    desired = (
                        vllm_server_key(job, gpu_id).digest
                        if job.resolved_capability == Capability.EVAL
                        else ""
                    )
                    if desired and snapshot.server_key == desired:
                        compatible = 1
                        effective_free = snapshot.total_mib or effective_free
                    else:
                        effective_free += round(
                            snapshot.server_utilization * (snapshot.total_mib or 0)
                        )
                if effective_free >= minimum:
                    candidates.append((compatible, -job_index, effective_free, job))
        if not candidates:
            return None
        _compatible, _order, effective_free, job = max(
            candidates, key=lambda item: (item[1], item[0], item[2])
        )
        gpu_choices = [
            gpu_id
            for gpu_id, snapshot in worker.gpus.items()
            if ResourceId(worker.node_id, gpu_id) not in leased_resources
            and snapshot.free_mib is not None
            and snapshot.free_mib
            + round(snapshot.server_utilization * (snapshot.total_mib or 0))
            >= int(job.metadata.get("min_gpu_free_mib") or 0)
        ]
        gpu_id = max(gpu_choices, key=lambda item: worker.gpus[item].free_mib or -1)
        claimed = self._claim_job_locked(job.job_id)
        if claimed is None:
            return None
        token = uuid.uuid4().hex
        timestamp = time.time()
        lease = Lease(
            token=token,
            job_id=claimed.job_id,
            attempt=claimed.attempt,
            worker_id=worker.node_id,
            worker_boot_id=worker.boot_id,
            resources=(ResourceId(worker.node_id, gpu_id),),
            issued_at=timestamp,
            last_heartbeat=timestamp,
        )
        self.leases[token] = lease
        self.lease_by_job[claimed.job_id] = token
        self.plan_runner.event(
            "START "
            f"{claimed.job_id} {claimed.action.value} {claimed.family} {claimed.name} "
            f"shard_{claimed.shard if claimed.shard is not None else '-'}_of_{claimed.shards if claimed.shards is not None else '-'} "
            f"gpu_{gpu_id} attempt_{claimed.attempt + 1}_of_{claimed.max_retries + 1} "
            f"batch_{claimed.retry_batch() if claimed.retry_batch() is not None else '-'} "
            f"mem_free_before_{worker.gpus[gpu_id].free_mib} node_{worker.node_id} lease_{token}"
        )
        self._write_snapshot_locked()
        return {
            "lease": lease.to_wire(),
            "job": claimed.to_wire(),
            "gpu_id": gpu_id,
            "effective_free_mib": effective_free,
        }

    def _complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        token = str(payload["lease_token"])
        with self.lock:
            worker = self._validate_worker(payload)
            lease = self.leases.get(token)
            if lease is None:
                return {"accepted": False, "reason": "stale_or_unknown_lease"}
            if lease.worker_id != worker.node_id or lease.worker_boot_id != worker.boot_id:
                return {"accepted": False, "reason": "fenced_lease"}
            status = int(payload.get("status", 72))
            self._finalize_remote_locked(lease, status, payload)
            self._write_snapshot_locked()
        return {"accepted": True}

    def _finalize_remote_locked(
        self,
        lease: Lease,
        status: int,
        payload: dict[str, Any],
    ) -> None:
        jobs = self._read_jobs_locked()
        job = next((item for item in jobs if item.job_id == lease.job_id), None)
        if job is None:
            self._drop_lease_locked(lease)
            return
        resource_text = ",".join(resource.label for resource in lease.resources)
        append_tsv(
            self.plan_dir / "attempts.tsv",
            [
                now(),
                job.job_id,
                job.action.value,
                job.family,
                job.name,
                "" if job.shard is None else str(job.shard),
                "" if job.shards is None else str(job.shards),
                resource_text,
                str(job.attempt + 1),
                "" if job.retry_batch() is None else str(job.retry_batch()),
                str(status),
                "1" if payload.get("oom") else "0",
                str(payload.get("free_before", "NA")),
                str(payload.get("used_before", "NA")),
                str(payload.get("total_before", "NA")),
                str(payload.get("free_after", "NA")),
                str(payload.get("used_after", "NA")),
                str(payload.get("total_after", "NA")),
                job.log_dir,
                lease.worker_id,
                lease.token,
            ],
        )
        if status == 0:
            self._update_job_locked(job.job_id, status=JobStatus.DONE)
            self.plan_runner.event(
                f"END {job.job_id} {job.action.value} {job.family} {job.name} "
                f"status_0 node_{lease.worker_id} lease_{lease.token}"
            )
        elif status == STOP_STATUS:
            self._update_job_locked(job.job_id, status=JobStatus.PENDING)
            self.plan_runner.event(
                f"STOPPED {job.job_id} {job.action.value} {job.family} {job.name} "
                f"status_{status} node_{lease.worker_id} lease_{lease.token}"
            )
        else:
            next_attempt = job.attempt + 1
            if next_attempt <= job.max_retries:
                self._update_job_locked(
                    job.job_id, status=JobStatus.PENDING, attempt=next_attempt
                )
                self.plan_runner.event(
                    f"RETRY {job.job_id} {job.action.value} {job.family} {job.name} "
                    f"status_{status} oom_{1 if payload.get('oom') else 0} "
                    f"next_attempt_{next_attempt + 1} node_{lease.worker_id}"
                )
            else:
                self._update_job_locked(
                    job.job_id, status=JobStatus.FAILED, attempt=next_attempt
                )
                self.plan_runner.event(
                    f"FAILED {job.job_id} {job.action.value} {job.family} {job.name} "
                    f"status_{status} oom_{1 if payload.get('oom') else 0} node_{lease.worker_id}"
                )
        self._drop_lease_locked(lease)

    def _drop_lease_locked(self, lease: Lease) -> None:
        self.leases.pop(lease.token, None)
        if self.lease_by_job.get(lease.job_id) == lease.token:
            self.lease_by_job.pop(lease.job_id, None)

    def _teardown_ack(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            worker = self._validate_worker(payload)
            job_id = str(payload.get("job_id") or "")
            if job_id != self.teardown_job:
                return {"accepted": False, "reason": "stale_teardown"}
            self.teardown_pending.discard(worker.node_id)
            self.teardown_acked.add(worker.node_id)
            worker.gpus = {
                gpu_id: GpuSnapshot(
                    gpu_id=snapshot.gpu_id,
                    free_mib=snapshot.free_mib,
                    used_mib=snapshot.used_mib,
                    total_mib=snapshot.total_mib,
                    utilization=snapshot.utilization,
                )
                for gpu_id, snapshot in worker.gpus.items()
            }
            self.event(f"TEARDOWN_ACK job_{job_id} node_{worker.node_id}")
            self._finish_teardown_if_ready_locked()
            self._write_snapshot_locked()
        return {"accepted": True}

    def _worker_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            worker = self._validate_worker(payload)
            message = str(payload.get("message") or "").replace("\n", " ")[:2000]
            self.event(f"WORKER_EVENT node_{worker.node_id} {message}")
        return {"ok": True}

    def _read_jobs_locked(self) -> list[Job]:
        with PlanLock(self.plan_dir, exclusive=False):
            return read_plan(self.plan_file)

    def _claim_job_locked(self, job_id: str) -> Job | None:
        with PlanLock(self.plan_dir, exclusive=True):
            jobs = read_plan(self.plan_file)
            claimed = None
            output = []
            for job in jobs:
                if (
                    job.job_id == job_id
                    and job.status == JobStatus.PENDING
                    and dependencies_satisfied(job, jobs)
                ):
                    job = job.with_updates(status=JobStatus.RUNNING)
                    claimed = job
                output.append(job)
            if claimed is not None:
                write_plan(self.plan_file, output)
            return claimed

    def _update_job_locked(self, job_id: str, **updates: object) -> Job:
        with PlanLock(self.plan_dir, exclusive=True):
            jobs = read_plan(self.plan_file)
            output = []
            updated = None
            for job in jobs:
                if job.job_id == job_id:
                    job = job.with_updates(**updates)
                    updated = job
                output.append(job)
            if updated is None:
                raise SchedulerError(f"missing job: {job_id}")
            write_plan(self.plan_file, output)
            return updated

    def _fence_worker_locked(self, worker: WorkerInfo, *, reason: str) -> None:
        for lease in list(self.leases.values()):
            if lease.worker_id != worker.node_id or lease.worker_boot_id != worker.boot_id:
                continue
            jobs = self._read_jobs_locked()
            job = next((item for item in jobs if item.job_id == lease.job_id), None)
            if job is not None and job.status == JobStatus.RUNNING:
                next_attempt = job.attempt + 1
                if next_attempt <= job.max_retries:
                    self._update_job_locked(job.job_id, status=JobStatus.PENDING, attempt=next_attempt)
                else:
                    self._update_job_locked(job.job_id, status=JobStatus.FAILED, attempt=next_attempt)
            self._drop_lease_locked(lease)
            self.event(
                f"LEASE_FENCED node_{worker.node_id} boot_{worker.boot_id} "
                f"job_{lease.job_id} lease_{lease.token} reason_{reason}"
            )

    def _expire_workers_locked(self) -> None:
        cutoff = time.time() - self.worker_ttl
        for worker in list(self.workers.values()):
            if worker.last_heartbeat >= cutoff:
                continue
            if any(lease.worker_id == worker.node_id for lease in self.leases.values()):
                self._fence_worker_locked(worker, reason="heartbeat_timeout")

    def _start_teardown_locked(self, job: Job) -> None:
        claimed = self._claim_job_locked(job.job_id)
        if claimed is None:
            return
        fresh = {
            worker.node_id
            for worker in self.workers.values()
            if worker.fresh_age <= self.worker_ttl
        }
        self.teardown_job = claimed.job_id
        self.teardown_pending = set(fresh)
        self.teardown_acked = set()
        self.mode = "draining"
        self.plan_runner.event(
            "START "
            f"{claimed.job_id} {claimed.action.value} {claimed.family} {claimed.name} "
            f"shard_-_of_- gpu_- attempt_{claimed.attempt + 1}_of_{claimed.max_retries + 1} "
            "batch_- mem_free_before_NA node_cluster"
        )
        self._finish_teardown_if_ready_locked()

    def _finish_teardown_if_ready_locked(self) -> None:
        if not self.teardown_job or self.teardown_pending or self.leases:
            return
        job_id = self.teardown_job
        jobs = self._read_jobs_locked()
        job = next((item for item in jobs if item.job_id == job_id), None)
        if job is not None:
            self._update_job_locked(job_id, status=JobStatus.DONE)
            self.plan_runner.event(
                f"END {job.job_id} {job.action.value} {job.family} {job.name} status_0 node_cluster"
            )
        else:
            self.event(f"IMPLICIT_TEARDOWN_END job_{job_id}")
        self.teardown_job = None
        self.teardown_pending.clear()
        self.teardown_acked.clear()
        self.mode = "evaluating"

    def _run_control(self, job: Job) -> tuple[str, int]:
        return self.plan_runner.run_one(job, None, ())

    def _multinode_training_job(self, job: Job) -> Job:
        hostfile = str(job.metadata.get("multinode_hostfile") or "")
        if not hostfile:
            return job
        raw_command = job.metadata.get("command")
        if isinstance(raw_command, str):
            raw_argv = shlex.split(raw_command)
        elif isinstance(raw_command, list) and all(isinstance(part, str) for part in raw_command):
            raw_argv = list(raw_command)
        else:
            raise SchedulerError("multi-node training requires metadata.command")
        command_environment, argv = split_command_environment(raw_argv)
        if any(Path(part).name == "launch_multinode_torchrun.py" for part in argv):
            return job
        try:
            app_index = next(
                index for index, part in enumerate(argv) if Path(part).name == "pretrain.py"
            )
        except StopIteration as exc:
            raise SchedulerError("could not find pretrain.py in the training command") from exc
        app_command = argv[app_index:]
        python_env = str(
            job.metadata.get("multinode_python_env")
            or job.metadata.get("python_env")
            or Path(sys.executable).parent.parent
        )
        workdir = str(job.metadata.get("workdir") or self.plan_dir.parent.parent)
        launcher = [
            str(Path(python_env) / "bin/python"),
            "scripts/launch_multinode_torchrun.py",
            "--hostfile",
            hostfile,
            "--workdir",
            workdir,
            "--python-env",
            python_env,
            "--master-port",
            str(job.metadata.get("multinode_master_port", 29500)),
            "--nproc-per-node",
            str(job.metadata.get("multinode_nproc_per_node", 8)),
            "--log-dir",
            str(job.metadata.get("multinode_log_dir", "logs/multinode")),
        ]
        nccl_interface = str(job.metadata.get("multinode_nccl_interface") or "")
        if nccl_interface:
            launcher.extend(["--nccl-interface", nccl_interface])
        for path in job.metadata.get("multinode_required_paths", []) or []:
            launcher.extend(["--required-path", str(path)])
        remote_environment = {
            **command_environment,
            **{
                str(key): str(value)
                for key, value in (job.metadata.get("multinode_environment") or {}).items()
            },
        }
        for key, value in sorted(remote_environment.items()):
            launcher.extend(["--env", f"{key}={value}"])
        if job.metadata.get("multinode_skip_preflight"):
            launcher.append("--skip-preflight")
        if job.metadata.get("multinode_skip_nccl_smoke"):
            launcher.append("--skip-nccl-smoke")
        launcher.extend(["--", *app_command])
        metadata = dict(job.metadata)
        metadata["command"] = launcher
        return job.with_updates(metadata=metadata)

    def _run_training(self, job: Job) -> tuple[str, int]:
        job = self._multinode_training_job(job)
        local_gpu_count = max((len(worker.gpus) for worker in self.workers.values()), default=8)
        return self.plan_runner.run_one(job, 0, tuple(range(local_gpu_count)))

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def _adopt_training(self, job: Job, pid: int) -> tuple[str, int]:
        self.event(f"TRAIN_ADOPT job_{job.job_id} pid_{pid}")
        while self._pid_alive(pid):
            time.sleep(5)
        target_step = int(job.metadata["stop_after_step"])
        ready, reason = training_checkpoint_ready(job, target_step)
        with self.lock:
            current = next(
                (item for item in self._read_jobs_locked() if item.job_id == job.job_id),
                None,
            )
            if current is None or current.status != JobStatus.RUNNING:
                return job.job_id, 0
            if ready:
                self._update_job_locked(job.job_id, status=JobStatus.DONE)
                self.plan_runner.event(
                    f"END {job.job_id} {job.action.value} {job.family} {job.name} "
                    "status_0 node_cluster adopted_1"
                )
                return job.job_id, 0
            next_attempt = current.attempt + 1
            if next_attempt <= current.max_retries:
                self._update_job_locked(
                    job.job_id, status=JobStatus.PENDING, attempt=next_attempt
                )
            else:
                self._update_job_locked(
                    job.job_id, status=JobStatus.FAILED, attempt=next_attempt
                )
            self.event(f"TRAIN_ADOPT_FAILED job_{job.job_id} reason_{reason}")
        return job.job_id, 4

    def _reconcile_running_jobs_locked(self) -> None:
        for job in self._read_jobs_locked():
            if job.status != JobStatus.RUNNING:
                continue
            if job.resolved_execution_scope == ExecutionScope.GPU:
                if job.job_id not in self.lease_by_job:
                    next_attempt = job.attempt + 1
                    if next_attempt <= job.max_retries:
                        self._update_job_locked(
                            job.job_id, status=JobStatus.PENDING, attempt=next_attempt
                        )
                    else:
                        self._update_job_locked(
                            job.job_id, status=JobStatus.FAILED, attempt=next_attempt
                        )
                continue
            if job.resolved_execution_scope != ExecutionScope.CLUSTER:
                # Controller-only jobs are idempotent and safe to retry after a
                # coordinator restart.
                self._update_job_locked(job.job_id, status=JobStatus.PENDING)
                continue
            target = int(job.metadata.get("stop_after_step") or 0)
            process_path = Path(job.log_dir) / f"train_until_step_{target}.process.json"
            try:
                process_state = json.loads(process_path.read_text())
                pid = int(process_state["pid"])
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                pid = -1
            if pid > 0 and self._pid_alive(pid):
                self.mode = "training"
                future = self.control_pool.submit(self._adopt_training, job, pid)
                self.control_futures[future] = job.job_id
                continue
            ready, _reason = training_checkpoint_ready(job, target)
            if ready:
                self._update_job_locked(job.job_id, status=JobStatus.DONE)
            else:
                self._update_job_locked(job.job_id, status=JobStatus.PENDING)

    def _reap_control_locked(self) -> None:
        completed = [future for future in self.control_futures if future.done()]
        for future in completed:
            job_id = self.control_futures.pop(future)
            try:
                future.result()
            except BaseException as exc:  # noqa: BLE001 - contain control-thread failure
                self._update_job_locked(job_id, status=JobStatus.FAILED)
                self.event(f"CONTROL_EXCEPTION job_{job_id} {type(exc).__name__}_{exc}")
            if self.mode == "training":
                self.mode = "evaluating"

    def _schedule_control_locked(self) -> None:
        jobs = self._read_jobs_locked()
        jobs_by_id = {job.job_id: job for job in jobs}
        ready = [
            job
            for job in jobs
            if job.status == JobStatus.PENDING and dependencies_satisfied(job, jobs)
        ]
        if self.teardown_job:
            self._finish_teardown_if_ready_locked()
            return
        for job in ready:
            scope = job.resolved_execution_scope
            if job.action.value == "teardown_eval":
                self._start_teardown_locked(job)
                return
            if scope == ExecutionScope.CLUSTER:
                blocking_control_jobs = {
                    job_id
                    for job_id in self.control_futures.values()
                    if job_id not in jobs_by_id
                    or jobs_by_id[job_id].action != Action.WAIT_CHECKPOINT
                }
                if self.leases or blocking_control_jobs:
                    self.mode = "draining"
                    return
                fresh_workers = [
                    worker
                    for worker in self.workers.values()
                    if worker.fresh_age <= self.worker_ttl
                ]
                if self.expected_nodes and len(fresh_workers) < self.expected_nodes:
                    return
                if any(worker.active_leases for worker in fresh_workers):
                    self.mode = "draining"
                    return
                workers_with_servers = {
                    worker.node_id
                    for worker in fresh_workers
                    if any(snapshot.server_key for snapshot in worker.gpus.values())
                }
                if workers_with_servers:
                    self.teardown_job = f"__before__{job.job_id}"
                    self.teardown_pending = workers_with_servers
                    self.teardown_acked = set()
                    self.mode = "draining"
                    self.event(
                        f"IMPLICIT_TEARDOWN_START job_{job.job_id} "
                        f"nodes_{','.join(sorted(workers_with_servers))}"
                    )
                    return
                claimed = self._claim_job_locked(job.job_id)
                if claimed is None:
                    continue
                self.mode = "training"
                future = self.control_pool.submit(self._run_training, claimed)
                self.control_futures[future] = claimed.job_id
                return
            if scope != ExecutionScope.CONTROL:
                continue
            if len(self.control_futures) >= 12:
                return
            claimed = self._claim_job_locked(job.job_id)
            if claimed is None:
                continue
            future = self.control_pool.submit(self._run_control, claimed)
            self.control_futures[future] = claimed.job_id

    def _write_snapshot_locked(self) -> None:
        atomic_json(self.plan_dir / CLUSTER_SNAPSHOT, self._snapshot_locked())

    def _snapshot_locked(self) -> dict[str, Any]:
        jobs = self._read_jobs_locked()
        counts = {status.value: 0 for status in JobStatus}
        for job in jobs:
            counts[job.status.value] += 1
        ready = [
            job.job_id
            for job in jobs
            if job.status == JobStatus.PENDING and dependencies_satisfied(job, jobs)
        ]
        return {
            "version": 1,
            "updated_at": time.time(),
            "coordinator_pid": os.getpid(),
            "coordinator_host": socket.gethostname(),
            "mode": self.mode,
            "started_at": self.started_at,
            "worker_ttl": self.worker_ttl,
            "expected_nodes": self.expected_nodes,
            "counts": counts,
            "ready": ready,
            "workers": {key: value.to_wire() for key, value in sorted(self.workers.items())},
            "leases": {key: value.to_wire() for key, value in self.leases.items()},
            "control_jobs": sorted(self.control_futures.values()),
            "teardown_job": self.teardown_job,
            "teardown_pending": sorted(self.teardown_pending),
        }

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return self._snapshot_locked()

    def run(self) -> None:
        self.server, self.server_thread = start_cluster_server(
            self, host=self.bind_host, port=self.port, token=self.token
        )
        self.event(
            f"COORDINATOR_START host_{self.bind_host} port_{self.port} pid_{os.getpid()}"
        )
        with self.lock:
            self._reconcile_running_jobs_locked()
        try:
            while not self.stop_event.wait(1.0):
                with self.lock:
                    self._expire_workers_locked()
                    self._reap_control_locked()
                    if stop_requested(self.plan_dir):
                        self.mode = "stopped"
                    elif self.mode == "stopped":
                        self.mode = "evaluating"
                    if self.mode != "stopped":
                        self._schedule_control_locked()
                    self._write_snapshot_locked()
                    should_stop = (
                        self.mode == "stopped"
                        and not self.leases
                        and not self.control_futures
                    )
                if should_stop:
                    break
                jobs = self._read_jobs_locked()
                if not [
                    job
                    for job in jobs
                    if job.status in {JobStatus.PENDING, JobStatus.RUNNING}
                ]:
                    break
        finally:
            with self.lock:
                self.mode = "stopped"
                self._write_snapshot_locked()
            if self.server is not None:
                self.server.shutdown()
                self.server.server_close()
            self.control_pool.shutdown(wait=True)
            self.event("COORDINATOR_END")


class ClusterWorker:
    """Node-local GPU executor with a persistent vLLM pool."""

    def __init__(
        self,
        *,
        coordinator_url: str,
        token: str,
        plan_dir: Path,
        node_id: str,
        gpus: list[int],
        workdir: Path,
        environment: str,
        persistent_vllm: bool,
        poll_interval: float = 1.0,
        heartbeat_interval: float = 5.0,
    ) -> None:
        self.client = ClusterClient(coordinator_url, token)
        self.plan_dir = plan_dir.resolve()
        self.node_id = node_id
        self.boot_id = uuid.uuid4().hex
        self.gpus = sorted(gpus)
        self.workdir = workdir.resolve()
        self.environment = environment
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval
        self.stop_event = Event()
        self.lock = Lock()
        self.active: dict[str, dict[str, Any]] = {}
        self.threads: dict[str, Thread] = {}
        self.server_pool = (
            VLLMServerPool(self.plan_dir, self._pool_event) if persistent_vllm else None
        )
        self.manifest_path = (
            self.plan_dir / WORKER_MANIFEST_DIR / self.node_id / "worker.json"
        )

    def _identity(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "boot_id": self.boot_id,
            "hostname": socket.gethostname(),
            "capabilities": [Capability.EVAL.value, Capability.EXPORT.value, Capability.TEARDOWN.value],
            "repo_commit": _git_head(self.workdir),
            "python": sys.executable,
            "environment": self.environment,
            "gpus": [asdict(value) for value in _gpu_inventory(self.gpus, self.server_pool).values()],
            "active_leases": sorted(self.active),
        }

    def _pool_event(self, message: str) -> None:
        try:
            self.client.request(
                "/v1/event",
                {"node_id": self.node_id, "boot_id": self.boot_id, "message": message},
            )
        except ClusterProtocolError:
            pass

    def register(self) -> None:
        response = self.client.request("/v1/register", self._identity())
        if not response.get("ok"):
            raise ClusterProtocolError(f"registration rejected: {response}")
        self._write_manifest("registered")

    def _write_manifest(self, state: str) -> None:
        atomic_json(
            self.manifest_path,
            {
                **self._identity(),
                "pid": os.getpid(),
                "state": state,
                "updated_at": time.time(),
            },
        )

    def heartbeat(self) -> dict[str, Any]:
        with self.lock:
            payload = self._identity()
        return self.client.request("/v1/heartbeat", payload)

    def _busy_gpus(self) -> set[int]:
        with self.lock:
            return {int(item["gpu_id"]) for item in self.active.values()}

    def _execute(self, lease: dict[str, Any], job_value: dict[str, Any], gpu_id: int) -> None:
        token = str(lease["token"])
        job = Job.from_wire(job_value)
        free_before, used_before, total_before = gpu_snapshot(gpu_id)
        status = 72
        error = ""
        try:
            status = run_job(job, gpu_id, self.server_pool, (gpu_id,))
        except BaseException as exc:  # noqa: BLE001 - report worker failures to coordinator
            error = f"{type(exc).__name__}: {exc}"
            status = 72
        free_after, used_after, total_after = gpu_snapshot(gpu_id)
        payload = {
            "node_id": self.node_id,
            "boot_id": self.boot_id,
            "lease_token": token,
            "status": status,
            "oom": _job_oom(job),
            "error": error,
            "free_before": free_before,
            "used_before": used_before,
            "total_before": total_before,
            "free_after": free_after,
            "used_after": used_after,
            "total_after": total_after,
        }
        try:
            while not self.stop_event.is_set():
                try:
                    response = self.client.request("/v1/complete", payload)
                    if response.get("accepted") in {True, False}:
                        break
                except ClusterProtocolError:
                    self.stop_event.wait(5)
        finally:
            with self.lock:
                self.active.pop(token, None)
                self.threads.pop(token, None)
            self._write_manifest("running")

    def _accept_assignment(self, response: dict[str, Any]) -> None:
        lease = dict(response["lease"])
        token = str(lease["token"])
        gpu_id = int(response["gpu_id"])
        if gpu_id not in self.gpus:
            raise ClusterProtocolError(f"coordinator assigned unavailable gpu {gpu_id}")
        with self.lock:
            busy_gpus = {int(item["gpu_id"]) for item in self.active.values()}
            if token in self.active or gpu_id in busy_gpus:
                raise ClusterProtocolError(f"duplicate assignment on gpu {gpu_id}")
            self.active[token] = {
                "job_id": lease["job_id"],
                "gpu_id": gpu_id,
                "started_at": time.time(),
            }
            thread = Thread(
                target=self._execute,
                args=(lease, dict(response["job"]), gpu_id),
                name=f"eval-{lease['job_id']}",
                daemon=False,
            )
            self.threads[token] = thread
            thread.start()

    def _teardown(self) -> None:
        if self._busy_gpus():
            return
        if self.server_pool is not None:
            self.server_pool.close_all()
        self.client.request(
            "/v1/teardown-ack",
            {
                "node_id": self.node_id,
                "boot_id": self.boot_id,
                "job_id": self.heartbeat().get("teardown_job", ""),
            },
        )

    def run(self) -> None:
        while not self.stop_event.is_set():
            try:
                self.register()
                break
            except ClusterProtocolError:
                self.stop_event.wait(5)
        last_heartbeat = 0.0
        try:
            while not self.stop_event.is_set():
                try:
                    current = time.monotonic()
                    heartbeat_response: dict[str, Any] = {}
                    if current - last_heartbeat >= self.heartbeat_interval:
                        heartbeat_response = self.heartbeat()
                        last_heartbeat = current
                        command = heartbeat_response.get("command")
                        if command == "teardown" and not self._busy_gpus():
                            if self.server_pool is not None:
                                self.server_pool.close_all()
                            self.client.request(
                                "/v1/teardown-ack",
                                {
                                    "node_id": self.node_id,
                                    "boot_id": self.boot_id,
                                    "job_id": heartbeat_response.get("teardown_job", ""),
                                },
                            )
                        elif command == "stop" and not self._busy_gpus():
                            break
                    if len(self._busy_gpus()) < len(self.gpus):
                        response = self.client.request(
                            "/v1/poll",
                            {"node_id": self.node_id, "boot_id": self.boot_id},
                        )
                        if response.get("command") == "run":
                            self._accept_assignment(response)
                    self._write_manifest("running")
                    self.stop_event.wait(self.poll_interval)
                except ClusterProtocolError:
                    self.stop_event.wait(5)
                    try:
                        self.register()
                    except ClusterProtocolError:
                        continue
        finally:
            self.stop_event.set()
            for thread in list(self.threads.values()):
                thread.join()
            if self.server_pool is not None:
                self.server_pool.close_all()
            self._write_manifest("stopped")


def install_signal_handlers(stop_event: Event) -> None:
    def stop(_signum: int, _frame: object) -> None:
        stop_event.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
