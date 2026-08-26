#!/usr/bin/env python3
"""Measure the exact ShareGPT boundary retained in the local Tulu v2 artifacts."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
DOWNLOADS = ROOT / "data/downloads/datasets"
OUTPUT = ROOT / "legal/registers/dfm9-sharegpt-boundary-audit.csv"

SPLIT_ROOT = DOWNLOADS / "allenai_tulu_v2_sft_mixture"
LONG_PATH = DOWNLOADS / "allenai_tulu_v2_sft_long_mixture/tulu_v2_data.jsonl"

PATTERNS = {
    "email_address": re.compile(r"(?i)(?<![\w.+-])[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}(?![\w.-])"),
    "public_ipv4": re.compile(
        r"(?<!\d)(?!(?:10|127)\.)(?!(?:169\.254|192\.168)\.)(?!(?:172\.(?:1[6-9]|2\d|3[01]))\.)"
        r"(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?!\d)"
    ),
    "private_ipv4": re.compile(
        r"(?<!\d)(?:(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}|192\.168\.(?:\d{1,3}\.)\d{1,3}|"
        r"172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3})(?!\d)"
    ),
    "openai_style_key": re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    "aws_access_key": re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])"),
    "private_key_block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "password_assignment": re.compile(r"(?i)\b(?:password|passwd|pwd)\s*[:=]\s*[^\s,'\";]{6,}"),
    "phone_like": re.compile(r"(?<!\d)(?:\+?\d[\s().-]*){8,15}(?!\d)"),
    "self_identification": re.compile(r"(?i)\b(?:my name is|i am called|contact me at|email me at|my address is)\b"),
    "source_text_task": re.compile(
        r"(?i)\b(?:summari[sz]e|translate|rewrite|proofread|paraphrase|extract|analy[sz]e)\b.{0,120}"
        r"\b(?:following|below|text|article|passage|document|email|letter|story|review|transcript)\b"
    ),
}


def base_id(row_id: str) -> str:
    match = re.fullmatch(r"sharegpt_(.+)_([0-9]+)", row_id)
    if not match:
        raise ValueError(f"Unexpected ShareGPT row id: {row_id}")
    return match.group(1)


def iter_split_rows():
    for path in sorted(SPLIT_ROOT.rglob("*.parquet")):
        parquet = pq.ParquetFile(path)
        for batch in parquet.iter_batches(columns=["dataset", "id", "messages"], batch_size=32_768):
            for row in batch.to_pylist():
                if row["dataset"] == "sharegpt":
                    yield row


def iter_long_rows():
    with LONG_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row["dataset"] == "sharegpt":
                    yield row


def measure_rows(rows, *, split: bool) -> tuple[Counter[str], set[str]]:
    counts: Counter[str] = Counter()
    ids: set[str] = set()
    message_counts: list[int] = []
    for row in rows:
        counts["rows"] += 1
        current_id = base_id(row["id"])
        ids.add(current_id)
        messages = row["messages"]
        message_counts.append(len(messages))
        counts["messages"] += len(messages)
        counts["turn_pairs"] += len(messages) // 2
        for message in messages:
            role = message["role"]
            content = message["content"] or ""
            counts[f"{role}_messages"] += 1
            counts[f"{role}_characters"] += len(content)
            if len(content) >= 500:
                counts[f"{role}_messages_ge_500_chars"] += 1
            if len(content) >= 2_000:
                counts[f"{role}_messages_ge_2000_chars"] += 1
            if "```" in content:
                counts[f"{role}_messages_with_code_fence"] += 1
    counts["unique_original_conversation_ids"] = len(ids)
    message_counts.sort()
    for percentile in (50, 95, 99):
        index = ((len(message_counts) - 1) * percentile) // 100
        counts[f"messages_per_row_p{percentile}"] = message_counts[index]
    counts["messages_per_row_max"] = message_counts[-1]
    return counts, ids


def scan_raw_patterns() -> Counter[str]:
    """Count matching ShareGPT JSONL rows without emitting their contents."""
    counts: Counter[str] = Counter()
    for name, pattern in PATTERNS.items():
        select = subprocess.Popen(
            ["rg", "-F", '"dataset": "sharegpt"', str(LONG_PATH)],
            stdout=subprocess.PIPE,
        )
        assert select.stdout is not None
        match = subprocess.run(
            ["rg", "-c", "--pcre2", "--", pattern.pattern],
            stdin=select.stdout,
            text=True,
            capture_output=True,
            check=False,
        )
        select.stdout.close()
        select.wait()
        if select.returncode not in (0, 1) or match.returncode not in (0, 1):
            raise RuntimeError(f"rg scan failed for {name}: {match.stderr.strip()}")
        counts[f"conversation_rows_matching_{name}"] = int(match.stdout.strip() or 0)
    return counts


def main() -> None:
    split_counts, split_ids = measure_rows(iter_split_rows(), split=True)
    long_counts, long_ids = measure_rows(iter_long_rows(), split=False)
    long_counts.update(scan_raw_patterns())
    split_counts["original_ids_also_in_long_artifact"] = len(split_ids & long_ids)
    split_counts["original_ids_absent_from_long_artifact"] = len(split_ids - long_ids)
    long_counts["original_ids_also_in_split_artifact"] = len(split_ids & long_ids)
    long_counts["original_ids_absent_from_split_artifact"] = len(long_ids - split_ids)

    rows = []
    for artifact, counts in (("tulu_v2_split_4096", split_counts), ("tulu_v2_long", long_counts)):
        for metric, value in sorted(counts.items()):
            rows.append({"artifact": artifact, "metric": metric, "value": value})

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["artifact", "metric", "value"])
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"Measured {len(split_ids):,} split-artifact and {len(long_ids):,} long-artifact "
        f"original conversation IDs ({len(split_ids & long_ids):,} shared)"
    )
    print(f"Wrote {len(rows):,} aggregate measurements to {OUTPUT}")


if __name__ == "__main__":
    main()
