#!/usr/bin/env python3
"""Create a deterministic, stratified human-review sheet from profile metadata."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_BINS = ("8k_16k", "16k_32k", "32k_60k", "60k_plus")
SCORE_FIELDS = (
    "danish_readability_1_5",
    "corruption_quality_1_5",
    "document_coherence_1_5",
    "structural_quality_1_5",
    "long_context_value_1_5",
    "boilerplate_cleanliness_1_5",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiled-documents", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--per-bin", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260831)
    parser.add_argument("--bin", action="append", dest="bins", default=None)
    return parser.parse_args()


def stable_priority(row: dict[str, Any], seed: int) -> str:
    material = f"{seed}\0{row['source_id']}\0{row['document_id']}\0{row['document_sha256']}"
    return hashlib.blake2b(material.encode("utf-8"), digest_size=16).hexdigest()


def choose_rows(rows: list[dict[str, Any]], bins: list[str], per_bin: int, seed: int) -> list[dict[str, Any]]:
    if per_bin < 1:
        raise ValueError("per-bin must be positive")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        label = str(row.get("measurements", {}).get("length_bin", ""))
        if label in bins:
            grouped[label].append(row)
    selected: list[dict[str, Any]] = []
    for label in bins:
        ordered = sorted(grouped[label], key=lambda row: stable_priority(row, seed))
        selected.extend(ordered[:per_bin])
    return selected


def flatten_review_row(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata") or {}
    measurements = row.get("measurements") or {}
    output = {
        "source_id": row.get("source_id", ""),
        "document_id": row.get("document_id", ""),
        "title": metadata.get("titel", ""),
        "created": metadata.get("skabt", ""),
        "document_type": metadata.get("type", ""),
        "source_word_count": metadata.get("antal ord", ""),
        "ocr": metadata.get("dannet ved OCR", ""),
        "ocr_method": metadata.get("OCR-metode", ""),
        "source_tokens": measurements.get("source_tokens", ""),
        "length_bin": measurements.get("length_bin", ""),
        "document_sha256": row.get("document_sha256", ""),
        "reviewer": "",
        **{field: "" for field in SCORE_FIELDS},
        "privacy_rights": "",
        "decision": "",
        "segmentation_notes": "",
        "review_notes": "",
    }
    return output


def main() -> None:
    args = parse_args()
    bins = args.bins or list(DEFAULT_BINS)
    with args.profiled_documents.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    selected = choose_rows(rows, bins, args.per_bin, args.seed)
    output_rows = [flatten_review_row(row) for row in selected]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    fieldnames = list(output_rows[0]) if output_rows else list(flatten_review_row({}))
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    temporary.replace(args.output)
    counts = {label: sum(row["length_bin"] == label for row in output_rows) for label in bins}
    print(json.dumps({"output": str(args.output), "rows": len(output_rows), "by_bin": counts}, indent=2))


if __name__ == "__main__":
    main()
