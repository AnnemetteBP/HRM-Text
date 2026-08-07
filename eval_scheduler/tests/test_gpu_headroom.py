from pathlib import Path

from eval_scheduler import runtime
from eval_scheduler.model import Action, Job


def gpu_job(minimum: int) -> Job:
    return Job(
        job_id="eval-1",
        action=Action.EVAL_STANDARD,
        family="standard",
        name="BoolQ",
        metadata={"min_gpu_free_mib": minimum},
    )


def test_select_gpu_uses_highest_eligible_headroom(monkeypatch, tmp_path: Path) -> None:
    snapshots = {
        0: ("30000", "150000", "180000"),
        1: ("36000", "144000", "180000"),
        2: ("40000", "140000", "180000"),
    }
    monkeypatch.setattr(runtime, "gpu_snapshot", lambda gpu: snapshots[gpu])
    runner = runtime.Runner(tmp_path, [0, 1, 2])
    free_gpus = [0, 1, 2]

    assert runner.select_gpu(gpu_job(34000), free_gpus) == 2
    assert free_gpus == [0, 1]


def test_select_gpu_waits_when_no_gpu_meets_gate(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        runtime,
        "gpu_snapshot",
        lambda _gpu: ("32000", "148000", "180000"),
    )
    runner = runtime.Runner(tmp_path, [0, 1])
    free_gpus = [0, 1]

    assert runner.select_gpu(gpu_job(34000), free_gpus) is None
    assert free_gpus == [0, 1]


def test_reusable_persistent_lease_bypasses_reserved_memory(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        runtime,
        "gpu_snapshot",
        lambda _gpu: ("10000", "170000", "180000"),
    )
    runner = runtime.Runner(tmp_path, [0], persistent_vllm=True)
    assert runner.server_pool is not None
    monkeypatch.setattr(
        runner.server_pool,
        "effective_free_credit_mib",
        lambda _job, _gpu, _total: -1,
    )
    free_gpus = [0]

    assert runner.select_gpu(gpu_job(34000), free_gpus) == 0
    assert free_gpus == []


def test_replaced_persistent_lease_credits_reclaimable_reservation(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        runtime,
        "gpu_snapshot",
        lambda _gpu: ("10000", "170000", "180000"),
    )
    runner = runtime.Runner(tmp_path, [0], persistent_vllm=True)
    assert runner.server_pool is not None
    monkeypatch.setattr(
        runner.server_pool,
        "effective_free_credit_mib",
        lambda _job, _gpu, _total: 25200,
    )
    free_gpus = [0]

    assert runner.select_gpu(gpu_job(34000), free_gpus) == 0
    assert free_gpus == []
