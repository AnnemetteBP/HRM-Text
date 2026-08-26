from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from scripts import audit_export_datasets


def _row(row_id: str, *, keep: bool) -> dict[str, object]:
    return {
        "row_id": row_id,
        "dataset": "dataset",
        "task": "denoising",
        "keep": keep,
        "primary_failure_type": None if keep else "quality",
    }


def test_resume_repairs_partial_tail_and_summarizes_all_rows(tmp_path, monkeypatch) -> None:
    audit_root = tmp_path / "audit"
    audit_root.mkdir()
    audit_path = audit_root / "export_judge.audit.jsonl"
    existing = [_row("dataset/file.jsonl:0", keep=True), _row("dataset/file.jsonl:1", keep=False)]
    audit_path.write_text("\n".join(json.dumps(row) for row in existing) + "\n{\"row_id\":")

    jobs = [
        ("dataset", Path("file.jsonl"), 0, "old", "old"),
        ("dataset", Path("file.jsonl"), 2, "new", "new"),
    ]
    monkeypatch.setattr(audit_export_datasets, "iter_jobs", lambda _args: iter(jobs))
    monkeypatch.setattr(
        audit_export_datasets,
        "judge_row",
        lambda *_args: _row("dataset/file.jsonl:2", keep=True),
    )
    args = SimpleNamespace(
        audit_root=audit_root,
        force=False,
        resume=True,
        concurrency=1,
        progress_interval=100,
        export_root=tmp_path,
        dataset=["dataset"],
        sample_rate=1.0,
        max_records=None,
        model="judge",
        base_url="http://localhost",
    )

    audit_export_datasets.audit(args)

    rows = [json.loads(line) for line in audit_path.read_text().splitlines()]
    assert [row["row_id"] for row in rows] == [
        "dataset/file.jsonl:0",
        "dataset/file.jsonl:1",
        "dataset/file.jsonl:2",
    ]
    summary = json.loads((audit_root / "summary.json").read_text())
    assert summary["counts"] == {
        "audited": 3,
        "drop": 1,
        "failure:quality": 1,
        "keep": 2,
    }
    assert summary["keep_rate"] == 2 / 3
