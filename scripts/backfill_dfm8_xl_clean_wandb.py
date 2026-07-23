#!/usr/bin/env python3
"""Create a clean DFM8-XL continuation W&B run from deterministic local rows.

This is the replacement for the deprecated broad W&B-history clone. It uses
local audit rows that were already verified for the DFM6->DFM7 XL run:

- dense train/eval rows through 1.2M:
  logs/dfm8/dfm8_xl_from_dfm6_dfm7_backfill_rows.jsonl
- local W&B training fragments after 1.0M, read directly from ``run-*.wandb``
  files using W&B's internal datastore reader

The script intentionally filters to canonical train/eval namespaces and v3
average namespaces. It does not replay stale v2 averages or W&B summary helper
keys such as ``*/epoch_5``.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


TRAIN_KEYS = {
    "train/step",
    "train/loss",
    "train/accuracy",
    "train/exact_accuracy",
    "train/lr",
    "bp_steps",
}
CANONICAL_PREFIXES = (
    "eval/",
    "dfm_eval/",
    "euroeval/",
    "headline_avg_v3/",
    "suite_avg_v3/",
)
DROP_PREFIXES = (
    "avg/",
    "headline_avg/",
    "headline_avg_v2/",
    "headline_avg_v4/",
    "suite_avg/",
    "suite_avg_v2/",
    "suite_avg_v4/",
    "lite_eval",
    "lite_dfm_eval",
)
REQUIRED_EVAL_STEPS = (
    50_000,
    100_000,
    150_000,
    200_000,
    250_000,
    300_000,
    350_000,
    400_000,
    450_000,
    500_000,
    550_000,
    600_000,
    650_000,
    700_000,
    750_000,
    800_000,
    850_000,
    900_000,
    950_000,
    1_000_000,
    1_050_000,
    1_100_000,
    1_150_000,
    1_200_000,
)


def finite_number(value: Any) -> float | int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    return None


def keep_key(key: str) -> bool:
    if key in TRAIN_KEYS:
        return True
    if key.startswith("_"):
        return False
    if "/epoch_" in key or key.endswith("/last_epoch"):
        return False
    if key.startswith(DROP_PREFIXES):
        return False
    return key.startswith(CANONICAL_PREFIXES)


def has_train_metric(row: dict[str, float | int]) -> bool:
    return any(key in row for key in ("train/loss", "train/accuracy", "train/exact_accuracy", "train/lr", "bp_steps"))


def load_rows(path: Path) -> dict[int, dict[str, float | int]]:
    rows: dict[int, dict[str, float | int]] = {}
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            rec = json.loads(line)
            step = int(rec["step"])
            raw_row = dict(rec["row"])
            cleaned: dict[str, float | int] = {}
            for raw_key, raw_value in raw_row.items():
                key = str(raw_key)
                if not keep_key(key):
                    continue
                value = finite_number(raw_value)
                if value is not None:
                    cleaned[key] = value
            if not cleaned:
                continue
            if has_train_metric(cleaned):
                cleaned["train/step"] = step
            rows.setdefault(step, {}).update(cleaned)
    return rows


def json_number(value_json: str) -> float | int | None:
    try:
        value = json.loads(value_json)
    except Exception:
        return None
    return finite_number(value)


def extract_local_wandb_train_rows(wandb_root: Path, min_step: int) -> dict[int, dict[str, float | int]]:
    from wandb.proto import wandb_internal_pb2
    from wandb.sdk.internal.datastore import DataStore

    rows: dict[int, dict[str, float | int]] = {}
    for path in sorted(wandb_root.glob("run-*/run-dfm6-dfm7-xl-gas2.wandb")):
        try:
            datastore = DataStore()
            datastore.open_for_scan(str(path))
            while True:
                data = datastore.scan_data()
                if data is None:
                    break
                record = wandb_internal_pb2.Record()
                record.ParseFromString(data)
                if record.WhichOneof("record_type") != "history":
                    continue
                raw: dict[str, str] = {}
                for item in record.history.item:
                    key = "/".join(item.nested_key) if item.nested_key else item.key
                    raw[key] = item.value_json
                step_value = json_number(raw.get("_step", "null"))
                if step_value is None:
                    continue
                step = int(step_value)
                if step < min_step:
                    continue
                row: dict[str, float | int] = {}
                for key in ("train/accuracy", "train/exact_accuracy", "train/loss", "train/lr", "bp_steps"):
                    if key in raw:
                        value = json_number(raw[key])
                        if value is not None:
                            row[key] = value
                if not row:
                    continue
                row["train/step"] = step
                # Prefer complete rows over partial/single-metric fragments.
                existing = rows.get(step)
                if existing is None or len(row) > len(existing):
                    rows[step] = row
        except Exception:
            continue
    return rows


def normalize_epoch5_step_zero(rows: dict[int, dict[str, float | int]], resume_step: int) -> None:
    row = rows.get(0)
    if not row:
        return
    epoch_values = [
        row.get("eval/epoch"),
        row.get("dfm_eval/epoch"),
        row.get("euroeval/epoch"),
        row.get("headline_avg_v3/epoch"),
        row.get("suite_avg_v3/epoch"),
    ]
    if not any(value == 5 or value == 5.0 for value in epoch_values):
        return
    moved = rows.pop(0)
    moved.pop("train/step", None)
    for key in (
        "eval/train_step",
        "dfm_eval/train_step",
        "euroeval/train_step",
        "headline_avg_v3/train_step",
        "suite_avg_v3/train_step",
    ):
        if key in moved:
            moved[key] = resume_step
    rows.setdefault(resume_step, {}).update(moved)


def merge_rows(
    main_path: Path,
    resume_step: int,
    wandb_root: Path,
    local_train_min_step: int,
) -> list[tuple[int, dict[str, float | int]]]:
    rows = load_rows(main_path)
    normalize_epoch5_step_zero(rows, resume_step)
    local_train_rows = extract_local_wandb_train_rows(wandb_root, local_train_min_step)
    for step, row in local_train_rows.items():
        target = rows.setdefault(step, {})
        # Replace train metrics at these steps with the original committed rows,
        # while preserving eval/average metrics if the step also has them.
        for key in TRAIN_KEYS:
            target.pop(key, None)
        target.update(row)
    return sorted(rows.items())


def validate_rows(rows: list[tuple[int, dict[str, float | int]]], resume_step: int) -> dict[str, Any]:
    by_step = dict(rows)
    missing_eval_steps = [
        step
        for step in REQUIRED_EVAL_STEPS
        if step not in by_step
        or not any(key.startswith(("eval/", "dfm_eval/", "euroeval/")) for key in by_step[step])
    ]
    missing_avg_steps = [
        step
        for step in REQUIRED_EVAL_STEPS
        if step not in by_step
        or not any(key.startswith(("headline_avg_v3/", "suite_avg_v3/")) for key in by_step[step])
    ]
    train_steps = [
        step
        for step, row in rows
        if any(key in row for key in ("train/loss", "train/accuracy", "train/exact_accuracy", "train/lr", "bp_steps"))
    ]
    non_v3_average_keys = sorted(
        {
            key
            for _, row in rows
            for key in row
            if key.startswith(("avg/", "headline_avg/", "headline_avg_v2/", "headline_avg_v4/", "suite_avg/", "suite_avg_v2/", "suite_avg_v4/"))
        }
    )
    summary = {
        "rows": len(rows),
        "min_step": rows[0][0] if rows else None,
        "max_step": rows[-1][0] if rows else None,
        "resume_step": resume_step,
        "train_metric_rows": len(train_steps),
        "train_metric_min_step": min(train_steps) if train_steps else None,
        "train_metric_max_step": max(train_steps) if train_steps else None,
        "eval_like_rows": sum(
            1
            for _, row in rows
            if any(key.startswith(("eval/", "dfm_eval/", "euroeval/")) for key in row)
        ),
        "average_rows": sum(
            1
            for _, row in rows
            if any(key.startswith(("headline_avg_v3/", "suite_avg_v3/")) for key in row)
        ),
        "missing_eval_steps": missing_eval_steps,
        "missing_avg_steps": missing_avg_steps,
        "non_v3_average_keys": non_v3_average_keys,
    }
    if missing_eval_steps or missing_avg_steps or non_v3_average_keys:
        raise SystemExit(json.dumps({"validation_failed": summary}, indent=2, sort_keys=True))
    return summary


def write_payload(rows: list[tuple[int, dict[str, float | int]]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for step, row in rows:
            handle.write(json.dumps({"step": step, "row": row}, sort_keys=True) + "\n")


def define_metrics(wandb: Any) -> None:
    wandb.define_metric("train/step")
    wandb.define_metric("train/*", step_metric="train/step")
    wandb.define_metric("bp_steps", step_metric="train/step")
    for prefix in ("eval", "dfm_eval", "euroeval", "headline_avg_v3", "suite_avg_v3"):
        epoch_key = f"{prefix}/epoch"
        train_step_key = f"{prefix}/train_step"
        wandb.define_metric(epoch_key)
        wandb.define_metric(train_step_key)
        wandb.define_metric(f"{prefix}/*", step_metric=epoch_key)
    wandb.define_metric("dfm8_backfill/step")
    wandb.define_metric("dfm8_backfill/*", step_metric="dfm8_backfill/step")


def build_config(source_config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    config = dict(source_config)
    config.update(
        {
            "data": {"path": "data/sampled_dfm8", "target_only": True},
            "run_name": args.dest_run_name,
            "project_name": args.dest_project,
            "checkpoint_path": "checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5",
            "resume_checkpoint_path": "checkpoints/dfm7/XL-gas2-from-dfm6-epoch3",
            "resume_checkpoint_tag": "epoch_5",
            "resume_step": args.resume_step,
            "resume_epoch": 5,
            "resume_batch_in_epoch": 0,
            "splice_source_project": args.source_project,
            "splice_source_run_id": args.source_run_id,
            "splice_source_max_step": args.resume_step,
            "splice_source_data_until_step": "data/sampled_dfm7",
            "splice_target_data_from_next_step": "data/sampled_dfm8",
            "dfm8_pretraining_gate": "Integrate accepted dfm8_openhermes_da before DFM8 training restart.",
        }
    )
    return config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entity", default="peter-sk-sdu")
    parser.add_argument("--source-project", default="DFM5")
    parser.add_argument("--source-run-id", default="dfm6-dfm7-xl-gas2")
    parser.add_argument("--dest-project", default="DFM5")
    parser.add_argument("--dest-run-id", default="dfm8-xl-from-dfm6-dfm7-epoch5-clean")
    parser.add_argument("--dest-run-name", default="DFM8-XL clean from DFM6-DFM7 epoch5")
    parser.add_argument("--resume-step", type=int, default=1_229_504)
    parser.add_argument("--main-audit", type=Path, default=Path("logs/dfm8/dfm8_xl_from_dfm6_dfm7_backfill_rows.jsonl"))
    parser.add_argument("--wandb-root", type=Path, default=Path("wandb"))
    parser.add_argument("--local-train-min-step", type=int, default=1_000_005)
    parser.add_argument("--payload-jsonl", type=Path, default=Path("logs/dfm8/dfm8_xl_clean_backfill_payload.jsonl"))
    parser.add_argument("--summary-json", type=Path, default=Path("logs/dfm8/dfm8_xl_clean_backfill_summary.json"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--wandb-mode", choices=("online", "offline"), default="online")
    parser.add_argument("--replace-existing", action="store_true", help="Delete an existing destination run before creating it.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = merge_rows(args.main_audit, args.resume_step, args.wandb_root, args.local_train_min_step)
    summary = validate_rows(rows, args.resume_step)
    summary.update(
        {
            "source": f"{args.entity}/{args.source_project}/{args.source_run_id}",
            "dest": f"{args.entity}/{args.dest_project}/{args.dest_run_id}",
            "dest_name": args.dest_run_name,
            "main_audit": str(args.main_audit),
            "wandb_root": str(args.wandb_root),
            "local_train_min_step": args.local_train_min_step,
            "payload_jsonl": str(args.payload_jsonl),
        }
    )
    write_payload(rows, args.payload_jsonl)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.dry_run:
        return

    import wandb

    api = wandb.Api(timeout=120)
    source = api.run(f"{args.entity}/{args.source_project}/{args.source_run_id}")
    if args.replace_existing:
        try:
            existing = api.run(f"{args.entity}/{args.dest_project}/{args.dest_run_id}")
        except Exception:
            existing = None
        if existing is not None:
            existing.delete()

    run = wandb.init(
        entity=args.entity,
        project=args.dest_project,
        id=args.dest_run_id,
        name=args.dest_run_name,
        resume="never",
        mode=args.wandb_mode,
        config=build_config(dict(source.config), args),
        tags=["dfm8", "xl", "gas2", "dfm6-dfm7-continuation", "epoch5-clean-backfill"],
        settings=wandb.Settings(init_timeout=300),
    )
    assert run is not None
    define_metrics(wandb)
    for step, row in rows:
        wandb.log(row, step=step, commit=True)
    marker = {
        "dfm8_backfill/step": args.resume_step,
        "dfm8_backfill/backfilled_through_step": args.resume_step,
        "dfm8_backfill/source_max_payload_step": rows[-1][0],
        "dfm8_backfill/eval_rows": summary["eval_like_rows"],
        "dfm8_backfill/average_rows": summary["average_rows"],
        "dfm8_backfill/train_metric_rows": summary["train_metric_rows"],
    }
    wandb.log(marker, step=args.resume_step, commit=True)
    run.summary["dfm8_backfill/source_run"] = summary["source"]
    run.summary["dfm8_backfill/backfilled_through_step"] = args.resume_step
    run.summary["dfm8_backfill/resume_checkpoint_path"] = "checkpoints/dfm7/XL-gas2-from-dfm6-epoch3"
    run.summary["dfm8_backfill/resume_checkpoint_tag"] = "epoch_5"
    run.summary["dfm8_backfill/target_data"] = "data/sampled_dfm8"
    run.summary["dfm8_backfill/payload_jsonl"] = str(args.payload_jsonl)
    run.summary["dfm8_backfill/local_train_min_step"] = args.local_train_min_step
    run.summary["dfm8_backfill/pretraining_gate"] = "dfm8_openhermes_da generation/audit/integration before training"
    wandb.finish()


if __name__ == "__main__":
    main()
