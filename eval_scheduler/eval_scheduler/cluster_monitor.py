from __future__ import annotations

import json
import shutil
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any

from .cluster_runtime import CLUSTER_SNAPSHOT
from .locking import PlanLock
from .model import Action, Job, JobStatus, read_plan
from .monitor import blocked_pending_jobs, fmt_seconds, job_model_label, job_progress
from .plan import plan_path
from .runtime import dependencies_satisfied


def read_cluster_snapshot(plan_dir: Path) -> dict[str, Any]:
    path = plan_dir / CLUSTER_SNAPSHOT
    if not path.exists():
        raise FileNotFoundError(f"cluster snapshot does not exist: {path}")
    return json.loads(path.read_text())


def _jobs(plan_dir: Path) -> list[Job]:
    with PlanLock(plan_dir, exclusive=False):
        return read_plan(plan_path(plan_dir))


def _lease_jobs(snapshot: dict[str, Any], jobs: list[Job]) -> dict[str, tuple[dict[str, Any], Job]]:
    by_id = {job.job_id: job for job in jobs}
    return {
        token: (lease, by_id[lease["job_id"]])
        for token, lease in snapshot.get("leases", {}).items()
        if lease.get("job_id") in by_id
    }


def _active_cluster_training(snapshot: dict[str, Any], jobs: list[Job]) -> Job | None:
    if snapshot.get("mode") != "training":
        return None
    by_id = {job.job_id: job for job in jobs}
    for job_id in snapshot.get("control_jobs", []):
        job = by_id.get(job_id)
        if (
            job is not None
            and job.action == Action.TRAIN_UNTIL_STEP
            and job.status == JobStatus.RUNNING
        ):
            return job
    return None


def _historical_durations(plan_dir: Path) -> dict[str, list[float]]:
    starts: dict[str, float] = {}
    durations: dict[str, list[float]] = defaultdict(list)
    path = plan_dir / "status.tsv"
    if not path.exists():
        return durations
    for raw in path.read_text(errors="replace").splitlines():
        if "\t" not in raw:
            continue
        timestamp, message = raw.split("\t", 1)
        try:
            moment = datetime.fromisoformat(timestamp).timestamp()
        except ValueError:
            continue
        parts = message.split()
        if parts and parts[0] == "CLUSTER":
            parts = parts[1:]
        if len(parts) >= 2 and parts[0] == "START":
            starts[parts[1]] = moment
        elif len(parts) >= 2 and parts[0] == "END":
            started = starts.pop(parts[1], None)
            if started is not None and moment >= started:
                durations[parts[1]].append(moment - started)
    return durations


def global_eta(plan_dir: Path, snapshot: dict[str, Any], jobs: list[Job]) -> float | None:
    lease_jobs = _lease_jobs(snapshot, jobs)
    active_etas = []
    rate_by_key: dict[tuple[str, str], list[float]] = defaultdict(list)
    for lease, job in lease_jobs.values():
        progress = job_progress(job)
        elapsed = max(0.0, time.time() - float(lease.get("issued_at", time.time())))
        if progress.eta_seconds is not None:
            active_etas.append(progress.eta_seconds)
        elif progress.fraction and progress.fraction > 0:
            active_etas.append(elapsed * (1 - progress.fraction) / progress.fraction)
        if progress.fraction and progress.fraction > 0 and elapsed > 0:
            rate_by_key[(job.family, job.name)].append(elapsed / progress.fraction)
    history = _historical_durations(plan_dir)
    ready_or_pending = [job for job in jobs if job.status == JobStatus.PENDING]
    estimated_work = 0.0
    known = 0
    for job in ready_or_pending:
        rates = rate_by_key.get((job.family, job.name), [])
        if rates:
            estimated_work += median(rates)
            known += 1
        elif history.get(job.job_id):
            estimated_work += median(history[job.job_id])
            known += 1
    gpu_count = sum(len(worker.get("gpus", {})) for worker in snapshot.get("workers", {}).values())
    if not active_etas and not known:
        return None
    return max(active_etas, default=0.0) + estimated_work / max(1, gpu_count)


def cluster_status_text(plan_dir: Path) -> str:
    snapshot = read_cluster_snapshot(plan_dir)
    jobs = _jobs(plan_dir)
    cluster_training = _active_cluster_training(snapshot, jobs)
    lease_jobs = _lease_jobs(snapshot, jobs)
    by_resource: dict[tuple[str, int], tuple[dict[str, Any], Job]] = {}
    for lease, job in lease_jobs.values():
        for resource in lease.get("resources", []):
            by_resource[(str(resource["node_id"]), int(resource["gpu_id"]))] = (lease, job)
    age = max(0.0, time.time() - float(snapshot.get("updated_at", 0)))
    counts = Counter(job.status for job in jobs)
    lines = [
        (
            f"mode={snapshot.get('mode')} snapshot_age={age:.1f}s "
            f"workers={len(snapshot.get('workers', {}))}/{snapshot.get('expected_nodes') or '?'} "
            f"done={counts[JobStatus.DONE]} running={counts[JobStatus.RUNNING]} "
            f"pending={counts[JobStatus.PENDING]} failed={counts[JobStatus.FAILED]} "
            f"global_eta={fmt_seconds(global_eta(plan_dir, snapshot, jobs))}"
        ),
    ]
    ttl = float(snapshot.get("worker_ttl", 30))
    for node_id, worker in sorted(snapshot.get("workers", {}).items()):
        worker_age = max(0.0, time.time() - float(worker.get("last_heartbeat", 0)))
        state = "STALE" if worker_age > ttl else "ok"
        for gpu_text, gpu in sorted(worker.get("gpus", {}).items(), key=lambda item: int(item[0])):
            gpu_id = int(gpu_text)
            active = by_resource.get((node_id, gpu_id))
            prefix = (
                f"{node_id}/GPU{gpu_id}: used={gpu.get('used_mib')}MiB "
                f"free={gpu.get('free_mib')}MiB util={gpu.get('utilization')}% "
                f"worker={state}/{worker_age:.0f}s"
            )
            if active is None:
                if cluster_training is not None:
                    progress = job_progress(cluster_training)
                    lines.append(
                        prefix
                        + f" {cluster_training.job_id} "
                        + f"{cluster_training.family}:{cluster_training.name} "
                        + f"{progress.text} ETA={fmt_seconds(progress.eta_seconds)}"
                    )
                    continue
                server = f" server={gpu.get('server_key')}" if gpu.get("server_key") else ""
                lines.append(prefix + " idle" + server)
                continue
            lease, job = active
            progress = job_progress(job)
            elapsed = max(0.0, time.time() - float(lease.get("issued_at", time.time())))
            eta = progress.eta_seconds
            if eta is None and progress.fraction and progress.fraction > 0:
                eta = elapsed * (1 - progress.fraction) / progress.fraction
            lines.append(
                prefix
                + f" {job.job_id} {job_model_label(job)} {job.family}:{job.name} "
                + f"shard={job.shard}/{job.shards} batch={job.retry_batch()} "
                + f"{progress.text} ETA={fmt_seconds(eta)}"
            )
    control = snapshot.get("control_jobs", [])
    if control:
        for job_id in control:
            job = next((item for item in jobs if item.job_id == job_id), None)
            if job is None or job is cluster_training:
                continue
            progress = job_progress(job)
            lines.append(
                f"control: {job_id} {job.action.value} {progress.text} "
                f"ETA={fmt_seconds(progress.eta_seconds)}"
            )
    return "\n".join(lines)


def cluster_rich_renderable(plan_dir: Path) -> Any:
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table

    snapshot = read_cluster_snapshot(plan_dir)
    jobs = _jobs(plan_dir)
    by_id = {job.job_id: job for job in jobs}
    cluster_training = _active_cluster_training(snapshot, jobs)
    lease_jobs = _lease_jobs(snapshot, jobs)
    by_resource: dict[tuple[str, int], tuple[dict[str, Any], Job]] = {}
    for lease, job in lease_jobs.values():
        for resource in lease.get("resources", []):
            by_resource[(str(resource["node_id"]), int(resource["gpu_id"]))] = (lease, job)
    counts = Counter(job.status for job in jobs)
    age = max(0.0, time.time() - float(snapshot.get("updated_at", 0)))
    header = Panel(
        f"mode={snapshot.get('mode')}  snapshot={age:.1f}s old  "
        f"workers={len(snapshot.get('workers', {}))}/{snapshot.get('expected_nodes') or '?'}  "
        f"done={counts[JobStatus.DONE]} running={counts[JobStatus.RUNNING]} "
        f"pending={counts[JobStatus.PENDING]} failed={counts[JobStatus.FAILED]}  "
        f"ETA={fmt_seconds(global_eta(plan_dir, snapshot, jobs))}",
        title="Multi-node eval scheduler",
    )
    table = Table(expand=True)
    table.add_column("Resource", no_wrap=True)
    table.add_column("Memory", no_wrap=True)
    table.add_column("Util", no_wrap=True)
    table.add_column("Task", overflow="ellipsis")
    table.add_column("Progress", overflow="ellipsis")
    table.add_column("ETA", no_wrap=True)
    ttl = float(snapshot.get("worker_ttl", 30))
    for node_id, worker in sorted(snapshot.get("workers", {}).items()):
        worker_age = max(0.0, time.time() - float(worker.get("last_heartbeat", 0)))
        stale = worker_age > ttl
        for gpu_text, gpu in sorted(worker.get("gpus", {}).items(), key=lambda item: int(item[0])):
            gpu_id = int(gpu_text)
            resource = f"{node_id}/GPU{gpu_id}" + (" STALE" if stale else "")
            total = gpu.get("total_mib")
            used = gpu.get("used_mib")
            memory = "?" if total is None or used is None else f"{used / 1024:.1f}/{total / 1024:.1f} GiB"
            active = by_resource.get((node_id, gpu_id))
            if active is None:
                if cluster_training is not None:
                    progress = job_progress(cluster_training)
                    table.add_row(
                        resource,
                        memory,
                        f"{gpu.get('utilization')}%",
                        f"{cluster_training.family}:{cluster_training.name}",
                        progress.text,
                        fmt_seconds(progress.eta_seconds),
                    )
                    continue
                server = str(gpu.get("server_key") or "")
                table.add_row(resource, memory, f"{gpu.get('utilization')}%", "idle", server, "")
                continue
            lease, job = active
            progress = job_progress(job)
            elapsed = max(0.0, time.time() - float(lease.get("issued_at", time.time())))
            eta = progress.eta_seconds
            if eta is None and progress.fraction and progress.fraction > 0:
                eta = elapsed * (1 - progress.fraction) / progress.fraction
            shard = f" {job.shard}/{job.shards}" if job.shard is not None else ""
            table.add_row(
                resource,
                memory,
                f"{gpu.get('utilization')}%",
                f"{job_model_label(job)} {job.family}:{job.name}{shard}",
                progress.text,
                fmt_seconds(eta),
            )
    for job_id in snapshot.get("control_jobs", []):
        job = by_id.get(job_id)
        if job is None or job is cluster_training:
            continue
        progress = job_progress(job)
        lane = "CLUSTER" if job.resolved_execution_scope.value == "cluster" else "CPU"
        table.add_row(
            lane,
            "-",
            "-",
            f"{job.action.value} {job_model_label(job)} {job.family}:{job.name}",
            progress.text,
            fmt_seconds(progress.eta_seconds),
        )
    terminal = shutil.get_terminal_size((160, 50))
    remaining_rows = max(3, terminal.lines - len(table.rows) - 9)
    ready = [
        job for job in jobs
        if job.status == JobStatus.PENDING and dependencies_satisfied(job, jobs)
    ]
    blocked = blocked_pending_jobs(jobs)
    queue = Table(title="Ready / blocked", expand=True)
    queue.add_column("State", width=8)
    queue.add_column("Job")
    queue.add_column("Task")
    queue.add_column("Details")
    shown = 0
    for job in ready[:remaining_rows]:
        queue.add_row("ready", job.job_id, f"{job.family}:{job.name}", f"{job.action.value} batch={job.retry_batch()}")
        shown += 1
    for job, unmet in blocked[: max(0, remaining_rows - shown)]:
        queue.add_row("blocked", job.job_id, f"{job.family}:{job.name}", ", ".join(unmet[:4]))
        shown += 1
    hidden = len(ready) + len(blocked) - shown
    if hidden > 0:
        queue.add_row("", f"... {hidden} more", "", "")
    return Group(header, table, queue)


def cluster_watch(plan_dir: Path, *, interval: float, rich: bool) -> None:
    if rich:
        from rich.live import Live

        with Live(cluster_rich_renderable(plan_dir), refresh_per_second=4, screen=True) as live:
            while True:
                time.sleep(interval)
                live.update(cluster_rich_renderable(plan_dir))
    else:
        while True:
            print(cluster_status_text(plan_dir), flush=True)
            time.sleep(interval)
