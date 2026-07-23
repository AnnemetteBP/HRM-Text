#!/usr/bin/env python3
"""Report tokenized DFM8 source sizes by prefix/category."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokenized-root", type=Path, default=Path("data/tokenized_dfm8"))
    parser.add_argument("--md-out", type=Path, default=Path("data/show_tokenized_dfm8.md"))
    parser.add_argument("--json-out", type=Path, default=Path("data/show_tokenized_dfm8.json"))
    return parser.parse_args()


def category(name: str) -> str:
    if name.startswith("giannor_"):
        return "danish_gec_tv2r"
    if name.startswith(("dfm8-openhermes-en__", "dfm8-openhermes-da__")):
        return "openhermes_repaired"
    if name.startswith("danish-dynaword-"):
        return "danish_dynaword_transform"
    if name.startswith("common-pile-"):
        return "common_pile_transform"
    if name.startswith("transformations-"):
        return "posttrain_transform_refine"
    if name.startswith(("dolci_native_tool_use", "glaive_native_tool_use", "toolace_native_tool_use", "xlam_native_tool_use")):
        return "native_tool_use"
    if name.startswith(("allenai_rlvr", "openmathinstruct2", "dmmath", "ampsmathematica", "kaenguruen")):
        return "math"
    if name.startswith(("oliverkinch_", "synquid_", "dbc__", "lexdk__", "laerebogen")):
        return "danish_instruction"
    return "inherited_or_other"


def task_token_count(path: Path) -> int:
    tokens = path / "tokens.npy"
    if not tokens.exists():
        return 0
    arr = np.load(tokens, mmap_mode="r")
    return int(arr.shape[0])


def main() -> None:
    args = parse_args()
    rows = []
    totals: defaultdict[str, int] = defaultdict(int)
    for task in sorted(p for p in args.tokenized_root.iterdir() if p.is_dir()):
        count = task_token_count(task)
        cat = category(task.name)
        rows.append({"task": task.name, "category": cat, "tokens": count})
        totals[cat] += count
    payload = {"tokenized_root": str(args.tokenized_root), "total_tokens": sum(totals.values()), "categories": dict(sorted(totals.items())), "tasks": rows}
    args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    lines = ["# DFM8 Tokenized Mix Report", "", f"Tokenized root: `{args.tokenized_root}`", "", "## Categories", "", "| Category | Tokens |", "| --- | ---: |"]
    for cat, count in sorted(totals.items()):
        lines.append(f"| `{cat}` | {count:,} |")
    lines.extend(["", "## Tasks", "", "| Task | Category | Tokens |", "| --- | --- | ---: |"])
    for row in rows:
        lines.append(f"| `{row['task']}` | `{row['category']}` | {row['tokens']:,} |")
    args.md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"total_tokens": payload["total_tokens"], "categories": payload["categories"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
