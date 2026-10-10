import json
import os
from pathlib import Path
import sys

import pytest
from typer.testing import CliRunner

from eval_scheduler.cpu_budget import CpuBudget
from eval_scheduler.model import Action, Job, JobStatus, read_plan, write_plan
from eval_scheduler.runtime import Runner, client_cpu_lease, prepare_client_command, run_command, run_with_vllm_server
from eval_scheduler.store import SQLiteJobStore


def test_cpu_context_limits_child_and_restores_thread(tmp_path):
    original = os.sched_getaffinity(0)
    budget = CpuBudget(total_cores=2, reserve_cores=0)
    lease = budget.acquire(1)
    output = tmp_path / "child.log"
    with client_cpu_lease(budget, lease):
        assert os.sched_getaffinity(0) == set(lease.core_ids)
        _, env = prepare_client_command([sys.executable], {"CUDA_VISIBLE_DEVICES": "0"})
        assert env["CUDA_VISIBLE_DEVICES"] == ""
        code = "import os,json; print(json.dumps([sorted(os.sched_getaffinity(0)),os.environ['OMP_NUM_THREADS']]))"
        assert run_command([sys.executable, "-c", code], log_path=output) == 0
    assert os.sched_getaffinity(0) == original
    _, env = prepare_client_command([sys.executable], {"CUDA_VISIBLE_DEVICES": "0"})
    assert env["CUDA_VISIBLE_DEVICES"] == "0"
    assert json.loads(output.read_text()) == [list(lease.core_ids), "1"]
    budget.release(lease)


def test_migrated_plan_reads_database_and_rejects_legacy_writer(tmp_path):
    job = Job("one", Action.REPORT, "report", "report")
    path = tmp_path / "plan.tsv"
    write_plan(path, [job])
    store = SQLiteJobStore(tmp_path / "state.sqlite")
    store.import_jobs([job])
    store.update_jobs({"one": {"status": JobStatus.DONE}})
    (tmp_path / "database.json").write_text(json.dumps({"database": str(store.path)}))
    assert read_plan(path)[0].status == JobStatus.DONE
    with pytest.raises(ValueError, match="SQLite-managed"):
        write_plan(path, [job])
    with pytest.raises(RuntimeError, match="SQLite-managed"):
        Runner(tmp_path, [0])
    store.export_tsv(path)
    assert "done" in path.read_text()


def test_shared_callback_delegates_without_claiming_gpu(tmp_path):
    calls = []
    class Pool:
        def run_client(self, job, callback):
            calls.append(job.job_id)
            return callback("http://localhost/client/v1", tmp_path / "log", None, "alias")
        def acquire(self, *args):
            raise AssertionError("Client must not claim an exclusive GPU")
    job = Job("one", Action.EVAL_STANDARD, "standard", "piqa")
    result = run_with_vllm_server(job, 0, model_name="m", port_offset=0,
                                  log=tmp_path / "log", callback=lambda *args: 17,
                                  server_pool=Pool())
    assert result == 17
    assert calls == ["one"]


def test_cli_migrate_execute_and_monitor_cpu_only(tmp_path):
    from eval_scheduler.cli import app
    plan_dir = tmp_path / "campaign"
    plan_dir.mkdir()
    path = plan_dir / "plan.tsv"
    write_plan(path, [Job("barrier", Action.TERMINAL_BARRIER, "control", "done")])
    database = tmp_path / "jobs.sqlite"
    cli = CliRunner()
    result = cli.invoke(app, ["database", "import", "--source", str(path),
                             "--plan-dir", str(plan_dir), "--database", str(database),
                             "--runners-stopped"])
    assert result.exit_code == 0, result.output
    result = cli.invoke(app, ["run", "--plan-dir", str(plan_dir), "--backend", "sqlite",
                             "--persistent-vllm", "--gpus", "0",
                             "--reserve-cores", "1", "--client-cpu-cores", "1"])
    assert result.exit_code == 0, (result.output, result.exception)
    assert "database_runner\tdone" in result.output
    assert read_plan(path)[0].status == JobStatus.DONE
    assert "pending" in path.read_text()  # Input TSV remains an untouched definition artifact.
    assert "done" in (plan_dir / "plan.snapshot.tsv").read_text()
    result = cli.invoke(app, ["monitor", "--plan-dir", str(plan_dir), "--once", "--gpus", "0"])
    assert result.exit_code == 0, (result.output, result.exception)
    assert "done=1" in result.output
