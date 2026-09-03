#!/usr/bin/env python3
"""Render local HRM-MoE JSONL metrics as a dependency-free SVG figure."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape


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


def fmt(value: float) -> str:
    if value == 0:
        return "0"
    if abs(value) >= 1000 or abs(value) < 0.001:
        return f"{value:.1e}"
    return f"{value:.3g}"


def panel_svg(
    title: str,
    values: dict[str, list[tuple[float, float]]],
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    fixed_y: tuple[float, float] | None = None,
) -> str:
    left, right, top, bottom = 72.0, 20.0, 46.0, 48.0
    px, py = x + left, y + top
    pw, ph = width - left - right, height - top - bottom
    points = [point for item in values.values() for point in item]
    if not points:
        return f'<text x="{x + 20}" y="{y + 30}" font-size="18">{escape(title)}: no data</text>'
    x_min, x_max = min(p[0] for p in points), max(p[0] for p in points)
    if x_min == x_max:
        x_max = x_min + 1.0
    if fixed_y is None:
        y_min, y_max = min(p[1] for p in points), max(p[1] for p in points)
        pad = max((y_max - y_min) * 0.08, abs(y_max) * 0.01, 1e-9)
        y_min, y_max = y_min - pad, y_max + pad
    else:
        y_min, y_max = fixed_y

    def sx(value: float) -> float:
        return px + (value - x_min) / (x_max - x_min) * pw

    def sy(value: float) -> float:
        return py + ph - (value - y_min) / (y_max - y_min) * ph

    out = [
        f'<g><rect x="{x}" y="{y}" width="{width}" height="{height}" fill="#ffffff" stroke="#d0d0d0"/>',
        f'<text x="{x + 16}" y="{y + 28}" font-size="18" font-weight="600">{escape(title)}</text>',
        f'<line x1="{px}" y1="{py}" x2="{px}" y2="{py + ph}" stroke="#333"/>',
        f'<line x1="{px}" y1="{py + ph}" x2="{px + pw}" y2="{py + ph}" stroke="#333"/>',
    ]
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        gy = py + ph * (1.0 - fraction)
        value = y_min + fraction * (y_max - y_min)
        out.append(f'<line x1="{px}" y1="{gy}" x2="{px + pw}" y2="{gy}" stroke="#ececec"/>')
        out.append(f'<text x="{px - 8}" y="{gy + 4}" text-anchor="end" font-size="12">{fmt(value)}</text>')
    for fraction in (0.0, 0.5, 1.0):
        gx = px + pw * fraction
        value = x_min + fraction * (x_max - x_min)
        out.append(f'<text x="{gx}" y="{py + ph + 22}" text-anchor="middle" font-size="12">{value:.0f}</text>')
    out.append(f'<text x="{px + pw / 2}" y="{y + height - 8}" text-anchor="middle" font-size="13">optimizer step</text>')

    legend_x = px + 8
    for index, (key, item) in enumerate(values.items()):
        color = COLORS[index % len(COLORS)]
        path = " ".join(
            ("M" if point_index == 0 else "L") + f" {sx(step):.2f} {sy(value):.2f}"
            for point_index, (step, value) in enumerate(item)
        )
        out.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2"/>')
        label = key.removeprefix("train/").removeprefix("moe/")
        ly = py + 16 + index * 17
        out.append(f'<line x1="{legend_x}" y1="{ly - 4}" x2="{legend_x + 20}" y2="{ly - 4}" stroke="{color}" stroke-width="3"/>')
        out.append(f'<text x="{legend_x + 26}" y="{ly}" font-size="12">{escape(label)}</text>')
    out.append("</g>")
    return "".join(out)


def render(records: list[dict[str, float]], title: str) -> str:
    load_keys = [f"train/moe/expert_{index}/load" for index in range(4)]
    probability_keys = [f"train/moe/expert_{index}/mean_probability" for index in range(4)]
    panels = (
        ("Language-model training", ["train/loss", "train/objective"], None),
        ("Router auxiliary losses", ["train/moe/balance_loss", "train/moe/z_loss", "train/moe/aux_loss"], None),
        ("Top-1 expert load", load_keys, (0.0, 1.0)),
        ("Mean router probability", probability_keys, (0.0, 1.0)),
    )
    width, height = 1280, 940
    chunks = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f7f7f7"/>',
        f'<text x="30" y="38" font-size="24" font-weight="700">{escape(title)}</text>',
    ]
    for index, (panel_title, keys, fixed_y) in enumerate(panels):
        chunks.append(
            panel_svg(
                panel_title,
                series(records, keys),
                x=25 + (index % 2) * 627,
                y=60 + (index // 2) * 430,
                width=602,
                height=405,
                fixed_y=fixed_y,
            )
        )
    chunks.append("</svg>\n")
    return "".join(chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    metrics_path = args.run_root / "results" / "metrics.jsonl"
    output = args.output or args.run_root / "results" / "training-progress.svg"
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing figure: {output}")
    records = load_metrics(metrics_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(records, args.run_root.name), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
