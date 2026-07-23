#!/usr/bin/env python3
"""Lightweight DFM8 source audit before tokenization."""

from __future__ import annotations

import argparse
import gzip
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import pyarrow.parquet as pq


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path("data/dfm8_chat_sources"))
    parser.add_argument("--json-out", type=Path, default=Path("logs/dfm8_source_audit.json"))
    parser.add_argument("--md-out", type=Path, default=Path("logs/dfm8_source_audit.md"))
    parser.add_argument("--max-files", type=int, default=None)
    parser.add_argument("--max-rows-per-file", type=int, default=5000)
    return parser.parse_args()


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_parquet(path: Path, max_rows: int) -> Iterable[dict[str, Any]]:
    seen = 0
    parquet = pq.ParquetFile(path)
    for batch in parquet.iter_batches():
        for row in batch.to_pylist():
            yield row
            seen += 1
            if seen >= max_rows:
                return


def iter_rows(path: Path, max_rows: int) -> Iterable[dict[str, Any]]:
    if path.suffix == ".parquet":
        yield from iter_parquet(path, max_rows)
    elif path.suffix == ".jsonl" or path.name.endswith(".jsonl.gz"):
        for idx, row in enumerate(iter_jsonl(path)):
            if idx >= max_rows:
                break
            yield row


def supported(path: Path) -> bool:
    return path.suffix == ".parquet" or path.suffix == ".jsonl" or path.name.endswith(".jsonl.gz")


def input_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, _, filenames in os.walk(root, followlinks=True):
        directory = Path(dirpath)
        for filename in filenames:
            path = directory / filename
            if path.is_file() and supported(path):
                files.append(path)
    return sorted(files)


def audit_row(row: dict[str, Any], counters: Counter[str]) -> None:
    if isinstance(row.get("messages"), list):
        counters["messages_rows"] += 1
        messages = row["messages"]
        if any(m.get("role") == "assistant" and (m.get("tool_calls") or str(m.get("content") or "").strip()) for m in messages if isinstance(m, dict)):
            counters["has_assistant_target"] += 1
        if any(m.get("tool_calls") for m in messages if isinstance(m, dict)):
            counters["has_tool_calls"] += 1
        if any("<function" in str(m.get("content") or "") or "</function" in str(m.get("content") or "") for m in messages if isinstance(m, dict)):
            counters["xml_tool_artifact"] += 1
    elif {"condition", "instruction", "response"}.issubset(row):
        counters["hrm_rows"] += 1
        if str(row.get("response") or "").strip():
            counters["has_assistant_target"] += 1
    else:
        counters["generic_rows"] += 1
    category = row.get("dfm8_category") or row.get("openhermes_category") or row.get("source") or "unknown"
    counters[f"category::{category}"] += 1
    language = row.get("language")
    if language:
        counters[f"language::{language}"] += 1
    if "\\boxed{" in json.dumps(row, ensure_ascii=False):
        counters["contains_boxed"] += 1


def main() -> None:
    args = parse_args()
    files = input_files(args.source_root)
    if args.max_files is not None:
        files = files[: args.max_files]
    summary: dict[str, Any] = {"source_root": str(args.source_root), "files": {}, "totals": Counter()}
    totals: Counter[str] = Counter()
    for path in files:
        counters: Counter[str] = Counter()
        rows = 0
        try:
            for row in iter_rows(path, args.max_rows_per_file):
                audit_row(row, counters)
                rows += 1
        except Exception as exc:
            counters["errors"] += 1
            counters[f"error::{type(exc).__name__}"] += 1
        counters["sampled_rows"] = rows
        rel = path.relative_to(args.source_root).as_posix()
        summary["files"][rel] = dict(counters)
        totals.update(counters)
    summary["totals"] = dict(totals)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    lines = ["# DFM8 Source Audit", "", f"Source root: `{args.source_root}`", "", "## Totals", ""]
    for key, value in sorted(totals.items()):
        lines.append(f"- `{key}`: {value}")
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(files), "totals": dict(totals)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
