"""Process-local CPU admission for preparation jobs on one node.

Share one pool between scheduler threads. Reserved CPUs are excluded from all
preparation leases; this does not change gateway affinity or constrain foreign
processes. Affinity is scheduling containment, not a security sandbox.

    lease = pool.acquire(cpu_cores=2)
    if lease is not None:
        argv, env = pool.prepare(argv, env, lease)
        # Popen failure: release immediately. Success: wait for child exit first.
        child = subprocess.Popen(argv, env=env)  # no preexec_fn
        child.wait()
        pool.release(lease, child=child)

Children inherit taskset affinity and thread limits. Jobs must not daemonize
descendants that outlive their supervised child or change their own affinity.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import threading
from typing import Mapping, Sequence
import uuid


@dataclass(frozen=True)
class CpuLease:
    token: str
    core_ids: tuple[int, ...]

    @property
    def cpu_cores(self) -> int:
        return len(self.core_ids)


def child_affinity(pid: int = 0) -> tuple[int, ...]:
    """Read a child (or calling thread's) logical CPU affinity without changing it."""
    return tuple(sorted(os.sched_getaffinity(pid)))


def _integer(value: int, name: str, minimum: int) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


class CpuBudget:
    """Nonblocking, thread-safe pool; CPU counts refer to logical CPUs, not sockets."""

    def __init__(self, total_cores: int = 256, reserve_cores: int = 8):
        _integer(total_cores, "total_cores", 1)
        _integer(reserve_cores, "reserve_cores", 0)
        if reserve_cores > total_cores:
            raise ValueError("reserve_cores exceeds total_cores")
        self.affinity_core_ids = child_affinity()
        if not self.affinity_core_ids:
            raise ValueError("No CPUs available in scheduler affinity")
        self.core_ids = self.affinity_core_ids[:total_cores]
        self.reserved_core_ids = self.core_ids[:reserve_cores]
        self.worker_core_ids = self.core_ids[reserve_cores:]
        self.total_cores = len(self.core_ids)
        self.reserve_cores = len(self.reserved_core_ids)
        self.capacity = len(self.worker_core_ids)
        self.requested_total_cores = total_cores
        self.requested_reserve_cores = reserve_cores
        self._free = set(self.worker_core_ids)
        self._leases: dict[str, CpuLease] = {}
        self._lock = threading.Lock()

    def acquire(self, cpu_cores: int = 2) -> CpuLease | None:
        """Claim distinct CPUs, or return None if another job holds the capacity."""
        _integer(cpu_cores, "cpu_cores", 1)
        if cpu_cores > self.capacity:
            raise ValueError(f"cpu_cores={cpu_cores} exceeds preparation capacity={self.capacity}")
        with self._lock:
            if len(self._free) < cpu_cores:
                return None
            lease = CpuLease(uuid.uuid4().hex, tuple(sorted(self._free)[:cpu_cores]))
            self._free.difference_update(lease.core_ids)
            self._leases[lease.token] = lease
            return lease

    def _check_lease(self, lease: CpuLease) -> None:
        if not isinstance(lease, CpuLease) or self._leases.get(lease.token) is not lease:
            raise ValueError("Lease is foreign, forged or already released")

    def release(self, lease: CpuLease, *, child=None) -> None:
        """Release after child exit; pass Popen to guard against premature release.

        Without child, the caller owns exit verification (also used on spawn
        failure). No automatic expiry can reallocate CPUs under a running job.
        """
        with self._lock:
            self._check_lease(lease)
            if child is not None and child.poll() is None:
                raise RuntimeError("Cannot release CPUs while the child is running")
            del self._leases[lease.token]
            self._free.update(lease.core_ids)

    def prepare(
        self, argv: Sequence[str | os.PathLike], env: Mapping[str, str] | None,
        lease: CpuLease,
    ) -> tuple[list[str], dict[str, str]]:
        """Return shell-free taskset argv and a copied environment for Popen.

        env=None copies os.environ; a mapping is a complete child environment,
        not an overlay. The lease remains claimed if preparation/spawn fails.
        """
        if isinstance(argv, (str, bytes)) or not argv:
            raise ValueError("argv must be a nonempty argument sequence")
        command = [os.fspath(arg) for arg in argv]
        if any(not isinstance(arg, str) or '\0' in arg for arg in command) or not command[0]:
            raise ValueError("argv must contain NUL-free strings and an executable")
        with self._lock:
            self._check_lease(lease)
            executable = shutil.which("taskset")
            if executable is None:
                raise RuntimeError("taskset is required; refusing an unpinned subprocess")
            result = dict(os.environ if env is None else env)
            # Do not carry a gateway's thread-binding policy into a worker lease.
            for name in ("GOMP_CPU_AFFINITY", "KMP_AFFINITY", "KMP_HW_SUBSET", "OMP_PLACES"):
                result.pop(name, None)
            count = str(lease.cpu_cores)
            for name in ("OMP_NUM_THREADS", "OMP_THREAD_LIMIT", "MKL_NUM_THREADS",
                         "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                         "NUMEXPR_MAX_THREADS", "RAYON_NUM_THREADS"):
                result[name] = count
            result.update(TOKENIZERS_PARALLELISM="false", OMP_DYNAMIC="false",
                          MKL_DYNAMIC="false", OMP_PROC_BIND="false")
            return [str(Path(executable).resolve()), "--cpu-list",
                    ','.join(map(str, lease.core_ids)), *command], result

    @property
    def available_cores(self) -> int:
        with self._lock:
            return len(self._free)

    def snapshot(self) -> dict:
        """Atomic reserve/allocation information, suitable for a runtime receipt."""
        with self._lock:
            return dict(requested_total_cores=self.requested_total_cores,
                        requested_reserve_cores=self.requested_reserve_cores,
                        total_cores=self.total_cores, reserve_cores=self.reserve_cores,
                        capacity=self.capacity, available_cores=len(self._free),
                        affinity_core_ids=self.affinity_core_ids, core_ids=self.core_ids,
                        reserved_core_ids=self.reserved_core_ids,
                        worker_core_ids=self.worker_core_ids,
                        leases={token:lease.core_ids for token,lease in self._leases.items()})
