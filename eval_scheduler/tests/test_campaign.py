from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from eval_scheduler import monitor, runtime
from eval_scheduler.model import Action, Job, JobStatus


def job(
    job_id: str,
    *,
    action: Action = Action.EVAL_STANDARD,
    status: JobStatus = JobStatus.PENDING,
    deps: tuple[str, ...] = (),
    deps_mode: str = "success",
) -> Job:
    return Job(
        job_id=job_id,
        action=action,
        family="test",
        name=job_id,
        status=status,
        deps=deps,
        deps_mode=deps_mode,
    )


def test_terminal_barrier_accepts_failed_and_unreachable_eval_jobs() -> None:
    jobs = [
        job("export", action=Action.EXPORT_HF, status=JobStatus.FAILED),
        job("eval-failed", status=JobStatus.FAILED, deps=("export",)),
        job("eval-blocked", deps=("export",)),
        job(
            "barrier",
            action=Action.TERMINAL_BARRIER,
            deps=("eval-failed", "eval-blocked"),
            deps_mode="terminal",
        ),
    ]

    assert runtime.dependencies_satisfied(jobs[-1], jobs)


def test_terminal_barrier_waits_for_runnable_retry() -> None:
    jobs = [
        job("export", action=Action.EXPORT_HF, status=JobStatus.DONE),
        job("eval-retry", deps=("export",)),
        job(
            "barrier",
            action=Action.TERMINAL_BARRIER,
            deps=("eval-retry",),
            deps_mode="terminal",
        ),
    ]

    assert not runtime.dependencies_satisfied(jobs[-1], jobs)


def test_success_dependency_still_blocks_merge_after_eval_failure() -> None:
    jobs = [
        job("eval", status=JobStatus.FAILED),
        job("merge", action=Action.MERGE_STANDARD, deps=("eval",)),
    ]

    assert not runtime.dependencies_satisfied(jobs[-1], jobs)


def test_all_gpu_training_allocation_is_atomic(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        runtime,
        "gpu_snapshot",
        lambda _gpu: ("179000", "1000", "180000"),
    )
    runner = runtime.Runner(tmp_path, [0, 1, 2])
    training = Job(
        job_id="train",
        action=Action.TRAIN_UNTIL_STEP,
        family="training",
        name="step_100",
        gpu_policy="all",
        metadata={"min_gpu_free_mib": 178000},
    )
    partial = [0, 1]
    assert runner.select_gpus(training, partial) is None
    assert partial == [0, 1]

    complete = [0, 1, 2]
    assert runner.select_gpus(training, complete) == (0, 1, 2)
    assert complete == []


def test_training_checkpoint_requires_regular_sidecar(tmp_path: Path) -> None:
    tag = "step_100"
    checkpoint = tmp_path / "checkpoints"
    shard = checkpoint / f"fsdp2_{tag}"
    shard.mkdir(parents=True)
    (shard / ".metadata").touch()
    for rank in range(2):
        (checkpoint / f"carry_{tag}.{rank}.pt").touch()
    training = Job(
        job_id="train",
        action=Action.TRAIN_UNTIL_STEP,
        family="training",
        name=tag,
        metadata={
            "ckpt_path": str(checkpoint),
            "ckpt_tag": tag,
            "checkpoint_carry_ranks": 2,
        },
    )

    ready, reason = runtime.training_checkpoint_ready(training, 100)
    assert not ready
    assert "sidecar" in reason

    (checkpoint / f"checkpoint_state_{tag}.json").write_text(
        json.dumps({"step": 100, "checkpoint_kind": "regular"})
    )
    assert runtime.training_checkpoint_ready(training, 100) == (True, "ready")


def test_training_command_replaces_stop_target(monkeypatch, tmp_path: Path) -> None:
    process = MagicMock()
    process.wait.return_value = 0
    popen = MagicMock(return_value=process)
    monkeypatch.setattr(runtime.subprocess, "Popen", popen)
    monkeypatch.setattr(
        runtime,
        "training_checkpoint_ready",
        MagicMock(side_effect=[(False, "missing"), (True, "ready")]),
    )
    training = Job(
        job_id="train",
        action=Action.TRAIN_UNTIL_STEP,
        family="training",
        name="step_100",
        log_dir=str(tmp_path / "logs"),
        metadata={
            "command": "OMP_NUM_THREADS=1 torchrun --nproc_per_node=2 pretrain.py stop_after_step=50",
            "stop_after_step": 100,
            "ckpt_path": str(tmp_path / "checkpoints"),
            "ckpt_tag": "step_100",
            "workdir": str(tmp_path),
        },
    )

    assert runtime.run_training_until_step(training, (3, 5)) == 0
    argv = popen.call_args.args[0]
    assert "stop_after_step=50" not in argv
    assert argv[-1] == "stop_after_step=100"
    assert popen.call_args.kwargs["env"]["OMP_NUM_THREADS"] == "1"
    assert popen.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"] == "3,5"


def test_replace_hydra_overrides_handles_added_and_plain_keys() -> None:
    argv = [
        "torchrun",
        "pretrain.py",
        "+stop_after_step=50",
        "resume_checkpoint_tag=step_25",
        "data=dfm8",
    ]

    assert runtime.replace_hydra_overrides(
        argv,
        {
            "stop_after_step": "100",
            "resume_checkpoint_tag": "step_50",
        },
    ) == [
        "torchrun",
        "pretrain.py",
        "data=dfm8",
        "stop_after_step=100",
        "resume_checkpoint_tag=step_50",
    ]


def test_split_command_environment_keeps_command_without_shell() -> None:
    environment, argv = runtime.split_command_environment(
        [
            "OMP_NUM_THREADS=1",
            "MKL_NUM_THREADS=2",
            "torchrun",
            "--nproc_per_node=8",
            "pretrain.py",
        ]
    )

    assert environment == {"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "2"}
    assert argv == ["torchrun", "--nproc_per_node=8", "pretrain.py"]


def test_monitor_maps_all_gpu_training_event_to_every_gpu(tmp_path: Path) -> None:
    (tmp_path / "status.tsv").write_text(
        "2026-07-28T19:00:00+02:00\t"
        "START train train_until_step training step_100 "
        "shard_-_of_- gpu_0,1,2 attempt_1_of_1 batch_- mem_free_before_180000\n"
    )

    event = monitor.read_running_events(tmp_path)["train"]
    assert event.gpus == (0, 1, 2)


def test_monitor_reports_training_segment_progress_and_rate_eta(tmp_path: Path) -> None:
    log_dir = tmp_path / "training"
    log_dir.mkdir()
    (log_dir / "train_until_step_150000.log").write_text(
        " 38%|███▊      | 101120/268857 [02:12<28:58:27,  1.60it/s]\n"
    )
    training = Job(
        job_id="train",
        action=Action.TRAIN_UNTIL_STEP,
        family="training",
        name="step_150000",
        log_dir=str(log_dir),
        metadata={
            "resume_from_tag": "ephemeral_step_101000",
            "stop_after_step": 150000,
        },
    )

    progress = monitor.job_progress(training)

    assert progress.text == "step 101120/150000"
    assert progress.fraction == 120 / 49000
    assert progress.eta_seconds == 48880 / 1.6
    assert monitor.progress_eta(progress, elapsed=999999) == "8h29m"


def test_monitor_training_eta_supports_seconds_per_iteration(tmp_path: Path) -> None:
    log_dir = tmp_path / "training"
    log_dir.mkdir()
    (log_dir / "train_until_step_200.log").write_text(
        " 10%|█         | 110/1000 [00:20<29:40,  2.00s/it]\n"
    )
    training = Job(
        job_id="train",
        action=Action.TRAIN_UNTIL_STEP,
        family="training",
        name="step_200",
        log_dir=str(log_dir),
        metadata={"resume_from_tag": "step_100", "stop_after_step": 200},
    )

    progress = monitor.job_progress(training)

    assert progress.text == "step 110/200"
    assert progress.fraction == 0.1
    assert progress.eta_seconds == 180
