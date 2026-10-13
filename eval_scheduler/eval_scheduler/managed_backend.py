"""Owned target/judge pairs; retain the existing engines and launch arguments."""
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import runtime


JUDGE_FIELDS = (
    'judge_server_model', 'judge_model', 'judge_server_dtype',
    'judge_server_attn_implementation', 'judge_server_max_new_tokens',
    'judge_memory_reserve_mib', 'judge_max_concurrency',
)


def judge_identity(job):
    if not runtime.managed_judge_enabled(job):
        return None
    return {name: job.metadata.get(name) for name in JUDGE_FIELDS}


def judge_reserve(job):
    return int(job.metadata.get('judge_memory_reserve_mib', 16384)) if judge_identity(job) else 0


@dataclass
class PairedLease:
    target: object
    judge: object
    judge_base_url: str
    judge_model_name: str

    @property
    def process(self):
        return self

    def poll(self):
        status = self.target.process.poll()
        return status if status is not None else self.judge.poll()

    @property
    def base_url(self):
        return self.target.base_url

    @property
    def model_name(self):
        return self.target.model_name

    @property
    def log_path(self):
        return self.target.log_path


class ManagedBackend:
    def __init__(self, plan_dir, event, *, target=None):
        self.plan_dir = Path(plan_dir)
        self.target = target or runtime.VLLMServerPool(self.plan_dir, event)
        self.targets = {}
        self.pairs = {}

    def acquire(self, job, gpu):
        lease = self.target.acquire(job, gpu)
        self.targets[gpu] = lease
        if not runtime.managed_judge_enabled(job):
            return lease
        try:
            free, _, _ = runtime.gpu_snapshot(gpu)
            if float(free) < judge_reserve(job):
                raise runtime.SchedulerError(f'Insufficient judge headroom on GPU {gpu}')
            directory = lease.log_path.parent / (lease.log_path.stem + '.judge')
            proc, url, _ = runtime.start_managed_judge(job, gpu, directory)
            pair = PairedLease(lease, proc, url, runtime.judge_served_model_name(job))
            self.pairs[gpu] = pair
            return pair
        except BaseException:
            self.release_gpu(gpu, 'judge_start_failed')
            raise

    def release_gpu(self, gpu, reason):
        pair = self.pairs.get(gpu)
        if pair is not None:
            runtime.terminate(pair.judge)
            if pair.judge.poll() is None:
                raise runtime.SchedulerError(f'Judge exit unconfirmed on GPU {gpu}')
            self.pairs.pop(gpu)
        self.target.release_gpu(gpu, reason)
        target = self.targets.get(gpu)
        if target is not None:
            if target.process.poll() is None:
                raise runtime.SchedulerError(f'Target exit unconfirmed on GPU {gpu}')
            self.targets.pop(gpu)

    def close_all(self):
        gpus = list(self.targets)
        if gpus:
            # The pool has already drained clients. Each worker stops only its
            # owned pair, retaining judge-before-target order within that GPU.
            with ThreadPoolExecutor(max_workers=min(8, len(gpus))) as workers:
                futures = [workers.submit(self.release_gpu, gpu, 'shared_shutdown') for gpu in gpus]
                errors = []
                for future in futures:
                    try:
                        future.result()
                    except Exception as exc:
                        errors.append(exc)
                if errors:
                    raise errors[0]
        self.target.close_all()
