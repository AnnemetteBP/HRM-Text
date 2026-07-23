#!/usr/bin/env python3
"""Prepare a DFM8-XL W&B run from the completed DFM6->DFM7 XL history.

This clones numeric history from the current DFM6-DFM7 run into a new run whose
config is set up for a future DFM8 continuation from the DFM7 epoch_5
checkpoint. It does not launch training and does not touch checkpoints.

DEPRECATED 2026-07-11: Do not use this script for a production W&B run. It
missed sparse train/eval rows and produced misleading W&B curves when repaired
incrementally. Keep it only as a record of the failed approach.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


SYSTEM_KEYS = {"_runtime", "_timestamp", "_step"}
DEFAULT_EVAL_PREFIXES = (
    "eval/",
    "dfm_eval/",
    "euroeval/",
    "avg/",
    "headline_avg/",
    "headline_avg_v2/",
    "headline_avg_v3/",
    "headline_avg_v4/",
    "suite_avg/",
    "suite_avg_v2/",
    "suite_avg_v3/",
    "suite_avg_v4/",
    "lite_eval",
    "lite_dfm_eval",
)


def finite_number(value: Any) -> float | int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return None


def row_train_step(row: dict[str, Any]) -> int | None:
    candidates = (
        "train/step",
        "eval/train_step",
        "dfm_eval/train_step",
        "euroeval/train_step",
        "avg/train_step",
        "headline_avg/train_step",
        "headline_avg_v2/train_step",
        "headline_avg_v3/train_step",
        "headline_avg_v4/train_step",
        "suite_avg/train_step",
        "suite_avg_v2/train_step",
        "suite_avg_v3/train_step",
        "suite_avg_v4/train_step",
    )
    for key in candidates:
        parsed = finite_number(row.get(key))
        if parsed is not None:
            return int(parsed)
    step = row.get("_step")
    return step if isinstance(step, int) else None


def clean_history_row(row: dict[str, Any]) -> tuple[int | None, dict[str, float | int]]:
    step = row_train_step(row)
    if step is None:
        return None, {}
    cleaned: dict[str, float | int] = {}
    for raw_key, value in row.items():
        key = str(raw_key)
        if key in SYSTEM_KEYS or key.startswith("_"):
            continue
        # Drop W&B summary convenience keys that encode epochs into the metric
        # name; keep canonical metric keys and explicit axis keys.
        if "/epoch_" in key or key.endswith("/last_epoch"):
            continue
        parsed = finite_number(value)
        if parsed is not None:
            cleaned[key] = parsed
    if cleaned:
        cleaned.setdefault("train/step", step)
    return step, cleaned


def define_metrics(wandb: Any) -> None:
    wandb.define_metric("train/step")
    wandb.define_metric("train/*", step_metric="train/step")
    for prefix in (
        "eval",
        "dfm_eval",
        "euroeval",
        "avg",
        "headline_avg",
        "headline_avg_v2",
        "headline_avg_v3",
        "headline_avg_v4",
        "suite_avg",
        "suite_avg_v2",
        "suite_avg_v3",
        "suite_avg_v4",
    ):
        epoch_key = f"{prefix}/epoch"
        train_step_key = f"{prefix}/train_step"
        wandb.define_metric(epoch_key)
        wandb.define_metric(train_step_key)
        wandb.define_metric(f"{prefix}/*", step_metric=epoch_key)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entity", default="peter-sk-sdu")
    parser.add_argument("--source-project", default="DFM5")
    parser.add_argument("--source-run-id", default="dfm6-dfm7-xl-gas2")
    parser.add_argument("--dest-project", default="DFM5")
    parser.add_argument("--dest-run-id", default="dfm8-xl-from-dfm6-dfm7-epoch5")
    parser.add_argument("--dest-run-name", default="DFM8-XL from DFM6-DFM7 epoch5")
    parser.add_argument("--max-step", type=int, default=1229504)
    parser.add_argument("--page-size", type=int, default=5000)
    parser.add_argument("--audit-jsonl", type=Path, default=Path("logs/dfm8/dfm8_xl_from_dfm6_dfm7_backfill_rows.jsonl"))
    parser.add_argument("--use-existing-audit", action="store_true")
    parser.add_argument("--allow-deprecated", action="store_true", help="Acknowledge this deprecated script's known W&B history issues.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--wandb-mode", choices=("online", "offline"), default="online")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.allow_deprecated:
        raise SystemExit(
            "This script is deprecated after producing misleading W&B history. "
            "Use --allow-deprecated only for forensic reproduction, not for a production backfill."
        )
    import wandb

    api = wandb.Api(timeout=120)
    source = api.run(f"{args.entity}/{args.source_project}/{args.source_run_id}")

    if args.use_existing_audit:
        rows: list[tuple[int, dict[str, float | int]]] = []
        for line in args.audit_jsonl.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            rows.append((int(rec["step"]), dict(rec["row"])))
        scanned = None
    else:
        rows_by_step: dict[int, dict[str, float | int]] = {}
        scanned = 0
        for raw in source.scan_history(page_size=args.page_size):
            scanned += 1
            step, cleaned = clean_history_row(raw)
            if step is None or step > args.max_step or not cleaned:
                continue
            rows_by_step.setdefault(step, {}).update(cleaned)
        rows = sorted(rows_by_step.items(), key=lambda item: item[0])
        args.audit_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with args.audit_jsonl.open("w", encoding="utf-8") as handle:
            for step, row in rows:
                handle.write(json.dumps({"step": step, "row": row}, sort_keys=True) + "\n")

    eval_like_rows = sum(
        1
        for _, row in rows
        if any(key.startswith(DEFAULT_EVAL_PREFIXES) for key in row)
    )
    summary = {
        "source": f"{args.entity}/{args.source_project}/{args.source_run_id}",
        "dest": f"{args.entity}/{args.dest_project}/{args.dest_run_id}",
        "dest_name": args.dest_run_name,
        "scanned_source_rows": scanned,
        "rows": len(rows),
        "eval_like_rows": eval_like_rows,
        "min_step": rows[0][0] if rows else None,
        "max_step": rows[-1][0] if rows else None,
        "audit_jsonl": str(args.audit_jsonl),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.dry_run:
        return

    target_config = dict(source.config)
    target_config.update(
        {
            "data": {"path": "data/sampled_dfm8", "target_only": True},
            "run_name": args.dest_run_name,
            "project_name": args.dest_project,
            "checkpoint_path": "checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5",
            "resume_checkpoint_path": "checkpoints/dfm7/XL-gas2-from-dfm6-epoch3",
            "resume_checkpoint_tag": "epoch_5",
            "resume_source_project": args.source_project,
            "resume_source_run_id": args.source_run_id,
            "resume_source_checkpoint_step": args.max_step,
            "resume_source_data_until_step": "data/sampled_dfm7",
            "resume_target_data_from_next_step": "data/sampled_dfm8",
            "dfm8_pretraining_gate": (
                "Run and integrate dfm8_openhermes_da before restarting training."
            ),
        }
    )

    run = wandb.init(
        entity=args.entity,
        project=args.dest_project,
        id=args.dest_run_id,
        name=args.dest_run_name,
        resume="never",
        mode=args.wandb_mode,
        config=target_config,
        tags=["dfm8", "xl", "gas2", "dfm6-dfm7-continuation", "epoch5-backfill"],
        settings=wandb.Settings(init_timeout=300),
    )
    assert run is not None
    define_metrics(wandb)
    for step, row in rows:
        row.setdefault("train/step", step)
        wandb.log(row, step=step, commit=True)
    run.summary["dfm8_backfill/source_run"] = f"{args.entity}/{args.source_project}/{args.source_run_id}"
    run.summary["dfm8_backfill/backfilled_through_step"] = args.max_step
    run.summary["dfm8_backfill/resume_checkpoint_path"] = "checkpoints/dfm7/XL-gas2-from-dfm6-epoch3"
    run.summary["dfm8_backfill/resume_checkpoint_tag"] = "epoch_5"
    run.summary["dfm8_backfill/target_data"] = "data/sampled_dfm8"
    run.summary["dfm8_backfill/audit_jsonl"] = str(args.audit_jsonl)
    run.summary["dfm8_backfill/pretraining_gate"] = "dfm8_openhermes_da generation/audit/integration before training"
    wandb.finish()


if __name__ == "__main__":
    main()
