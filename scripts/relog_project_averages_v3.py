#!/usr/bin/env python3
"""Relog corrected v3 headline and suite averages for W&B project runs.

The script reads raw eval metrics from W&B history and writes only new average
namespaces. It is intended for backfilling corrected averages after changing
normalization rules without mutating old v2 keys.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import wandb
from wandb.proto import wandb_internal_pb2
from wandb.sdk.internal.datastore import DataStore

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from log_dfm5_headline_averages import SECTION_KEYS, SUITE_KEYS, section_average  # noqa: E402


SOURCE_KEYS = sorted({key for keys in [*SECTION_KEYS.values(), *SUITE_KEYS.values()] for key in keys})
SOURCE_PREFIXES = ("eval", "dfm_eval", "euroeval")


@dataclass
class Bucket:
    step: int | None = None
    epoch: float | None = None
    metrics: dict[str, float] = field(default_factory=dict)


def finite_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    return None


def finite_int(value: Any) -> int | None:
    parsed = finite_float(value)
    if parsed is None:
        return None
    return int(parsed)


def key_prefix(metric: str) -> str:
    return metric.split("/", 1)[0]


def row_axis(row: dict[str, Any], metric: str) -> tuple[int | None, float | None]:
    prefix = key_prefix(metric)
    step = finite_int(row.get(f"{prefix}/train_step"))
    epoch = finite_float(row.get(f"{prefix}/epoch"))
    if step is None:
        for alt in ("eval/train_step", "dfm_eval/train_step", "euroeval/train_step"):
            step = finite_int(row.get(alt))
            if step is not None:
                break
    if epoch is None:
        for alt in ("eval/epoch", "dfm_eval/epoch", "euroeval/epoch"):
            epoch = finite_float(row.get(alt))
            if epoch is not None:
                break
    return step, epoch


def bucket_key(step: int | None, epoch: float | None) -> tuple[str, int | str]:
    if step is not None and step > 0:
        return ("step", step)
    if epoch is not None:
        return ("epoch", f"{epoch:.12g}")
    return ("unknown", "unknown")


def collect_run_buckets(run: Any, *, page_size: int) -> dict[tuple[str, int | str], Bucket]:
    axis_keys = []
    for prefix in SOURCE_PREFIXES:
        axis_keys.extend([f"{prefix}/epoch", f"{prefix}/train_step"])
    keys = SOURCE_KEYS + axis_keys
    buckets: dict[tuple[str, int | str], Bucket] = defaultdict(Bucket)
    for row in run.scan_history(keys=keys, page_size=page_size):
        for metric in SOURCE_KEYS:
            value = finite_float(row.get(metric))
            if value is None:
                continue
            step, epoch = row_axis(row, metric)
            if step is None and epoch is None:
                continue
            bucket = buckets[bucket_key(step, epoch)]
            if step is not None:
                bucket.step = step
            if epoch is not None:
                bucket.epoch = epoch
            bucket.metrics[metric] = value
    return dict(buckets)


def iter_records(path: Path):
    ds = DataStore()
    ds.open_for_scan(str(path))
    while True:
        data = ds.scan_data()
        if data is None:
            break
        record = wandb_internal_pb2.Record()
        record.ParseFromString(data)
        yield record


def item_key(item: Any) -> str:
    if len(item.nested_key) > 1:
        return ".".join(item.nested_key)
    if len(item.nested_key) == 1:
        return item.nested_key[0]
    return item.key


def item_value(item: Any) -> Any:
    try:
        return json.loads(item.value_json)
    except json.JSONDecodeError:
        return item.value_json


def history_row(record: wandb_internal_pb2.Record) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for item in record.history.item:
        row[item_key(item)] = item_value(item)
    if record.history.HasField("step"):
        row.setdefault("_step", int(record.history.step.num))
    return row


def local_wandb_files(wandb_root: Path, run_id: str) -> list[Path]:
    return sorted(wandb_root.glob(f"run-*-{run_id}/run-{run_id}.wandb"))


def collect_local_buckets(run_id: str, *, wandb_root: Path) -> dict[tuple[str, int | str], Bucket]:
    buckets: dict[tuple[str, int | str], Bucket] = defaultdict(Bucket)
    seen_rows: set[str] = set()
    for path in local_wandb_files(wandb_root, run_id):
        for record in iter_records(path):
            if record.WhichOneof("record_type") != "history":
                continue
            row = history_row(record)
            signature = json.dumps(row, sort_keys=True, default=str)
            if signature in seen_rows:
                continue
            seen_rows.add(signature)
            for metric in SOURCE_KEYS:
                value = finite_float(row.get(metric))
                if value is None:
                    continue
                step, epoch = row_axis(row, metric)
                if step is None and epoch is None:
                    continue
                bucket = buckets[bucket_key(step, epoch)]
                if step is not None:
                    bucket.step = step
                if epoch is not None:
                    bucket.epoch = epoch
                bucket.metrics[metric] = value
    return dict(buckets)


def average_rows_for_bucket(bucket: Bucket) -> dict[str, float | int]:
    if bucket.epoch is None:
        raise ValueError("Cannot log averages without an epoch axis")
    row: dict[str, float | int] = {
        "headline_avg_v3/epoch": bucket.epoch,
        "suite_avg_v3/epoch": bucket.epoch,
    }
    if bucket.step is not None:
        row["headline_avg_v3/train_step"] = bucket.step
        row["suite_avg_v3/train_step"] = bucket.step

    section_values: list[float] = []
    for section, keys in SECTION_KEYS.items():
        avg, count = section_average(bucket.metrics, keys)
        row[f"headline_avg_v3/{section}/count"] = count
        if avg is not None:
            row[f"headline_avg_v3/{section}"] = avg
            section_values.append(avg)
    if section_values:
        row["headline_avg_v3/overall"] = sum(section_values) / len(section_values)

    for suite, keys in SUITE_KEYS.items():
        avg, count = section_average(bucket.metrics, keys)
        row[f"suite_avg_v3/{suite}/count"] = count
        if avg is not None:
            row[f"suite_avg_v3/{suite}"] = avg
    return row


def define_metrics() -> None:
    for prefix in ("headline_avg_v3", "suite_avg_v3"):
        wandb.define_metric(f"{prefix}/epoch")
        wandb.define_metric(f"{prefix}/train_step")
        wandb.define_metric(f"{prefix}/*", step_metric=f"{prefix}/epoch")


def iter_runs(api: wandb.Api, entity: str, project: str, run_ids: list[str]) -> list[Any]:
    if run_ids:
        return [api.run(f"{entity}/{project}/{run_id}") for run_id in run_ids]
    return list(api.runs(f"{entity}/{project}"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entity", default="peter-sk-sdu")
    parser.add_argument("--project", default="DFM5")
    parser.add_argument("--run-id", action="append", default=[], help="Restrict to one run id. Repeatable.")
    parser.add_argument("--name-contains", action="append", default=[], help="Restrict to display names containing this substring.")
    parser.add_argument("--source", choices=("local", "api"), default="local")
    parser.add_argument("--wandb-root", type=Path, default=Path("wandb"))
    parser.add_argument("--page-size", type=int, default=2000)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--audit", type=Path, default=Path("logs/relog_project_averages_v3_audit.jsonl"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api = wandb.Api(timeout=180)
    runs = iter_runs(api, args.entity, args.project, args.run_id)
    if args.name_contains:
        needles = [needle.lower() for needle in args.name_contains]
        runs = [run for run in runs if any(needle in (run.name or "").lower() for needle in needles)]

    audit_records: list[dict[str, Any]] = []
    for source_run in runs:
        if args.source == "local":
            buckets = collect_local_buckets(source_run.id, wandb_root=args.wandb_root)
        else:
            buckets = collect_run_buckets(source_run, page_size=args.page_size)
        rows = []
        for key, bucket in sorted(
            buckets.items(),
            key=lambda item: (
                item[1].epoch if item[1].epoch is not None else float("inf"),
                item[1].step if item[1].step is not None else 10**18,
                str(item[0]),
            ),
        ):
            if not bucket.metrics or bucket.epoch is None:
                continue
            row = average_rows_for_bucket(bucket)
            rows.append(row)
            audit_records.append(
                {
                    "run_id": source_run.id,
                    "run_name": source_run.name,
                    "bucket": key,
                    "epoch": bucket.epoch,
                    "step": bucket.step,
                    "metric_count": len(bucket.metrics),
                    "row": row,
                }
            )
        print(f"{source_run.id}\t{source_run.name}\trows={len(rows)}")
        if args.dry_run or not rows:
            continue
        target = wandb.init(
            entity=args.entity,
            project=args.project,
            id=source_run.id,
            name=source_run.name,
            resume="allow",
            settings=wandb.Settings(init_timeout=300),
        )
        assert target is not None
        define_metrics()
        for row in rows:
            wandb.log(row, commit=True)
        target.finish()

    args.audit.parent.mkdir(parents=True, exist_ok=True)
    with args.audit.open("w", encoding="utf-8") as f:
        for record in audit_records:
            f.write(json.dumps(record, sort_keys=True) + "\n")
    print(f"audit\t{args.audit}\trecords={len(audit_records)}")


if __name__ == "__main__":
    main()
