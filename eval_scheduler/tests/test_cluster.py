from __future__ import annotations

import time
from concurrent.futures import Future
from pathlib import Path

from eval_scheduler.cluster_monitor import cluster_rich_renderable, cluster_status_text
from eval_scheduler.cluster_protocol import (
    ClusterClient,
    ClusterProtocolError,
    start_cluster_server,
)
from eval_scheduler.cluster_runtime import ClusterCoordinator, ClusterWorker
from eval_scheduler.model import (
    Action,
    Capability,
    ExecutionScope,
    Job,
    JobStatus,
    read_plan,
    write_plan,
)

from eval_scheduler import cluster_runtime


def worker_payload(node_id: str = "node-00", boot_id: str = "boot-a") -> dict[str, object]:
    return {
        "node_id": node_id,
        "boot_id": boot_id,
        "hostname": node_id,
        "capabilities": ["eval", "export", "teardown"],
        "repo_commit": "deadbeef",
        "python": "/env/bin/python",
        "environment": "/env",
        "gpus": [
            {
                "gpu_id": 0,
                "free_mib": 170000,
                "used_mib": 10000,
                "total_mib": 180000,
                "utilization": 0,
                "server_key": "",
                "server_utilization": 0,
            }
        ],
        "active_leases": [],
    }


def coordinator(tmp_path: Path, jobs: list[Job]) -> ClusterCoordinator:
    plan_dir = tmp_path / "plan"
    write_plan(plan_dir / "plan.tsv", jobs)
    return ClusterCoordinator(plan_dir, bind_host="127.0.0.1", port=0)


def test_old_job_rows_derive_safe_execution_profiles() -> None:
    evaluation = Job(
        job_id="eval",
        action=Action.EVAL_DFM,
        family="dfm",
        name="piqa",
    )
    training = Job(
        job_id="train",
        action=Action.TRAIN_UNTIL_STEP,
        family="training",
        name="step_10",
    )

    assert evaluation.resolved_execution_scope == ExecutionScope.GPU
    assert evaluation.resolved_capability == Capability.EVAL
    assert evaluation.resolved_gpu_count == 1
    assert training.resolved_execution_scope == ExecutionScope.CLUSTER
    assert training.resolved_capability == Capability.TRAIN


def test_capability_cannot_broaden_action_profile() -> None:
    job = Job(
        job_id="bad",
        action=Action.EVAL_STANDARD,
        family="standard",
        name="BoolQ",
        required_capability="train",
    )
    try:
        _ = job.resolved_capability
    except ValueError as exc:
        assert "cannot override" in str(exc)
    else:
        raise AssertionError("unsafe capability override was accepted")


def test_remote_assignment_and_completion_are_node_qualified(tmp_path: Path) -> None:
    job = Job(
        job_id="eval-1",
        action=Action.EVAL_STANDARD,
        family="standard",
        name="BoolQ",
        initial_batch=16,
        log_dir=str(tmp_path / "logs"),
        metadata={"min_gpu_free_mib": 100000},
    )
    service = coordinator(tmp_path, [job])
    service._register(worker_payload())

    response = service._poll({"node_id": "node-00", "boot_id": "boot-a"})

    assert response["command"] == "run"
    assert response["gpu_id"] == 0
    assert response["lease"]["resources"] == [{"node_id": "node-00", "gpu_id": 0}]
    token = response["lease"]["token"]
    completed = service._complete(
        {
            "node_id": "node-00",
            "boot_id": "boot-a",
            "lease_token": token,
            "status": 0,
            "oom": False,
        }
    )
    assert completed == {"accepted": True}
    assert read_plan(service.plan_file)[0].status == JobStatus.DONE
    assert "node-00:gpu0" in (service.plan_dir / "attempts.tsv").read_text()


def test_new_worker_boot_fences_and_retries_old_lease(tmp_path: Path) -> None:
    job = Job(
        job_id="eval-1",
        action=Action.EVAL_DFM,
        family="dfm",
        name="piqa",
        max_retries=3,
    )
    service = coordinator(tmp_path, [job])
    service._register(worker_payload())
    response = service._poll({"node_id": "node-00", "boot_id": "boot-a"})
    assert response["command"] == "run"

    service._register(worker_payload(boot_id="boot-b"))

    retried = read_plan(service.plan_file)[0]
    assert retried.status == JobStatus.PENDING
    assert retried.attempt == 1
    assert not service.leases


def test_cluster_teardown_waits_for_every_worker_ack(tmp_path: Path) -> None:
    teardown = Job(
        job_id="teardown",
        action=Action.TEARDOWN_EVAL,
        family="control",
        name="teardown",
    )
    service = coordinator(tmp_path, [teardown])
    service._register(worker_payload("node-00", "boot-a"))
    service._register(worker_payload("node-01", "boot-b"))
    with service.lock:
        service._schedule_control_locked()

    assert service.mode == "draining"
    assert service.teardown_pending == {"node-00", "node-01"}
    assert service._heartbeat(worker_payload("node-00", "boot-a"))["command"] == "teardown"
    service._teardown_ack(
        {"node_id": "node-00", "boot_id": "boot-a", "job_id": "teardown"}
    )
    assert read_plan(service.plan_file)[0].status == JobStatus.RUNNING
    service._teardown_ack(
        {"node_id": "node-01", "boot_id": "boot-b", "job_id": "teardown"}
    )
    assert read_plan(service.plan_file)[0].status == JobStatus.DONE
    assert service.mode == "evaluating"


def test_multinode_training_wraps_torchrun_command(tmp_path: Path) -> None:
    training = Job(
        job_id="train",
        action=Action.TRAIN_UNTIL_STEP,
        family="training",
        name="step_100",
        metadata={
            "command": (
                "OMP_NUM_THREADS=1 /env/bin/torchrun --nproc_per_node=8 "
                "pretrain.py data=dfm10 global_batch_size=262144"
            ),
            "multinode_hostfile": "/cluster/hosts.txt",
            "multinode_python_env": "/env",
            "multinode_nccl_interface": "ib0",
            "multinode_required_paths": ["/data", "/checkpoints"],
            "workdir": "/repo",
        },
    )
    service = coordinator(tmp_path, [training])

    wrapped = service._multinode_training_job(training)
    command = wrapped.metadata["command"]

    assert command[:2] == ["/env/bin/python", "scripts/launch_multinode_torchrun.py"]
    assert command[command.index("--hostfile") + 1] == "/cluster/hosts.txt"
    assert command[command.index("--nccl-interface") + 1] == "ib0"
    assert "OMP_NUM_THREADS=1" in command
    separator = command.index("--")
    assert command[separator + 1 :] == [
        "pretrain.py",
        "data=dfm10",
        "global_batch_size=262144",
    ]


def test_future_checkpoint_waiter_does_not_block_cluster_training(
    tmp_path: Path, monkeypatch
) -> None:
    waiter = Job(
        job_id="wait-future",
        action=Action.WAIT_CHECKPOINT,
        family="checkpoint",
        name="step_200",
        status=JobStatus.RUNNING,
    )
    training = Job(
        job_id="train-now",
        action=Action.TRAIN_UNTIL_STEP,
        family="training",
        name="step_100",
    )
    service = coordinator(tmp_path, [waiter, training])
    waiting_future: Future[tuple[str, int]] = Future()
    service.control_futures[waiting_future] = waiter.job_id
    submitted: list[str] = []

    def submit(_callable, job):
        submitted.append(job.job_id)
        return Future()

    monkeypatch.setattr(service.control_pool, "submit", submit)
    with service.lock:
        service._schedule_control_locked()

    assert submitted == [training.job_id]
    assert read_plan(service.plan_file)[1].status == JobStatus.RUNNING


def test_authenticated_http_registration_and_snapshot(tmp_path: Path) -> None:
    service = coordinator(tmp_path, [])
    server, thread = start_cluster_server(
        service, host="127.0.0.1", port=0, token=service.token
    )
    url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        response = ClusterClient(url, service.token).request(
            "/v1/register", worker_payload()
        )
        assert response["ok"] is True
        snapshot = ClusterClient(url, service.token).request("/v1/snapshot")
        assert "node-00" in snapshot["workers"]
        try:
            ClusterClient(url, "wrong").request("/v1/snapshot")
        except ClusterProtocolError as exc:
            assert "401" in str(exc)
        else:
            raise AssertionError("invalid bearer token was accepted")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_worker_executes_and_completes_job_over_http(tmp_path: Path, monkeypatch) -> None:
    job = Job(
        job_id="eval-http",
        action=Action.EVAL_STANDARD,
        family="standard",
        name="BoolQ",
        log_dir=str(tmp_path / "logs"),
    )
    service = coordinator(tmp_path, [job])
    server, server_thread = start_cluster_server(
        service, host="127.0.0.1", port=0, token=service.token
    )
    url = f"http://127.0.0.1:{server.server_address[1]}"
    monkeypatch.setattr(
        cluster_runtime,
        "gpu_snapshot",
        lambda _gpu: ("170000", "10000", "180000"),
    )
    monkeypatch.setattr(cluster_runtime, "run_job", lambda *_args, **_kwargs: 0)
    worker = ClusterWorker(
        coordinator_url=url,
        token=service.token,
        plan_dir=service.plan_dir,
        node_id="node-http",
        gpus=[0],
        workdir=tmp_path,
        environment="/env",
        persistent_vllm=False,
    )
    try:
        worker.register()
        response = worker.client.request(
            "/v1/poll", {"node_id": worker.node_id, "boot_id": worker.boot_id}
        )
        assert response["command"] == "run"
        worker._accept_assignment(response)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if read_plan(service.plan_file)[0].status == JobStatus.DONE:
                break
            time.sleep(0.01)
        assert read_plan(service.plan_file)[0].status == JobStatus.DONE
        for execution_thread in list(worker.threads.values()):
            execution_thread.join(timeout=5)
        assert not worker.active
    finally:
        worker.stop_event.set()
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)


def test_coordinator_restores_fenced_leases_from_atomic_snapshot(tmp_path: Path) -> None:
    job = Job(
        job_id="eval-1",
        action=Action.EVAL_STANDARD,
        family="standard",
        name="BoolQ",
        max_retries=3,
    )
    service = coordinator(tmp_path, [job])
    service._register(worker_payload())
    response = service._poll({"node_id": "node-00", "boot_id": "boot-a"})
    with service.lock:
        service._write_snapshot_locked()

    restored = ClusterCoordinator(
        service.plan_dir, bind_host="127.0.0.1", port=0
    )

    assert response["lease"]["token"] in restored.leases
    assert restored.lease_by_job == {
        "eval-1": response["lease"]["token"]
    }
    text = cluster_status_text(restored.plan_dir)
    assert "node-00/GPU0" in text
    assert "standard:BoolQ" in text


def test_cluster_training_is_shown_on_worker_gpus(tmp_path: Path) -> None:
    from rich.console import Console

    training = Job(
        job_id="train-cluster",
        action=Action.TRAIN_UNTIL_STEP,
        family="training",
        name="step_100",
        status=JobStatus.RUNNING,
    )
    service = coordinator(tmp_path, [training])
    service._register(worker_payload())
    service.control_futures[Future()] = training.job_id
    with service.lock:
        service.mode = "training"
        service._write_snapshot_locked()

    text = cluster_status_text(service.plan_dir)

    assert "node-00/GPU0" in text
    assert "training:step_100" in text
    assert "node-00/GPU0:" in text and " idle" not in text
    assert "control: train-cluster" not in text
    console = Console(record=True, width=160)
    console.print(cluster_rich_renderable(service.plan_dir))
    rich_text = console.export_text()
    assert "training:step_100" in rich_text
    assert "idle" not in rich_text
    assert "CLUSTER" not in rich_text
