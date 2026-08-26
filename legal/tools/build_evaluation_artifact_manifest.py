#!/usr/bin/env python3
"""Hash release-checkpoint evaluation plans, configs, code, and retained outputs."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "legal" / "registers" / "evaluation-artifact-manifest.csv"
PLAN_ROOT = ROOT / "logs" / "scheduler" / "dfm8_XL_steps1250k_1450k_vllm_hrmenv_20260714_094255"
RESULT_ROOTS = (
    ROOT / "logs" / "dfm_evals" / "dfm8_XL_steps1250k_1450k_vllm_hrmenv" / "step_1650000",
    ROOT / "logs" / "eval" / "dfm8_XL_steps1250k_1450k_vllm_hrmenv" / "step_1650000",
)
CODE_INPUTS = (
    ROOT / "config" / "dfm_evals_hrm.yaml",
    ROOT / "config" / "dfm_evals_hrm_single_tasks.yaml",
    ROOT / "config" / "dfm_evals_hrm_ifeval_da_16_shards.yaml",
    ROOT / "config" / "dfm_evals_hrm_ifeval_da_32_shards.yaml",
    ROOT / "evaluation" / "config" / "cfg_eval.yaml",
    ROOT / "scripts" / "merge_dfm_eval_shards.py",
    ROOT / "scripts" / "merge_eval_shards.py",
    ROOT / "scripts" / "run_euroeval_on_checkpoint.sh",
    ROOT / "eval_scheduler" / "eval_scheduler" / "catalog.py",
    ROOT / "eval_scheduler" / "eval_scheduler" / "runtime.py",
)
EVIDENCE_SUFFIXES = {".json", ".jsonl", ".eval", ".eval-set-id", ".log", ".tsv", ".yaml", ".yml"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(path: Path) -> str:
    if path.is_relative_to(PLAN_ROOT):
        return "scheduler_plan_or_log"
    if any(path.is_relative_to(root) for root in RESULT_ROOTS):
        return "evaluation_output"
    return "evaluation_code_or_config"


def main() -> None:
    paths = [path for path in PLAN_ROOT.rglob("*") if path.is_file() and path.suffix in EVIDENCE_SUFFIXES]
    for root in RESULT_ROOTS:
        paths.extend(path for path in root.rglob("*") if path.is_file() and path.suffix in EVIDENCE_SUFFIXES)
    paths.extend(path for path in CODE_INPUTS if path.is_file())
    paths = sorted(set(paths))

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["artifact_type", "path", "size_bytes", "sha256"],
        )
        writer.writeheader()
        for path in paths:
            writer.writerow(
                {
                    "artifact_type": classify(path),
                    "path": str(path.relative_to(ROOT)),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    print(f"Wrote {len(paths)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
