from __future__ import annotations

import concurrent.futures
import json
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cluster_protocol import atomic_json

SSH_OPTIONS = (
    "-o",
    "BatchMode=yes",
    "-o",
    "ConnectTimeout=15",
    "-o",
    "ServerAliveInterval=30",
    "-o",
    "ServerAliveCountMax=3",
)


@dataclass(frozen=True)
class WorkerLaunch:
    node_id: str
    host: str
    pid: int
    log_path: str
    started_at: float


def parse_hostfile(path: Path) -> list[str]:
    hosts = []
    for raw in path.read_text().splitlines():
        host = raw.split("#", 1)[0].strip()
        if host:
            hosts.append(host)
    if not hosts:
        raise ValueError(f"hostfile is empty: {path}")
    if len(set(hosts)) != len(hosts):
        raise ValueError(f"hostfile contains duplicate hosts: {path}")
    return hosts


def ssh_command(host: str, command: str) -> list[str]:
    return ["ssh", *SSH_OPTIONS, host, "bash", "-lc", shlex.quote(command)]


def _run_ssh(host: str, command: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ssh_command(host, command),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def launch_workers(
    *,
    hostfile: Path,
    coordinator_url: str,
    token_path: Path,
    plan_dir: Path,
    workdir: Path,
    python_env: Path,
    gpus: str,
    persistent_vllm: bool,
    ssh_timeout: int = 60,
) -> list[WorkerLaunch]:
    hosts = parse_hostfile(hostfile)
    token_path = token_path.resolve()
    plan_dir = plan_dir.resolve()
    workdir = workdir.resolve()
    python_env = python_env.resolve()
    launch_dir = plan_dir / "cluster-workers"
    launch_dir.mkdir(parents=True, exist_ok=True)

    def launch(index_host: tuple[int, str]) -> WorkerLaunch:
        index, host = index_host
        node_id = f"node-{index:02d}"
        log_path = launch_dir / node_id / "worker.log"
        pid_path = launch_dir / node_id / "worker.pid"
        remote = (
            "set -euo pipefail; "
            f"test -d {shlex.quote(str(workdir))}; "
            f"test -x {shlex.quote(str(python_env / 'bin/python'))}; "
            f"test -r {shlex.quote(str(token_path))}; "
            f"mkdir -p {shlex.quote(str(log_path.parent))}; "
            f"cd {shlex.quote(str(workdir))}; "
            "export PYTHONUNBUFFERED=1; "
            f"export PATH={shlex.quote(str(python_env / 'bin'))}:$PATH; "
            "setsid "
            f"{shlex.quote(str(python_env / 'bin/python'))} -m eval_scheduler cluster worker "
            f"--coordinator-url {shlex.quote(coordinator_url)} "
            f"--token-file {shlex.quote(str(token_path))} "
            f"--plan-dir {shlex.quote(str(plan_dir))} "
            f"--node-id {shlex.quote(node_id)} "
            f"--gpus {shlex.quote(gpus)} "
            f"--workdir {shlex.quote(str(workdir))} "
            f"--environment {shlex.quote(str(python_env))} "
            + ("--persistent-vllm " if persistent_vllm else "--no-persistent-vllm ")
            + f">> {shlex.quote(str(log_path))} 2>&1 < /dev/null & "
            "pid=$!; "
            f"printf '%s\\n' \"$pid\" > {shlex.quote(str(pid_path))}; "
            "sleep 1; kill -0 \"$pid\"; printf '%s\\n' \"$pid\""
        )
        result = _run_ssh(host, remote, timeout=ssh_timeout)
        if result.returncode:
            raise RuntimeError(
                f"worker launch failed on {host} ({result.returncode}):\n{result.stdout}"
            )
        try:
            pid = int(result.stdout.strip().splitlines()[-1])
        except (IndexError, ValueError) as exc:
            raise RuntimeError(f"invalid worker PID from {host}: {result.stdout!r}") from exc
        return WorkerLaunch(node_id, host, pid, str(log_path), time.time())

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(hosts)) as pool:
        futures = [pool.submit(launch, item) for item in enumerate(hosts)]
        launches = [future.result() for future in futures]
    manifest = {
        "version": 1,
        "created_at": time.time(),
        "coordinator_url": coordinator_url,
        "hostfile": str(hostfile.resolve()),
        "workers": [launch.__dict__ for launch in launches],
    }
    atomic_json(launch_dir / "launch.json", manifest)
    return launches


def stop_workers(plan_dir: Path, *, force: bool = False, ssh_timeout: int = 60) -> list[str]:
    manifest_path = plan_dir.resolve() / "cluster-workers" / "launch.json"
    manifest: dict[str, Any] = json.loads(manifest_path.read_text())
    stopped: list[str] = []

    def stop(value: dict[str, Any]) -> str:
        host = str(value["host"])
        pid = int(value["pid"])
        signal_name = "KILL" if force else "TERM"
        # Workers are launched under setsid; kill only that recorded process group.
        command = f"kill -{signal_name} -- -{pid} 2>/dev/null || true"
        result = _run_ssh(host, command, timeout=ssh_timeout)
        if result.returncode:
            raise RuntimeError(f"failed to stop worker {host}:{pid}: {result.stdout}")
        return f"{host}:{pid}"

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(manifest["workers"])) as pool:
        stopped = list(pool.map(stop, manifest["workers"]))
    return stopped
