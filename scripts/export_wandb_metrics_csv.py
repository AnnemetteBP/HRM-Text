#!/usr/bin/env python3
"""Export unsampled W&B training and evaluation history to a tidy CSV."""

from __future__ import annotations

import argparse
import csv
import math
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any


METRIC_PREFIXES = (
    "train/",
    "eval/",
    "dfm_eval/",
    "euroeval/",
    "headline_avg_v3/",
    "suite_avg_v3/",
)
STANDALONE_METRICS = {"bp_steps"}
FIELDNAMES = (
    "entity",
    "project",
    "run_id",
    "run_name",
    "wandb_step",
    "timestamp",
    "runtime",
    "namespace",
    "metric",
    "value",
    "metric_epoch",
    "metric_train_step",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_path", help="W&B entity/project/run_id path")
    parser.add_argument("output", type=Path)
    parser.add_argument("--page-size", type=int, default=1000)
    parser.add_argument("--progress-every", type=int, default=10_000)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--workers", type=int, default=1)
    return parser.parse_args()


def is_metric_key(key: str) -> bool:
    return key in STANDALONE_METRICS or key.startswith(METRIC_PREFIXES)


def finite_number(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    return None


def namespace(metric: str) -> str:
    if metric == "bp_steps" or metric.startswith("train/"):
        return "train"
    return metric.split("/", 1)[0]


def export_range(
    run_path: str,
    output: Path,
    metric_keys: set[str],
    page_size: int,
    progress_every: int,
    timeout: int,
    min_step: int | None,
    max_step: int | None,
) -> tuple[int, int, Path]:
    import wandb

    run = wandb.Api(timeout=timeout).run(run_path)
    observations = 0
    history_rows = 0
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        for row in run.scan_history(
            page_size=page_size,
            min_step=min_step,
            max_step=max_step,
        ):
            history_rows += 1
            wandb_step = row.get("_step")
            timestamp = row.get("_timestamp")
            runtime = row.get("_runtime")
            for metric, raw_value in row.items():
                if metric not in metric_keys:
                    continue
                value = finite_number(raw_value)
                if value is None:
                    continue
                metric_namespace = namespace(metric)
                if metric_namespace == "train":
                    metric_epoch = ""
                    metric_train_step = row.get("train/step", wandb_step)
                else:
                    metric_epoch = row.get(f"{metric_namespace}/epoch", "")
                    metric_train_step = row.get(
                        f"{metric_namespace}/train_step", wandb_step
                    )
                writer.writerow(
                    {
                        "entity": run.entity,
                        "project": run.project,
                        "run_id": run.id,
                        "run_name": run.name,
                        "wandb_step": wandb_step,
                        "timestamp": timestamp,
                        "runtime": runtime,
                        "namespace": metric_namespace,
                        "metric": metric,
                        "value": value,
                        "metric_epoch": metric_epoch,
                        "metric_train_step": metric_train_step,
                    }
                )
                observations += 1

            if progress_every and history_rows % progress_every == 0:
                print(
                    f"range={min_step or 0}-{max_step or 'end'} "
                    f"history_rows={history_rows} observations={observations}",
                    file=sys.stderr,
                    flush=True,
                )
    return history_rows, observations, output


def main() -> None:
    args = parse_args()

    import wandb

    run = wandb.Api(timeout=args.timeout).run(args.run_path)
    history_keys = run._attrs.get("historyKeys", {}).get("keys", {})
    metric_keys = {key for key in history_keys if is_metric_key(key)}
    expected_rows = int(run._attrs.get("historyLineCount") or 0)
    max_history_step = int(
        history_keys.get("_step", {}).get("previousValue") or expected_rows
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    workers = max(1, args.workers)
    if workers == 1:
        parts = [
            export_range(
                args.run_path,
                args.output.with_suffix(args.output.suffix + ".part000"),
                metric_keys,
                args.page_size,
                args.progress_every,
                args.timeout,
                None,
                None,
            )
        ]
    else:
        width = math.ceil((max_history_step + 1) / workers)
        ranges = [
            (index * width, min(max_history_step, (index + 1) * width - 1))
            for index in range(workers)
            if index * width <= max_history_step
        ]
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(
                    export_range,
                    args.run_path,
                    args.output.with_suffix(args.output.suffix + f".part{index:03d}"),
                    metric_keys,
                    args.page_size,
                    args.progress_every,
                    args.timeout,
                    min_step,
                    max_step,
                )
                for index, (min_step, max_step) in enumerate(ranges)
            ]
            parts = [future.result() for future in as_completed(futures)]

    parts.sort(key=lambda item: item[2].name)
    history_rows = sum(item[0] for item in parts)
    observations = sum(item[1] for item in parts)
    with args.output.open("w", encoding="utf-8", newline="") as output_handle:
        writer = csv.DictWriter(output_handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for _, _, part_path in parts:
            with part_path.open("r", encoding="utf-8", newline="") as part_handle:
                shutil.copyfileobj(part_handle, output_handle)
            part_path.unlink()

    print(
        f"Exported {observations} observations from {history_rows} history rows "
        f"and {len(metric_keys)} metric keys to {args.output}"
    )


if __name__ == "__main__":
    main()
