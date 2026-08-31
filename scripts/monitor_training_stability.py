#!/usr/bin/env python3
"""Periodically report W&B training stability without modifying the run."""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import wandb


METRICS = (
    "train/loss",
    "train/grad_norm",
    "train/grad_clipped",
    "train/grad_clip_coefficient",
    "train/accuracy",
    "train/exact_accuracy",
    "train/lr",
)


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((len(ordered) - 1) * fraction))
    return ordered[index]


def metric_values(rows: list[dict[str, Any]], key: str) -> list[float]:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return [value for value in values if math.isfinite(value)]


def process_count(pattern: str) -> int:
    result = subprocess.run(
        ["pgrep", "-f", pattern],
        check=False,
        capture_output=True,
        text=True,
    )
    return len(
        [
            line
            for line in result.stdout.splitlines()
            if line.strip() and int(line.strip()) != os.getpid()
        ]
    )


def gpu_summary() -> dict[str, float | int | None]:
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    samples: list[tuple[int, int]] = []
    for line in result.stdout.splitlines():
        try:
            memory, utilization = (int(value.strip()) for value in line.split(","))
        except (TypeError, ValueError):
            continue
        samples.append((memory, utilization))
    if not samples:
        return {"gpu_count": 0, "gpu_memory_mib_mean": None, "gpu_utilization_mean": None}
    return {
        "gpu_count": len(samples),
        "gpu_memory_mib_mean": round(statistics.mean(memory for memory, _ in samples), 1),
        "gpu_utilization_mean": round(statistics.mean(utilization for _, utilization in samples), 1),
    }


def summarize(rows: list[dict[str, Any]], process_pattern: str) -> dict[str, Any]:
    latest = rows[-1]
    losses = metric_values(rows, "train/loss")
    norms = metric_values(rows, "train/grad_norm")
    accuracies = metric_values(rows, "train/accuracy")
    exact = metric_values(rows, "train/exact_accuracy")
    clipped = metric_values(rows, "train/grad_clipped")
    warnings: list[str] = []
    if losses and statistics.median(losses) > 1.4:
        warnings.append("median_loss_above_1.4")
    if losses and max(losses) > 2.0:
        warnings.append("loss_above_2.0")
    if norms and max(norms) > 1.0:
        warnings.append("gradient_clipping_active")
    processes = process_count(process_pattern)
    if processes == 0:
        warnings.append("training_process_absent")

    summary: dict[str, Any] = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "step": int(latest["_step"]),
        "samples": len(rows),
        "lr": latest.get("train/lr"),
        "loss_median": statistics.median(losses) if losses else None,
        "loss_mean": statistics.mean(losses) if losses else None,
        "loss_max": max(losses) if losses else None,
        "grad_norm_median": statistics.median(norms) if norms else None,
        "grad_norm_p95": percentile(norms, 0.95) if norms else None,
        "grad_norm_max": max(norms) if norms else None,
        "clipped_samples": int(sum(clipped)),
        "accuracy_mean": statistics.mean(accuracies) if accuracies else None,
        "exact_accuracy_mean": statistics.mean(exact) if exact else None,
        "training_processes": processes,
        "warnings": warnings,
    }
    summary.update(gpu_summary())
    return summary


def format_summary(summary: dict[str, Any]) -> str:
    def number(key: str, digits: int = 4) -> str:
        value = summary.get(key)
        return "n/a" if value is None else f"{float(value):.{digits}f}"

    warnings = ",".join(summary["warnings"]) or "none"
    return (
        f"{summary['timestamp']} step={summary['step']} lr={number('lr', 7)} "
        f"loss_med={number('loss_median')} loss_max={number('loss_max')} "
        f"grad_med={number('grad_norm_median')} grad_p95={number('grad_norm_p95')} "
        f"grad_max={number('grad_norm_max')} clipped={summary['clipped_samples']}/"
        f"{summary['samples']} acc={number('accuracy_mean')} "
        f"exact={number('exact_accuracy_mean')} gpu_util={number('gpu_utilization_mean', 1)}% "
        f"processes={summary['training_processes']} warnings={warnings}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, help="W&B run path: entity/project/run_id")
    parser.add_argument("--log", type=Path, required=True, help="Append-only JSONL output")
    parser.add_argument("--interval", type=float, default=1800.0)
    parser.add_argument("--window", type=int, default=100, help="Recent W&B steps to summarize")
    parser.add_argument("--min-step", type=int, default=0)
    parser.add_argument("--target-step", type=int)
    parser.add_argument("--process-pattern", default="pretrain.py")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    args.log.parent.mkdir(parents=True, exist_ok=True)
    api = wandb.Api(timeout=90)
    last_step: int | None = None
    while True:
        try:
            run = api.run(args.run)
            history_end = int(run.lastHistoryStep)
            start = max(args.min_step, history_end - args.window + 1)
            rows = [
                row
                for row in run.scan_history(
                    keys=["_step", *METRICS],
                    min_step=start,
                    max_step=history_end,
                    page_size=max(100, args.window),
                )
                if row.get("train/loss") is not None
            ]
            if not rows:
                raise RuntimeError(f"no training rows in W&B history range {start}--{history_end}")
            summary = summarize(rows, args.process_pattern)
            if last_step is not None and summary["step"] <= last_step and summary["training_processes"]:
                summary["warnings"].append("no_wandb_step_progress")
            last_step = summary["step"]
            with args.log.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(summary, sort_keys=True) + "\n")
            print(format_summary(summary), flush=True)
            if args.target_step is not None and summary["step"] >= args.target_step:
                break
        except Exception as exc:  # Keep monitoring through transient W&B/network failures.
            error = {
                "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
                "error": f"{type(exc).__name__}: {exc}",
            }
            with args.log.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(error, sort_keys=True) + "\n")
            print(f"{error['timestamp']} monitor_error={error['error']}", flush=True)
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
