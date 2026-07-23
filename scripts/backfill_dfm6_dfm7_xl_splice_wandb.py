#!/usr/bin/env python3
"""Backfill DFM6 XL-GAS2 history into a new DFM6->DFM7 splice run.

The intended use is to prepare a clean W&B run up to the completed DFM6 epoch 3
checkpoint, then resume training from that checkpoint with DFM7 data.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


SYSTEM_KEYS = {"_runtime", "_timestamp", "_step"}
EVAL_PREFIXES = (
    "eval/",
    "dfm_eval/",
    "euroeval/",
    "avg/",
    "headline_avg/",
    "headline_avg_v2/",
    "suite_avg/",
    "suite_avg_v2/",
)
TRAIN_STEP_KEYS = (
    "eval/train_step",
    "dfm_eval/train_step",
    "euroeval/train_step",
    "avg/train_step",
    "headline_avg/train_step",
    "headline_avg_v2/train_step",
    "suite_avg/train_step",
    "suite_avg_v2/train_step",
)
EPOCH_KEYS = (
    "eval/epoch",
    "dfm_eval/epoch",
    "euroeval/epoch",
    "avg/epoch",
    "headline_avg/epoch",
    "headline_avg_v2/epoch",
    "suite_avg/epoch",
    "suite_avg_v2/epoch",
)


def finite_number(value: Any) -> float | int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return None


def clean_training_row(row: dict[str, Any]) -> tuple[int | None, dict[str, float | int]]:
    step = row.get("_step")
    if not isinstance(step, int):
        return None, {}
    cleaned: dict[str, float | int] = {}
    for key, value in row.items():
        if key in SYSTEM_KEYS or key.startswith("_"):
            continue
        if str(key).startswith(EVAL_PREFIXES):
            continue
        parsed = finite_number(value)
        if parsed is not None:
            cleaned[str(key)] = parsed
    return step, cleaned


def eval_train_step(row: dict[str, Any]) -> int | None:
    for key in TRAIN_STEP_KEYS:
        value = row.get(key)
        parsed = finite_number(value)
        if parsed is not None:
            return int(parsed)
    return None


def clean_eval_row(row: dict[str, Any]) -> tuple[int | None, dict[str, float | int]]:
    step = eval_train_step(row)
    if step is None:
        return None, {}
    cleaned: dict[str, float | int] = {}
    for key, value in row.items():
        key = str(key)
        if key in SYSTEM_KEYS or key.startswith("_"):
            continue
        if not key.startswith(EVAL_PREFIXES):
            continue
        # Drop summary convenience keys such as metric/epoch_0p208... from the
        # history row; keep canonical metric keys and explicit axes.
        if "/epoch_" in key or key.endswith("/last_epoch"):
            continue
        parsed = finite_number(value)
        if parsed is not None:
            cleaned[key] = parsed
    for axis_key in TRAIN_STEP_KEYS:
        prefix = axis_key.split("/", 1)[0]
        if any(key.startswith(f"{prefix}/") for key in cleaned):
            cleaned[axis_key] = step
    for axis_key in EPOCH_KEYS:
        if axis_key in row:
            parsed = finite_number(row[axis_key])
            if parsed is not None:
                cleaned[axis_key] = parsed
    return step, cleaned


def define_metrics(wandb: Any) -> None:
    for prefix in ("eval", "dfm_eval", "euroeval", "headline_avg_v2", "suite_avg_v2", "avg", "headline_avg", "suite_avg"):
        epoch_key = f"{prefix}/epoch"
        train_step_key = f"{prefix}/train_step"
        wandb.define_metric(epoch_key)
        wandb.define_metric(train_step_key)
        wandb.define_metric(f"{prefix}/*", step_metric=epoch_key)
    wandb.define_metric("train/*", step_metric="train/step")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entity", default="peter-sk-sdu")
    parser.add_argument("--source-project", default="DFM5")
    parser.add_argument("--source-run-id", default="39ht9plp")
    parser.add_argument("--eval-source-project", default="DFM5")
    parser.add_argument("--eval-source-run-id", default="dfm6-xl-gas2-300k-stopfix-clean-20260624")
    parser.add_argument("--dest-project", default="DFM5")
    parser.add_argument("--dest-run-id", default="dfm6-dfm7-xl-gas2")
    parser.add_argument("--dest-run-name", default="DFM6-DFM7-XL-gas2")
    parser.add_argument("--max-step", type=int, default=720084)
    parser.add_argument("--max-eval-step", type=int, default=700000)
    parser.add_argument("--page-size", type=int, default=5000)
    parser.add_argument("--audit-jsonl", type=Path, default=Path("logs/dfm7/dfm6_dfm7_xl_backfill_rows.jsonl"))
    parser.add_argument("--use-existing-audit", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--wandb-mode", choices=("online", "offline"), default="online")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    import wandb

    api = wandb.Api(timeout=120)
    source = api.run(f"{args.entity}/{args.source_project}/{args.source_run_id}")
    eval_source = api.run(f"{args.entity}/{args.eval_source_project}/{args.eval_source_run_id}")

    if args.use_existing_audit:
        rows: list[tuple[int, dict[str, float | int]]] = []
        for line in args.audit_jsonl.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            rows.append((int(rec["step"]), dict(rec["row"])))
    else:
        rows_by_step: dict[int, dict[str, float | int]] = {}
        scanned = 0
        for raw in source.scan_history(page_size=args.page_size):
            scanned += 1
            step, cleaned = clean_training_row(raw)
            if step is None or step > args.max_step or not cleaned:
                continue
            rows_by_step.setdefault(step, {}).update(cleaned)
        eval_scanned = 0
        eval_rows = 0
        for raw in eval_source.scan_history(page_size=args.page_size):
            eval_scanned += 1
            step, cleaned = clean_eval_row(raw)
            if step is None or step > args.max_eval_step or not cleaned:
                continue
            rows_by_step.setdefault(step, {}).update(cleaned)
            eval_rows += 1
        rows = sorted(rows_by_step.items(), key=lambda item: item[0])
        args.audit_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with args.audit_jsonl.open("w", encoding="utf-8") as handle:
            for step, row in rows:
                handle.write(json.dumps({"step": step, "row": row}, sort_keys=True) + "\n")
        print(f"scanned_source_rows={scanned}")
        print(f"scanned_eval_source_rows={eval_scanned}")
        print(f"used_eval_source_rows={eval_rows}")

    eval_like_rows = sum(
        1
        for _, row in rows
        if any(key.startswith(("eval/", "dfm_eval/", "euroeval/", "headline_avg", "suite_avg", "avg/")) for key in row)
    )
    summary = {
        "source": f"{args.entity}/{args.source_project}/{args.source_run_id}",
        "eval_source": f"{args.entity}/{args.eval_source_project}/{args.eval_source_run_id}",
        "dest": f"{args.entity}/{args.dest_project}/{args.dest_run_id}",
        "rows": len(rows),
        "eval_like_rows": eval_like_rows,
        "min_step": rows[0][0] if rows else None,
        "max_step": rows[-1][0] if rows else None,
        "audit_jsonl": str(args.audit_jsonl),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.dry_run:
        return

    source_config = dict(source.config)
    target_config = dict(source_config)
    target_config["data"] = {"path": "data/sampled_dfm7", "target_only": True}
    target_config["run_name"] = args.dest_run_name
    target_config["checkpoint_path"] = "checkpoints/dfm7/XL-gas2-from-dfm6-epoch3"
    target_config["resume_checkpoint_path"] = "checkpoints/dfm6/XL-gas2"
    target_config["resume_checkpoint_tag"] = "epoch_3"
    target_config["splice_source_project"] = args.source_project
    target_config["splice_source_run_id"] = args.source_run_id
    target_config["splice_eval_source_project"] = args.eval_source_project
    target_config["splice_eval_source_run_id"] = args.eval_source_run_id
    target_config["splice_eval_source_max_step"] = args.max_eval_step
    target_config["splice_source_max_step"] = args.max_step
    target_config["splice_source_data_until_step"] = "data/sampled_dfm6"
    target_config["splice_target_data_from_next_step"] = "data/sampled_dfm7"

    run = wandb.init(
        entity=args.entity,
        project=args.dest_project,
        id=args.dest_run_id,
        name=args.dest_run_name,
        resume="allow",
        mode=args.wandb_mode,
        config=target_config,
        tags=["dfm7", "dfm6-splice", "xl", "gas2"],
        settings=wandb.Settings(init_timeout=300),
    )
    assert run is not None
    define_metrics(wandb)
    for step, row in rows:
        # Add an explicit train step axis where absent. This helps W&B panels
        # avoid relying on the internal history _step if metrics are relogged.
        row.setdefault("train/step", step)
        wandb.log(row, step=step, commit=True)
    run.summary["splice/backfilled_through_step"] = args.max_step
    run.summary["splice/source_run"] = f"{args.entity}/{args.source_project}/{args.source_run_id}"
    run.summary["splice/eval_source_run"] = f"{args.entity}/{args.eval_source_project}/{args.eval_source_run_id}"
    run.summary["splice/eval_source_max_step"] = args.max_eval_step
    run.summary["splice/source_data_until_step"] = "data/sampled_dfm6"
    run.summary["splice/target_data_from_next_step"] = "data/sampled_dfm7"
    wandb.finish()


if __name__ == "__main__":
    main()
