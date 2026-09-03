#!/usr/bin/env python3
"""Render local HRM-MoE JSONL metrics as a PNG figure."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


COLORS = ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9")


def load_metrics(path: Path) -> list[dict[str, float]]:
    records: list[dict[str, float]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
            if record.get("event") != "metrics":
                continue
            numeric = {
                key: float(value)
                for key, value in record.items()
                if key != "event" and isinstance(value, (int, float)) and math.isfinite(value)
            }
            if "step" in numeric:
                records.append(numeric)
    if not records:
        raise ValueError(f"No metric records found in {path}")
    return records


def series(records: list[dict[str, float]], keys: list[str]) -> dict[str, list[tuple[float, float]]]:
    return {
        key: [(record["step"], record[key]) for record in records if key in record]
        for key in keys
        if any(key in record for record in records)
    }


def render(records: list[dict[str, float]], title: str, output: Path) -> None:
    available_keys = {key for record in records for key in record}

    def expert_keys(metric: str) -> list[str]:
        matched: list[tuple[int, str]] = []
        pattern = re.compile(rf"train/moe/expert_(\d+)/{re.escape(metric)}")
        for key in available_keys:
            match = pattern.fullmatch(key)
            if match is not None:
                matched.append((int(match.group(1)), key))
        return [key for _, key in sorted(matched)]

    load_keys = expert_keys("load")
    probability_keys = expert_keys("mean_probability")
    panels = (
        ("Language-model training", ["train/loss", "train/objective"], None),
        ("Router auxiliary losses", ["train/moe/balance_loss", "train/moe/z_loss", "train/moe/aux_loss"], None),
        ("Top-1 expert load", load_keys, (0.0, 1.0)),
        ("Mean router probability", probability_keys, (0.0, 1.0)),
    )

    figure, axes = plt.subplots(2, 2, figsize=(12.8, 9.4), dpi=150)
    figure.suptitle(title, fontsize=16, fontweight="bold")
    for axis, (panel_title, keys, y_limits) in zip(axes.flat, panels, strict=True):
        values = series(records, keys)
        for index, (key, points) in enumerate(values.items()):
            axis.plot(
                [step for step, _ in points],
                [value for _, value in points],
                color=COLORS[index % len(COLORS)],
                linewidth=1.5,
                label=key.removeprefix("train/").removeprefix("moe/"),
            )
        axis.set_title(panel_title)
        axis.set_xlabel("optimizer step")
        axis.grid(alpha=0.25)
        if y_limits is not None:
            axis.set_ylim(*y_limits)
        if values:
            axis.legend(fontsize=8)

    figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    figure.savefig(output, format="png", dpi=150)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    metrics_path = args.run_root / "results" / "metrics.jsonl"
    output = args.output or args.run_root / "results" / "training-progress.png"
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing figure: {output}")
    if output.suffix.lower() != ".png":
        raise SystemExit(f"Output must use the .png extension: {output}")
    records = load_metrics(metrics_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    render(records, args.run_root.name, output)
    print(output)


if __name__ == "__main__":
    main()
