from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any

from .model import Capability


@dataclass(frozen=True, order=True)
class ResourceId:
    node_id: str
    gpu_id: int

    @property
    def label(self) -> str:
        return f"{self.node_id}:gpu{self.gpu_id}"


@dataclass(frozen=True)
class GpuSnapshot:
    gpu_id: int
    free_mib: int | None
    used_mib: int | None
    total_mib: int | None
    utilization: int | None
    server_key: str = ""
    server_utilization: float = 0.0

    @classmethod
    def from_wire(cls, value: dict[str, Any]) -> GpuSnapshot:
        return cls(
            gpu_id=int(value["gpu_id"]),
            free_mib=_optional_int(value.get("free_mib")),
            used_mib=_optional_int(value.get("used_mib")),
            total_mib=_optional_int(value.get("total_mib")),
            utilization=_optional_int(value.get("utilization")),
            server_key=str(value.get("server_key") or ""),
            server_utilization=float(value.get("server_utilization") or 0.0),
        )


@dataclass
class WorkerInfo:
    node_id: str
    boot_id: str
    hostname: str
    capabilities: set[Capability]
    repo_commit: str
    python: str
    environment: str
    gpus: dict[int, GpuSnapshot]
    active_leases: set[str] = field(default_factory=set)
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    drained: bool = False

    @property
    def fresh_age(self) -> float:
        return max(0.0, time.time() - self.last_heartbeat)

    def to_wire(self) -> dict[str, Any]:
        value = asdict(self)
        value["capabilities"] = sorted(item.value for item in self.capabilities)
        value["gpus"] = {str(key): asdict(item) for key, item in self.gpus.items()}
        value["active_leases"] = sorted(self.active_leases)
        return value

    @classmethod
    def from_wire(cls, value: dict[str, Any]) -> WorkerInfo:
        return cls(
            node_id=str(value["node_id"]),
            boot_id=str(value["boot_id"]),
            hostname=str(value.get("hostname") or value["node_id"]),
            capabilities={Capability(item) for item in value.get("capabilities", [])},
            repo_commit=str(value.get("repo_commit") or "unknown"),
            python=str(value.get("python") or ""),
            environment=str(value.get("environment") or ""),
            gpus={
                int(key): GpuSnapshot.from_wire(item)
                for key, item in (value.get("gpus") or {}).items()
            },
            active_leases={str(item) for item in value.get("active_leases", [])},
            registered_at=float(value.get("registered_at") or time.time()),
            last_heartbeat=float(value.get("last_heartbeat") or 0),
            drained=bool(value.get("drained", False)),
        )


@dataclass(frozen=True)
class Lease:
    token: str
    job_id: str
    attempt: int
    worker_id: str
    worker_boot_id: str
    resources: tuple[ResourceId, ...]
    issued_at: float
    last_heartbeat: float

    def to_wire(self) -> dict[str, Any]:
        return {
            "token": self.token,
            "job_id": self.job_id,
            "attempt": self.attempt,
            "worker_id": self.worker_id,
            "worker_boot_id": self.worker_boot_id,
            "resources": [asdict(resource) for resource in self.resources],
            "issued_at": self.issued_at,
            "last_heartbeat": self.last_heartbeat,
        }

    @classmethod
    def from_wire(cls, value: dict[str, Any]) -> Lease:
        return cls(
            token=str(value["token"]),
            job_id=str(value["job_id"]),
            attempt=int(value["attempt"]),
            worker_id=str(value["worker_id"]),
            worker_boot_id=str(value["worker_boot_id"]),
            resources=tuple(
                ResourceId(str(item["node_id"]), int(item["gpu_id"]))
                for item in value.get("resources", [])
            ),
            issued_at=float(value["issued_at"]),
            last_heartbeat=float(value["last_heartbeat"]),
        )


def _optional_int(value: Any) -> int | None:
    if value is None or value == "NA":
        return None
    return int(value)
