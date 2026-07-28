#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from eval_scheduler.eval_scheduler.model import Action, read_plan


EVENT_RE = re.compile(r"(START|END) (\S+)")
METRIC_FILENAMES = {
    "merged_metrics.json",
    "merged_ifeval_da_metrics.json",
    "wandb_metrics.json",
}


def event_times(plan_dir: Path) -> dict[str, dict[str, datetime]]:
    events: dict[str, dict[str, datetime]] = {}
    for line in (plan_dir / "status.tsv").read_text().splitlines():
        timestamp, _, message = line.partition("\t")
        match = EVENT_RE.match(message)
        if not match:
            continue
        events.setdefault(match.group(2), {})[match.group(1)] = (
            datetime.fromisoformat(timestamp)
        )
    return events


def selected_jobs(plan_dir: Path, checkpoint_tag: str):
    return [
        job
        for job in read_plan(plan_dir / "plan.tsv")
        if str(job.metadata.get("ckpt_tag", "")) == checkpoint_tag
    ]


def timing(plan_dir: Path, checkpoint_tag: str) -> dict[str, float | int | None]:
    jobs = selected_jobs(plan_dir, checkpoint_tag)
    events = event_times(plan_dir)
    eval_actions = {
        Action.EVAL_STANDARD,
        Action.EVAL_DFM,
        Action.EVAL_DFM_IFEVAL,
        Action.EVAL_EUROEVAL,
        Action.EVAL_EUROEVAL_BATCHED_IFEVAL,
    }
    intervals = []
    for job in jobs:
        if job.action not in eval_actions:
            continue
        job_events = events.get(job.job_id, {})
        if "START" in job_events and "END" in job_events:
            intervals.append((job_events["START"], job_events["END"]))
    if not intervals:
        return {
            "completed_eval_jobs": 0,
            "gpu_job_seconds": 0.0,
            "wall_span_seconds": None,
        }
    return {
        "completed_eval_jobs": len(intervals),
        "gpu_job_seconds": sum((end - start).total_seconds() for start, end in intervals),
        "wall_span_seconds": (
            max(end for _, end in intervals) - min(start for start, _ in intervals)
        ).total_seconds(),
    }


def flatten_metrics(value: object, prefix: str = "") -> dict[str, float]:
    output: dict[str, float] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}/{key}" if prefix else str(key)
            output.update(flatten_metrics(item, path))
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        if math.isfinite(number):
            output[prefix] = number
    return output


def metrics(plan_dir: Path, checkpoint_tag: str) -> dict[str, float]:
    jobs = selected_jobs(plan_dir, checkpoint_tag)
    roots = {Path(job.log_dir) for job in jobs if job.log_dir}
    output: dict[str, float] = {}
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            if path.name not in METRIC_FILENAMES or path in seen:
                continue
            seen.add(path)
            try:
                values = flatten_metrics(json.loads(path.read_text()))
            except (OSError, json.JSONDecodeError):
                continue
            for key, value in values.items():
                if "/" in key and not key.endswith("/epoch"):
                    output[key] = value
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-plan-dir", type=Path, required=True)
    parser.add_argument("--candidate-plan-dir", type=Path, required=True)
    parser.add_argument("--checkpoint-tag", default="step_100000")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tolerance", type=float, default=1e-6)
    args = parser.parse_args()

    baseline_metrics = metrics(args.baseline_plan_dir, args.checkpoint_tag)
    candidate_metrics = metrics(args.candidate_plan_dir, args.checkpoint_tag)
    shared = sorted(set(baseline_metrics) & set(candidate_metrics))
    differences = [
        {
            "metric": key,
            "baseline": baseline_metrics[key],
            "candidate": candidate_metrics[key],
            "absolute_difference": abs(candidate_metrics[key] - baseline_metrics[key]),
        }
        for key in shared
        if abs(candidate_metrics[key] - baseline_metrics[key]) > args.tolerance
    ]
    result = {
        "baseline_plan_dir": str(args.baseline_plan_dir),
        "candidate_plan_dir": str(args.candidate_plan_dir),
        "checkpoint_tag": args.checkpoint_tag,
        "baseline_timing": timing(args.baseline_plan_dir, args.checkpoint_tag),
        "candidate_timing": timing(args.candidate_plan_dir, args.checkpoint_tag),
        "baseline_metric_count": len(baseline_metrics),
        "candidate_metric_count": len(candidate_metrics),
        "shared_metric_count": len(shared),
        "missing_from_candidate": sorted(set(baseline_metrics) - set(candidate_metrics)),
        "new_in_candidate": sorted(set(candidate_metrics) - set(baseline_metrics)),
        "differences_over_tolerance": differences,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
