#!/usr/bin/env python3
"""Validate internal consistency of the machine-readable Mimir dossier."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTERS = ROOT / "legal" / "registers"


def read_csv(name: str) -> list[dict[str, str]]:
    with (REGISTERS / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    actions = read_csv("action-register.csv")
    statuses = Counter(row["status"] for row in actions)
    assert len(actions) == 46, f"expected 46 actions, found {len(actions)}"
    assert set(statuses) == {
        "human_required",
        "resolved_engineering",
        "resolved_human",
    }, statuses

    datasets = read_csv("dataset-legal-basis-register.csv")
    assert len(datasets) == 161, len(datasets)
    assert sum(int(row["sampled_tokens_per_epoch"]) for row in datasets) == 70_479_308_606

    hf = read_csv("hf-current-metadata-register.csv")
    assert len(hf) == 159, len(hf)
    assert all(row["fetch_status"] == "ok" for row in hf)

    dag_nodes = read_csv("dfm9-source-dag-nodes.csv")
    dag_edges = read_csv("dfm9-source-dag-edges.csv")
    dag_resolution = read_csv("dfm9-source-dag-resolution.csv")
    dag_queue = read_csv("dfm9-source-dag-expansion-queue.csv")
    node_ids = {row["node_id"] for row in dag_nodes}
    assert len(node_ids) == len(dag_nodes), "duplicate DAG node IDs"
    assert len(dag_resolution) == len(dag_nodes)
    assert {row["node_id"] for row in dag_resolution} == node_ids
    assert all(row["parent_id"] in node_ids and row["child_id"] in node_ids for row in dag_edges)
    assert sum(row["node_type"] == "effective_dataset" for row in dag_nodes) == 161
    assert {row["computed_status"] for row in dag_resolution} <= {"cleared", "partial", "unresolved"}
    assert all(row["node_id"] in node_ids for row in dag_queue)
    assert all(float(dag_queue[i]["average_tokens_per_epoch"]) >= float(dag_queue[i + 1]["average_tokens_per_epoch"])
               for i in range(len(dag_queue) - 1))

    effective_basis = read_csv("dfm9-effective-rights-basis.csv")
    assert len(effective_basis) == 161
    assert {row["source_id"] for row in effective_basis} == {
        row["source_id"] for row in read_csv("dfm9-copyright-basis-register.csv")
    }
    assert sum(float(row["average_tokens_per_epoch"]) for row in effective_basis) == 79_938_703_077.8

    synthetic = read_csv("synthetic-data-register.csv")
    assert len(synthetic) == 91, len(synthetic)
    missing_recipes = [row["prompt_or_recipe_evidence"] for row in synthetic if not (ROOT / row["prompt_or_recipe_evidence"]).exists()]
    assert not missing_recipes, missing_recipes

    summaries = {row["phase_id"]: row for row in read_csv("phase-exposure-summary.csv")}
    assert len(summaries) == 3
    for register in ("phase-source-exposure-register.csv", "phase-task-exposure-register.csv"):
        totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for row in read_csv(register):
            totals[row["phase_id"]][0] += int(row["sampled_rows_consumed"])
            totals[row["phase_id"]][1] += int(row["source_tokens_consumed"])
        for phase_id, (rows, tokens) in totals.items():
            assert rows == int(summaries[phase_id]["sampled_rows_consumed"])
            assert tokens == int(summaries[phase_id]["source_tokens_consumed"])

    artifacts = read_csv("evaluation-artifact-manifest.csv")
    assert len(artifacts) == 1_252, len(artifacts)
    for row in artifacts:
        path = ROOT / row["path"]
        assert path.is_file(), path
        assert path.stat().st_size == int(row["size_bytes"]), path
        assert sha256(path) == row["sha256"], path

    print(
        "Dossier validation passed: "
        f"actions={dict(statuses)}, datasets={len(datasets)}, "
        f"synthetic={len(synthetic)}, evaluation_artifacts={len(artifacts)}"
    )


if __name__ == "__main__":
    main()
