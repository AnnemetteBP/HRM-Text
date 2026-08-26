#!/usr/bin/env python3
"""Validate and summarize the prompt-level RLVE expression audit register."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTER = ROOT / "legal/registers/dfm9-rlve-prompt-expression-audit.csv"
EXPECTED_BINS = {
    "native_generator_no_source_comment",
    "functional_abstraction_or_rewrite",
    "close_but_constrained_restatement",
    "expressive_or_source_specific_carryover",
    "cited_source_unavailable",
    "unmatched_dataset_variant",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", type=Path, default=DEFAULT_REGISTER)
    args = parser.parse_args()

    with args.register.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    variants = [row["variant"] for row in rows]
    if len(rows) != 250 or len(set(variants)) != 250:
        raise SystemExit(
            f"expected 250 unique variants, found {len(rows)} rows and "
            f"{len(set(variants))} unique variants"
        )

    unknown = sorted({row["comparison_bin"] for row in rows} - EXPECTED_BINS)
    if unknown:
        raise SystemExit(f"unknown comparison bins: {unknown}")

    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0, 0])
    for row in rows:
        values = totals[row["comparison_bin"]]
        values[0] += 1
        values[1] += int(row["gpt41_rows"])
        values[2] += int(row["gpt41_tokens"])
        values[3] += int(row["o4mini_rows"])
        values[4] += int(row["o4mini_tokens"])

    print("bin,variants,gpt41_rows,gpt41_tokens,o4mini_rows,o4mini_tokens")
    for name in sorted(totals):
        print(name + "," + ",".join(map(str, totals[name])))


if __name__ == "__main__":
    main()
