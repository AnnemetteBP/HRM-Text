#!/usr/bin/env python3
"""Convert DFM9 new sources to condition/instruction/response parquet files.

Handles 6 sources with non-standard schemas that the generic converter
doesn't support:

1. numinamath_1_5: problem/solution -> instruction/response (cot)
2. nemotron_terminal_corpus: conversations -> messages expansion
3. allenai_code_meta_reasoning: raw text -> continuation
4. posttrain_natural_instructions: definition+inputs/targets -> instruction/response
5. posttrain_coedit: src/tgt -> instruction/response
6. posttrain_asset: original/simplifications -> instruction/response
"""

from __future__ import annotations

import gzip
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm

OUT_SCHEMA = pa.schema([
    ("condition", pa.string()),
    ("instruction", pa.string()),
    ("response", pa.string()),
])

REPO_ROOT = Path(__file__).resolve().parents[1]
FILTERED = REPO_ROOT / "data" / "filtered_sources"
CONVERTED = REPO_ROOT / "data" / "converted_sources"

BATCH_SIZE = 4096

PII_EXCLUDE_KEYWORDS = [
    "sms", "spam", "tweet", "twitter", "amazon_review", "amazonreview",
    "amazonfood", "imdb", "yelp", "civil_comments", "civilcomments",
    "hateeval", "hatexplain", "hate_speech", "offensive", "toxicity",
    "sarcasm", "sentiment140", "jigsaw", "stereoset", "crows",
    "ethnic", "gender_bias", "equity", "dialogre", "personachat",
    "deceptive", "opinion_spam", "review_",
    "olid", "socialiqa", "agnews", "yahoo_answers",
    "glue_cola", "ethos", "hope_edi",
]


def is_pii_task(filename: str) -> bool:
    fname_lower = filename.lower()
    return any(kw in fname_lower for kw in PII_EXCLUDE_KEYWORDS)


def as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def serialize_history(messages: list[dict[str, Any]]) -> str:
    chunks = []
    for msg in messages:
        role = as_text(msg.get("role")).strip().lower() or "message"
        content = as_text(msg.get("content")).strip()
        if not content:
            continue
        label = {
            "system": "System",
            "user": "User",
            "assistant": "Assistant",
            "tool": "Tool",
        }.get(role, role.title())
        chunks.append(f"{label}:\n{content}")
    return "\n\n".join(chunks)


def rows_from_messages(messages: list[dict[str, Any]], condition: str = "direct") -> Iterable[dict[str, str]]:
    history: list[dict[str, Any]] = []
    for msg in messages:
        role = as_text(msg.get("role")).lower()
        content = as_text(msg.get("content")).strip()
        if role == "assistant" and content:
            instruction = serialize_history(history)
            if instruction:
                yield {"condition": condition, "instruction": instruction, "response": content}
        history.append(msg)


def write_rows(rows: Iterable[dict[str, str]], out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    writer: pq.ParquetWriter | None = None
    batch: dict[str, list[str]] = {"condition": [], "instruction": [], "response": []}
    count = 0
    try:
        for row in rows:
            inst = as_text(row.get("instruction")).strip()
            resp = as_text(row.get("response")).strip()
            cond = as_text(row.get("condition")).strip() or "direct"
            if not resp:
                continue
            batch["condition"].append(cond)
            batch["instruction"].append(inst)
            batch["response"].append(resp)
            count += 1
            if len(batch["response"]) >= BATCH_SIZE:
                table = pa.Table.from_pydict(batch, schema=OUT_SCHEMA)
                if writer is None:
                    writer = pq.ParquetWriter(out_path, schema=OUT_SCHEMA, compression="zstd")
                writer.write_table(table)
                batch = {"condition": [], "instruction": [], "response": []}
        if batch["response"]:
            table = pa.Table.from_pydict(batch, schema=OUT_SCHEMA)
            if writer is None:
                writer = pq.ParquetWriter(out_path, schema=OUT_SCHEMA, compression="zstd")
            writer.write_table(table)
    finally:
        if writer is not None:
            writer.close()
    return count


def convert_numinamath() -> int:
    src_dir = FILTERED / "numinamath_1_5"
    out_dir = CONVERTED / "numinamath_1_5" / "data"
    total = 0
    for parquet_file in sorted(src_dir.rglob("*.parquet")):
        out_path = out_dir / parquet_file.name
        def iter_rows():
            pf = pq.ParquetFile(parquet_file)
            for batch in pf.iter_batches(
                columns=["problem", "solution", "problem_is_valid", "solution_is_valid"],
                batch_size=BATCH_SIZE,
            ):
                problems = batch.column("problem").to_pylist()
                solutions = batch.column("solution").to_pylist()
                valid_p = batch.column("problem_is_valid").to_pylist()
                valid_s = batch.column("solution_is_valid").to_pylist()
                for problem, solution, vp, vs in zip(problems, solutions, valid_p, valid_s):
                    problem = as_text(problem).strip()
                    solution = as_text(solution).strip()
                    if not problem or not solution:
                        continue
                    if vp != "Yes" or vs != "Yes":
                        continue
                    yield {"condition": "cot", "instruction": problem, "response": solution}
        count = write_rows(iter_rows(), out_path)
        total += count
        print(f"  numinamath {parquet_file.name}: {count:,} rows")
    return total


def convert_nemotron_terminal() -> int:
    src_dir = FILTERED / "nemotron_terminal_corpus"
    out_dir = CONVERTED / "nemotron_terminal_corpus" / "data"
    total = 0
    for parquet_file in sorted(src_dir.rglob("*.parquet")):
        out_path = out_dir / parquet_file.name
        def iter_rows():
            pf = pq.ParquetFile(parquet_file)
            for batch in pf.iter_batches(columns=["conversations"], batch_size=BATCH_SIZE):
                for raw_conversations in batch.column(0).to_pylist():
                    if not isinstance(raw_conversations, list):
                        continue
                    messages = []
                    for item in raw_conversations:
                        if isinstance(item, dict):
                            messages.append({
                                "role": as_text(item.get("role")),
                                "content": as_text(item.get("content")),
                            })
                    yield from rows_from_messages(messages)
        count = write_rows(iter_rows(), out_path)
        total += count
        print(f"  nemotron_terminal {parquet_file.name}: {count:,} rows")
    return total


def convert_code_meta_reasoning() -> int:
    src_dir = FILTERED / "allenai_code_meta_reasoning" / "data"
    out_dir = CONVERTED / "allenai_code_meta_reasoning" / "data"
    total = 0
    for parquet_file in sorted(src_dir.rglob("*.parquet")):
        out_path = out_dir / parquet_file.name
        def iter_rows():
            pf = pq.ParquetFile(parquet_file)
            for batch in pf.iter_batches(columns=["text"], batch_size=BATCH_SIZE):
                for text in batch.column(0).to_pylist():
                    text = as_text(text).strip()
                    if not text:
                        continue
                    yield {"condition": "direct", "instruction": "", "response": text}
        count = write_rows(iter_rows(), out_path)
        total += count
        print(f"  code_meta_reasoning {parquet_file.name}: {count:,} rows")
    return total


def convert_natural_instructions() -> int:
    src_dir = FILTERED / "posttrain_natural_instructions" / "train"
    out_dir = CONVERTED / "posttrain_natural_instructions" / "train"
    total = 0
    skipped_pii = 0
    for jsonl_file in sorted(src_dir.glob("*.jsonl")):
        if is_pii_task(jsonl_file.name):
            skipped_pii += 1
            continue
        out_path = out_dir / (jsonl_file.stem + ".parquet")
        def iter_rows():
            with open(jsonl_file, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    definition = as_text(row.get("definition")).strip()
                    inputs = as_text(row.get("inputs")).strip()
                    targets = as_text(row.get("targets")).strip()
                    if not targets:
                        continue
                    instruction = f"{definition}\n\n{inputs}".strip() if definition else inputs
                    if not instruction:
                        continue
                    yield {"condition": "direct", "instruction": instruction, "response": targets}
        count = write_rows(iter_rows(), out_path)
        total += count
    print(f"  natural_instructions: {total:,} rows from {len(list(src_dir.glob('*.jsonl'))) - skipped_pii} files (skipped {skipped_pii} PII-sensitive files)")
    return total


def convert_coedit() -> int:
    src_dir = FILTERED / "posttrain_coedit"
    out_dir = CONVERTED / "posttrain_coedit" / "data"
    total = 0
    for jsonl_file in sorted(src_dir.rglob("*.jsonl")):
        out_path = out_dir / (jsonl_file.stem + ".parquet")
        def iter_rows():
            with open(jsonl_file, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    src = as_text(row.get("src")).strip()
                    tgt = as_text(row.get("tgt")).strip()
                    if not src or not tgt:
                        continue
                    yield {"condition": "direct", "instruction": src, "response": tgt}
        count = write_rows(iter_rows(), out_path)
        total += count
        print(f"  coedit {jsonl_file.name}: {count:,} rows")
    return total


def convert_asset() -> int:
    src_dir = FILTERED / "posttrain_asset"
    out_dir = CONVERTED / "posttrain_asset" / "data"
    total = 0
    for parquet_file in sorted(src_dir.rglob("*.parquet")):
        out_path = out_dir / parquet_file.name
        cols = set(pq.ParquetFile(parquet_file).schema_arrow.names)
        if "simplifications" not in cols and "simplification" not in cols:
            print(f"  asset {parquet_file.name}: no simplification column, skipping")
            continue
        simp_col = "simplifications" if "simplifications" in cols else "simplification"
        def iter_rows():
            pf = pq.ParquetFile(parquet_file)
            for batch in pf.iter_batches(columns=["original", simp_col], batch_size=BATCH_SIZE):
                originals = batch.column("original").to_pylist()
                simpls = batch.column(simp_col).to_pylist()
                for original, simplification in zip(originals, simpls):
                    original = as_text(original).strip()
                    if not original:
                        continue
                    if isinstance(simplification, list):
                        if not simplification:
                            continue
                        simpl_text = as_text(simplification[0]).strip()
                    else:
                        simpl_text = as_text(simplification).strip()
                    if not simpl_text:
                        continue
                    yield {
                        "condition": "direct",
                        "instruction": f"Simplify this sentence:\n\n{original}",
                        "response": simpl_text,
                    }
        count = write_rows(iter_rows(), out_path)
        total += count
        print(f"  asset {parquet_file.name}: {count:,} rows")
    return total


def main() -> None:
    print("Converting DFM9 new sources to condition/instruction/response format...\n")

    results = {}

    print("[1/6] NuminaMath 1.5...")
    results["numinamath_1_5"] = convert_numinamath()

    print("\n[2/6] Nemotron Terminal Corpus...")
    results["nemotron_terminal_corpus"] = convert_nemotron_terminal()

    print("\n[3/6] AllenAI Code Meta Reasoning...")
    results["allenai_code_meta_reasoning"] = convert_code_meta_reasoning()

    print("\n[4/6] Posttrain Natural Instructions (PII-filtered)...")
    results["posttrain_natural_instructions"] = convert_natural_instructions()

    print("\n[5/6] Posttrain CoEdIT...")
    results["posttrain_coedit"] = convert_coedit()

    print("\n[6/6] Posttrain ASSET...")
    results["posttrain_asset"] = convert_asset()

    print("\n=== Summary ===")
    total_rows = 0
    for name, count in results.items():
        print(f"  {name}: {count:,} rows")
        total_rows += count
    print(f"  TOTAL: {total_rows:,} rows")


if __name__ == "__main__":
    main()
