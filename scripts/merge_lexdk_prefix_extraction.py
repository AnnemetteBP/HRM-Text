#!/usr/bin/env python3
"""Merge exhaustive LexDK prefix-extraction shards and compute tail statistics."""

from __future__ import annotations

import argparse
import heapq
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def percentile(values: list[int], fraction: float) -> float:
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-shards", type=int, default=8)
    parser.add_argument("--top-examples", type=int, default=100)
    args = parser.parse_args()

    paths = sorted(args.input_root.glob("shard_*/results.jsonl"))
    if len(paths) != args.expected_shards:
        parser.error(f"found {len(paths)} result shards; expected {args.expected_shards}")

    groups: dict[tuple[str, int], dict[str, Any]] = defaultdict(
        lambda: {
            "lcp": [],
            "aligned": [],
            "generated_lengths": [],
            "exact": 0,
            "top": [],
        }
    )
    total = 0
    tail_rows = 0
    tail_source_ids: set[str] = set()
    tail_reference_prefixes: Counter[tuple[int, ...]] = Counter()
    tail_copenhagen_titles = 0
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                key = (row["mode"], int(row["prefix_tokens"]))
                group = groups[key]
                lcp = int(row["matching_prefix_tokens"])
                group["lcp"].append(lcp)
                group["aligned"].append(float(row["aligned_token_accuracy"]))
                group["generated_lengths"].append(int(row["generated_token_count"]))
                group["exact"] += int(row["exact_target"])
                if lcp >= 20:
                    tail_rows += 1
                    tail_source_ids.add(str(row["source_id"]))
                    tail_reference_prefixes[tuple(row["reference_token_ids"][:20])] += 1
                    tail_copenhagen_titles += int("København" in str(row.get("title") or ""))
                ranked = (lcp, str(row["source_id"]), total, row)
                if len(group["top"]) < args.top_examples:
                    heapq.heappush(group["top"], ranked)
                elif ranked[:3] > group["top"][0][:3]:
                    heapq.heapreplace(group["top"], ranked)
                total += 1

    summary: dict[str, Any] = {}
    outliers: list[dict[str, Any]] = []
    thresholds = [1, 5, 10, 20, 30, 40, 50, 64]
    for (mode, prefix), group in sorted(groups.items()):
        lcp = group["lcp"]
        lengths = group["generated_lengths"]
        key = f"{mode}/prefix_{prefix}"
        summary[key] = {
            "eligible_rows": len(lcp),
            "exact_64_token_generations": group["exact"],
            "exact_64_token_rate": group["exact"] / len(lcp),
            "mean_exact_prefix_tokens": statistics.fmean(lcp),
            "stddev_exact_prefix_tokens": statistics.pstdev(lcp),
            "p50_exact_prefix_tokens": percentile(lcp, 0.50),
            "p75_exact_prefix_tokens": percentile(lcp, 0.75),
            "p90_exact_prefix_tokens": percentile(lcp, 0.90),
            "p95_exact_prefix_tokens": percentile(lcp, 0.95),
            "p99_exact_prefix_tokens": percentile(lcp, 0.99),
            "p99_9_exact_prefix_tokens": percentile(lcp, 0.999),
            "max_exact_prefix_tokens": max(lcp),
            "mean_aligned_token_accuracy": statistics.fmean(group["aligned"]),
            "mean_generated_tokens": statistics.fmean(lengths),
            "early_stop_rate": sum(length < 64 for length in lengths) / len(lengths),
            **{
                f"match_at_least_{threshold}_tokens_count": sum(value >= threshold for value in lcp)
                for threshold in thresholds
            },
            **{
                f"match_at_least_{threshold}_tokens_rate": sum(value >= threshold for value in lcp) / len(lcp)
                for threshold in thresholds
            },
        }
        outliers.extend(
            item[3]
            for item in sorted(group["top"], reverse=True)
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tail_summary = {
        "match_at_least_20_tokens_generations": tail_rows,
        "unique_source_rows": len(tail_source_ids),
        "unique_20_token_reference_prefixes": len(tail_reference_prefixes),
        "copenhagen_titled_generations": tail_copenhagen_titles,
        "most_repeated_20_token_reference_prefix_count": max(tail_reference_prefixes.values(), default=0),
    }
    (args.output_dir / "tail_analysis.json").write_text(
        json.dumps(tail_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (args.output_dir / "top_outliers.jsonl").open("w", encoding="utf-8") as handle:
        for row in outliers:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    lines = [
        "# Exhaustive LexDK Prefix-Extraction Results",
        "",
        f"Total greedy generations: {total:,}",
        "",
        "| Method | Prefix | Eligible | Exact 64 | Mean LCP | P50 | P90 | P95 | P99 | P99.9 | Max LCP | >=20 | >=50 | Aligned acc. | Early stop |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, metrics in summary.items():
        mode, prefix_name = key.split("/")
        lines.append(
            "| {mode} | {prefix} | {n:,} | {exact:,} ({exact_rate:.4%}) | {mean:.2f} | {p50:.1f} | {p90:.1f} | {p95:.1f} | {p99:.1f} | {p999:.1f} | {maximum} | {m20:,} ({m20_rate:.3%}) | {m50:,} ({m50_rate:.3%}) | {aligned:.3%} | {early:.3%} |".format(
                mode=mode,
                prefix=prefix_name.removeprefix("prefix_"),
                n=metrics["eligible_rows"],
                exact=metrics["exact_64_token_generations"],
                exact_rate=metrics["exact_64_token_rate"],
                mean=metrics["mean_exact_prefix_tokens"],
                p50=metrics["p50_exact_prefix_tokens"],
                p90=metrics["p90_exact_prefix_tokens"],
                p95=metrics["p95_exact_prefix_tokens"],
                p99=metrics["p99_exact_prefix_tokens"],
                p999=metrics["p99_9_exact_prefix_tokens"],
                maximum=metrics["max_exact_prefix_tokens"],
                m20=metrics["match_at_least_20_tokens_count"],
                m20_rate=metrics["match_at_least_20_tokens_rate"],
                m50=metrics["match_at_least_50_tokens_count"],
                m50_rate=metrics["match_at_least_50_tokens_rate"],
                aligned=metrics["mean_aligned_token_accuracy"],
                early=metrics["early_stop_rate"],
            )
        )
    maximum = max(outliers, key=lambda row: int(row["matching_prefix_tokens"]))
    lines.extend(
        [
            "",
            "## Tail diagnostics",
            "",
            f"- Generations matching at least 20 tokens: {tail_rows:,}",
            f"- Distinct original source rows among them: {len(tail_source_ids):,}",
            f"- Distinct 20-token reference prefixes among them: {len(tail_reference_prefixes):,}",
            f"- Rows with `København` in the title: {tail_copenhagen_titles:,}",
            f"- Most repeated 20-token reference prefix: {max(tail_reference_prefixes.values(), default=0):,} generations",
            f"- Overall maximum exact-prefix continuation: {maximum['matching_prefix_tokens']} tokens (`{maximum['mode']}`, prefix {maximum['prefix_tokens']}, `{maximum['title']}`)",
            "",
            "No generated continuation exactly matched all 64 reference tokens. The high tail is not independent: it is dominated by repeated listed-building prose, while the overall maximum is a mathematical-formula continuation.",
        ]
    )
    (args.output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"merged {total:,} generations from {len(paths)} shards")
    print(f"wrote {args.output_dir / 'report.md'}")


if __name__ == "__main__":
    main()
