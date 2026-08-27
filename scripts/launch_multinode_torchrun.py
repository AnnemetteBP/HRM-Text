#!/usr/bin/env python3
"""Launch a fixed-membership multi-node TorchRun job over SSH."""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import datetime as dt
import json
import os
import shlex
import subprocess
import time
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any

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


@dataclasses.dataclass
class NodeProcess:
    rank: int
    host: str
    process: subprocess.Popen[str]
    log_handle: Any
    log_path: Path
    pid_path: Path


def parse_hostfile(path: Path) -> list[str]:
    hosts: list[str] = []
    for raw in path.read_text().splitlines():
        host = raw.split("#", 1)[0].strip()
        if host:
            hosts.append(host)
    if not hosts:
        raise ValueError(f"Host file is empty: {path}")
    if len(set(hosts)) != len(hosts):
        raise ValueError(
            "Host file contains duplicate hosts; node ranks must be unique"
        )
    return hosts


def shell_join(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def ssh_command(host: str, remote_command: str) -> list[str]:
    return ["ssh", *SSH_OPTIONS, host, "bash", "-lc", shlex.quote(remote_command)]


def run_ssh(
    host: str, remote_command: str, *, timeout: int = 60
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ssh_command(host, remote_command),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def preflight_script(args: argparse.Namespace, expected_gpus: int) -> str:
    required = [args.workdir, args.python_env, *args.required_path]
    python = f"{args.python_env}/bin/python"
    checks = "\n".join(
        f"test -e {shlex.quote(path)} || {{ echo 'missing required path: {path}' >&2; exit 20; }}"
        for path in required
    )
    probe = r"""
import datetime, importlib, importlib.metadata, json, os, pathlib, socket, subprocess, time
import torch

def module_version(name):
    try:
        module = importlib.import_module(name)
        return {
            "path": getattr(module, "__file__", None),
            "version": getattr(module, "__version__", None),
        }
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}

def distribution_identity(name):
    try:
        distribution = importlib.metadata.distribution(name)
        direct_url_path = pathlib.Path(distribution._path) / "direct_url.json"
        return {
            "version": distribution.version,
            "direct_url": json.loads(direct_url_path.read_text()) if direct_url_path.exists() else None,
        }
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}

payload = {
    "hostname": socket.gethostname(),
    "addresses": sorted({item[4][0] for item in socket.getaddrinfo(socket.gethostname(), None)}),
    "unix_time": time.time(),
    "utc_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "python": os.sys.executable,
    "torch": torch.__version__,
    "torch_cuda": torch.version.cuda,
    "cuda_available": torch.cuda.is_available(),
    "gpu_count": torch.cuda.device_count(),
    "gpu_names": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
    "flash_attn_cute": module_version("flash_attn.cute"),
    "flash_attn_4_distribution": distribution_identity("flash-attn-4"),
    "network_interfaces": sorted(name for _, name in socket.if_nameindex()),
    "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
}
print(json.dumps(payload, sort_keys=True))
"""
    return (
        "set -euo pipefail\n"
        f"cd {shlex.quote(args.workdir)}\n"
        f"{checks}\n"
        f"test -x {shlex.quote(python)} || {{ echo 'missing Python: {python}' >&2; exit 21; }}\n"
        f"{shlex.quote(python)} - <<'PY'\n{probe}\nPY\n"
        f"test $({shlex.quote(python)} -c 'import torch; print(torch.cuda.device_count())') -eq {expected_gpus}"
    )


def run_preflight(hosts: list[str], args: argparse.Namespace) -> list[dict[str, Any]]:
    script = preflight_script(args, args.nproc_per_node)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(hosts)) as pool:
        futures = {
            pool.submit(run_ssh, host, script, timeout=args.ssh_timeout): host
            for host in hosts
        }
        raw = [(host, future.result()) for future, host in futures.items()]

    probes: list[dict[str, Any]] = []
    errors: list[str] = []
    for host, result in raw:
        if result.returncode:
            errors.append(
                f"{host}: preflight exited {result.returncode}\n{result.stdout.rstrip()}"
            )
            continue
        try:
            payload = json.loads(result.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError) as exc:
            errors.append(
                f"{host}: invalid preflight output ({exc})\n{result.stdout.rstrip()}"
            )
            continue
        payload["ssh_host"] = host
        probes.append(payload)
    if errors:
        raise RuntimeError("Preflight failed:\n" + "\n".join(errors))

    reference = probes[0]
    identity_keys = (
        "git_head",
        "torch",
        "torch_cuda",
        "gpu_count",
        "gpu_names",
        "flash_attn_4_distribution",
    )
    for probe in probes[1:]:
        differences = [key for key in identity_keys if probe[key] != reference[key]]
        if differences:
            raise RuntimeError(
                f"Node identity mismatch on {probe['ssh_host']}: "
                + ", ".join(
                    f"{key}={probe[key]!r} != {reference[key]!r}" for key in differences
                )
            )
    if any(not probe["cuda_available"] for probe in probes):
        raise RuntimeError("CUDA is not available on every node")
    if any("error" in probe["flash_attn_cute"] for probe in probes):
        details = {probe["ssh_host"]: probe["flash_attn_cute"] for probe in probes}
        raise RuntimeError(f"FlashAttention 4 import failed: {details}")
    if args.nccl_interface and any(
        args.nccl_interface not in probe["network_interfaces"] for probe in probes
    ):
        missing = [
            probe["ssh_host"]
            for probe in probes
            if args.nccl_interface not in probe["network_interfaces"]
        ]
        raise RuntimeError(
            f"NCCL interface {args.nccl_interface!r} is missing on: {', '.join(missing)}"
        )
    skew = max(probe["unix_time"] for probe in probes) - min(
        probe["unix_time"] for probe in probes
    )
    if skew > args.max_clock_skew:
        raise RuntimeError(
            f"Node clock skew {skew:.3f}s exceeds {args.max_clock_skew:.3f}s"
        )
    return sorted(probes, key=lambda probe: hosts.index(probe["ssh_host"]))


def check_master_port(host: str, master_addr: str, port: int, timeout: int) -> None:
    code = (
        "import socket; "
        f"s=socket.socket(); s.bind(({master_addr!r}, {port})); s.close(); "
        f"print('port {port} available')"
    )
    result = run_ssh(host, f"python3 -c {shlex.quote(code)}", timeout=timeout)
    if result.returncode:
        raise RuntimeError(
            f"Rendezvous port check failed on {host}:\n{result.stdout.rstrip()}"
        )


def remote_agent_command(
    *,
    args: argparse.Namespace,
    host_count: int,
    node_rank: int,
    master_addr: str,
    master_port: int,
    command: Sequence[str],
    pid_path: Path,
) -> str:
    env = dict(item.split("=", 1) for item in args.env)
    if args.nccl_interface:
        env.setdefault("NCCL_SOCKET_IFNAME", args.nccl_interface)
    env_parts = [f"{key}={value}" for key, value in sorted(env.items())]
    torchrun = f"{args.python_env}/bin/torchrun"
    launch = [
        torchrun,
        f"--nnodes={host_count}",
        f"--nproc-per-node={args.nproc_per_node}",
        f"--node-rank={node_rank}",
        f"--master-addr={master_addr}",
        f"--master-port={master_port}",
        *command,
    ]
    return (
        "set -euo pipefail; "
        f"cd {shlex.quote(args.workdir)}; "
        f"mkdir -p {shlex.quote(str(pid_path.parent))}; "
        f"echo $$ > {shlex.quote(str(pid_path))}; "
        f"export PATH={shlex.quote(args.python_env + '/bin')}:$PATH; "
        f"exec env {shell_join(env_parts)} {shell_join(launch)}"
    )


def launch_agents(
    hosts: list[str],
    args: argparse.Namespace,
    command: Sequence[str],
    *,
    master_addr: str,
    master_port: int,
    run_dir: Path,
) -> list[NodeProcess]:
    run_dir.mkdir(parents=True, exist_ok=True)
    nodes: list[NodeProcess] = []
    for rank, host in enumerate(hosts):
        log_path = run_dir / f"node_{rank:02d}_{host.replace('/', '_')}.log"
        pid_path = run_dir / "pids" / f"node_{rank:02d}.pid"
        remote = remote_agent_command(
            args=args,
            host_count=len(hosts),
            node_rank=rank,
            master_addr=master_addr,
            master_port=master_port,
            command=command,
            pid_path=pid_path,
        )
        log_handle = log_path.open("w")
        process = subprocess.Popen(
            ssh_command(host, f"exec setsid bash -lc {shlex.quote(remote)}"),
            text=True,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
        )
        nodes.append(NodeProcess(rank, host, process, log_handle, log_path, pid_path))
    return nodes


def terminate_agents(nodes: Sequence[NodeProcess], timeout: int) -> None:
    active = [node for node in nodes if node.process.poll() is None]
    for node in active:
        remote = (
            f"if test -s {shlex.quote(str(node.pid_path))}; then "
            f"pid=$(cat {shlex.quote(str(node.pid_path))}); kill -TERM -- -$pid 2>/dev/null || true; fi"
        )
        run_ssh(node.host, remote, timeout=30)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and any(
        node.process.poll() is None for node in active
    ):
        time.sleep(0.5)
    for node in active:
        if node.process.poll() is None:
            remote = (
                f"if test -s {shlex.quote(str(node.pid_path))}; then "
                f"pid=$(cat {shlex.quote(str(node.pid_path))}); kill -KILL -- -$pid 2>/dev/null || true; fi"
            )
            run_ssh(node.host, remote, timeout=30)
            node.process.terminate()


def wait_agents(
    nodes: list[NodeProcess],
    manifest: dict[str, Any],
    manifest_path: Path,
    args: argparse.Namespace,
) -> None:
    try:
        while True:
            statuses = [node.process.poll() for node in nodes]
            manifest["node_returncodes"] = {
                node.host: code for node, code in zip(nodes, statuses)
            }
            atomic_json(manifest_path, manifest)
            failures = [code for code in statuses if code not in (None, 0)]
            if failures:
                terminate_agents(nodes, args.terminate_timeout)
                raise RuntimeError(
                    f"A node agent failed; return codes: {manifest['node_returncodes']}"
                )
            if all(code == 0 for code in statuses):
                return
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        terminate_agents(nodes, args.terminate_timeout)
        raise
    finally:
        for node in nodes:
            node.log_handle.close()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hostfile", type=Path, required=True)
    parser.add_argument("--workdir", default="/work/dfm/HRM-Text")
    parser.add_argument("--python-env", default="/home/ucloud/miniforge3/envs/hrm")
    parser.add_argument(
        "--master-addr",
        help="Rendezvous address; defaults to the first preflight hostname",
    )
    parser.add_argument("--master-port", type=int, default=29500)
    parser.add_argument("--nproc-per-node", type=int, default=8)
    parser.add_argument("--log-dir", type=Path, default=Path("logs/multinode"))
    parser.add_argument("--required-path", action="append", default=[])
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--nccl-interface")
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--skip-nccl-smoke", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--ssh-timeout", type=int, default=120)
    parser.add_argument("--max-clock-skew", type=float, default=5.0)
    parser.add_argument("--terminate-timeout", type=int, default=30)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.preflight_only and not args.command:
        parser.error("a training command is required after --")
    for item in args.env:
        if "=" not in item or not item.split("=", 1)[0]:
            parser.error(f"invalid --env value: {item!r}; expected KEY=VALUE")
    if not 1 <= args.master_port <= 65534:
        parser.error("--master-port must be between 1 and 65534")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    hosts = parse_hostfile(args.hostfile)
    run_id = (
        dt.datetime.now(dt.UTC).strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    )
    run_dir = (
        (Path(args.workdir) / args.log_dir / run_id).resolve()
        if not args.log_dir.is_absolute()
        else args.log_dir / run_id
    )
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest_path = run_dir / "manifest.json"
    manifest: dict[str, Any] = {
        "run_id": run_id,
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "hosts": hosts,
        "command": args.command,
        "state": "preflight",
        "run_dir": str(run_dir),
    }
    atomic_json(manifest_path, manifest)

    probes = [] if args.skip_preflight else run_preflight(hosts, args)
    master_addr = args.master_addr or (probes[0]["hostname"] if probes else hosts[0])
    check_master_port(hosts[0], master_addr, args.master_port, args.ssh_timeout)
    manifest.update(
        {
            "preflight": probes,
            "master_addr": master_addr,
            "master_port": args.master_port,
        }
    )
    atomic_json(manifest_path, manifest)
    if args.preflight_only:
        manifest["state"] = "preflight_complete"
        atomic_json(manifest_path, manifest)
        print(f"Preflight passed for {len(hosts)} nodes; manifest: {manifest_path}")
        return 0

    if not args.skip_nccl_smoke:
        smoke_port = args.master_port + 1
        check_master_port(hosts[0], master_addr, smoke_port, args.ssh_timeout)
        manifest["state"] = "nccl_smoke"
        atomic_json(manifest_path, manifest)
        smoke_nodes = launch_agents(
            hosts,
            args,
            ["scripts/multinode_nccl_smoke.py"],
            master_addr=master_addr,
            master_port=smoke_port,
            run_dir=run_dir / "nccl_smoke",
        )
        wait_agents(smoke_nodes, manifest, manifest_path, args)

    manifest["state"] = "running"
    atomic_json(manifest_path, manifest)
    nodes = launch_agents(
        hosts,
        args,
        args.command,
        master_addr=master_addr,
        master_port=args.master_port,
        run_dir=run_dir,
    )
    try:
        wait_agents(nodes, manifest, manifest_path, args)
    except Exception as exc:
        manifest.update(
            {
                "state": "failed",
                "error": str(exc),
                "finished_at": dt.datetime.now(dt.UTC).isoformat(),
            }
        )
        atomic_json(manifest_path, manifest)
        raise
    manifest.update(
        {"state": "complete", "finished_at": dt.datetime.now(dt.UTC).isoformat()}
    )
    atomic_json(manifest_path, manifest)
    print(f"Multi-node job completed; manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
