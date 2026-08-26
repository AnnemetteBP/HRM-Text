#!/usr/bin/env python3
"""Log separate long-context task averages and an overall headline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_TASK_METRICS = {
    "ruler_8k": "long_context/ruler_8k/ruler_scorer/mean",
    "govreport_long": "long_context/govreport_long/bertscore_f1/mean",
    "longbench_en": "long_context/longbench_en/long_context_scorer/mean",
    "longalign_en": "long_context/longalign_en/long_context_scorer/mean",
    "longalign_da": "long_context/longalign_da/long_context_scorer/mean",
    "marathon": "long_context/marathon/long_context_scorer/mean",
    "qmsum_cleaned": "long_context/qmsum_cleaned/long_context_scorer/mean",
    "danish_summarization_eur_lex": "long_context/danish_summarization_eur_lex/long_context_scorer/mean",
    "danish_summarization": "long_context/danish_summarization/long_context_scorer/mean",
}


def load_metrics(path: Path) -> dict[str, float]:
    value = json.loads(path.read_text(encoding="utf-8"))
    value = value.get("metrics", value)
    return {str(k): float(v) for k, v in value.items() if isinstance(v, (int, float))}


def normalize(value: float) -> float | None:
    if 0 <= value <= 1:
        return value
    if 0 <= value <= 100:
        return value / 100
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--epoch", type=float, required=True)
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--prefix", default="long_context_headline_v3")
    parser.add_argument(
        "--task-metric",
        action="append",
        default=[],
        metavar="TASK=METRIC_KEY",
        help="Include exactly one metric for a task. May be repeated.",
    )
    args = parser.parse_args()

    row: dict[str, float | int] = {
        f"{args.prefix}/epoch": args.epoch,
        f"{args.prefix}/train_step": args.step,
    }
    task_values: list[float] = []
    specifications = args.task_metric or [f"{task}={metric}" for task, metric in DEFAULT_TASK_METRICS.items()]
    if specifications:
        for specification in specifications:
            try:
                task, metric_key = specification.split("=", 1)
            except ValueError as exc:
                raise ValueError(f"Invalid --task-metric {specification!r}; expected TASK=METRIC_KEY") from exc
            metrics_path = args.root / task / "merged_metrics.json"
            metrics = load_metrics(metrics_path)
            if metric_key not in metrics:
                raise KeyError(f"Missing required metric {metric_key!r} in {metrics_path}")
            value = normalize(metrics[metric_key])
            if value is None:
                raise ValueError(f"Metric {metric_key!r} is outside the supported normalization range")
            row[f"{args.prefix}/{task}"] = value
            task_values.append(value)
    if task_values:
        row[f"{args.prefix}/overall"] = sum(task_values) / len(task_values)

    import wandb

    run = wandb.init(project=args.project, id=args.run_id, name=args.run_name, resume="allow")
    wandb.define_metric(f"{args.prefix}/epoch")
    wandb.define_metric(f"{args.prefix}/*", step_metric=f"{args.prefix}/epoch")
    run.log(row, commit=True)
    run.finish()
    print(json.dumps(row, sort_keys=True))


if __name__ == "__main__":
    main()
