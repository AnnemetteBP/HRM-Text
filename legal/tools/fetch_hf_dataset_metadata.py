#!/usr/bin/env python3
"""Fetch current Hugging Face metadata for a dataset legal-basis register."""

from __future__ import annotations

import argparse
import csv
import json
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "legal" / "registers" / "dataset-legal-basis-register.csv"
OUTPUT = ROOT / "legal" / "registers" / "hf-current-metadata-register.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--input", type=Path, default=INPUT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    return parser.parse_args()


def fetch(source_id: str, timeout: float) -> dict[str, object]:
    encoded = urllib.parse.quote(source_id, safe="/")
    request = urllib.request.Request(
        f"https://huggingface.co/api/datasets/{encoded}",
        headers={"User-Agent": "DFM-Mimir-compliance-metadata/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"source_id": source_id, "fetch_status": "error", "error": str(exc)}

    card = payload.get("cardData") or {}
    licence = card.get("license") or card.get("licence") or ""
    if isinstance(licence, list):
        licence = ";".join(str(value) for value in licence)
    tag_licences = sorted(
        tag.removeprefix("license:")
        for tag in payload.get("tags", [])
        if isinstance(tag, str) and tag.startswith("license:")
    )

    def flatten(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            return ";".join(str(item) for item in value)
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=True, sort_keys=True)
        return str(value)

    return {
        "source_id": source_id,
        "fetch_status": "ok",
        "repository_sha": payload.get("sha", ""),
        "created_at": payload.get("createdAt", ""),
        "last_modified": payload.get("lastModified", ""),
        "gated": payload.get("gated", ""),
        "private": payload.get("private", ""),
        "disabled": payload.get("disabled", ""),
        "declared_licence": licence,
        "licence_tags": ";".join(tag_licences),
        "pretty_name": flatten(card.get("pretty_name")),
        "language": flatten(card.get("language")),
        "task_categories": flatten(card.get("task_categories")),
        "task_ids": flatten(card.get("task_ids")),
        "size_categories": flatten(card.get("size_categories")),
        "source_datasets": flatten(card.get("source_datasets")),
        "annotations_creators": flatten(card.get("annotations_creators")),
        "language_creators": flatten(card.get("language_creators")),
        "multilinguality": flatten(card.get("multilinguality")),
        "paperswithcode_id": flatten(card.get("paperswithcode_id")),
        "downloads": payload.get("downloads", ""),
        "likes": payload.get("likes", ""),
        "api_url": f"https://huggingface.co/api/datasets/{source_id}",
        "error": "",
    }


def main() -> None:
    args = parse_args()
    fetched_at = datetime.now(timezone.utc).isoformat()
    with args.input.open(encoding="utf-8", newline="") as handle:
        source_ids = [
            row["source_id"]
            for row in csv.DictReader(handle)
            if "/" in row["source_id"]
        ]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(lambda source_id: fetch(source_id, args.timeout), source_ids))
    for row in rows:
        row["fetched_at_utc"] = fetched_at
    fieldnames = [
        "source_id",
        "fetched_at_utc",
        "fetch_status",
        "repository_sha",
        "created_at",
        "last_modified",
        "gated",
        "private",
        "disabled",
        "declared_licence",
        "licence_tags",
        "pretty_name",
        "language",
        "task_categories",
        "task_ids",
        "size_categories",
        "source_datasets",
        "annotations_creators",
        "language_creators",
        "multilinguality",
        "paperswithcode_id",
        "downloads",
        "likes",
        "api_url",
        "error",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    failures = sum(row["fetch_status"] != "ok" for row in rows)
    print(f"Wrote {len(rows)} current HF metadata rows to {args.output}; failures={failures}")


if __name__ == "__main__":
    main()
