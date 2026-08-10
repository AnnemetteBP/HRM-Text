#!/usr/bin/env python3
"""Convert DFM9 extension sources to condition/instruction/response parquet files.

1. croco_munin_da_sft: prompt/chosen from DPO preference data -> instruction/response
2. gsm_symbolic_da: question/answer from multilingual GSM Symbolic (Danish) -> instruction/response (cot)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.parquet as pq
from huggingface_hub import snapshot_download
from tqdm import tqdm

OUT_SCHEMA = pa.schema([
    ("condition", pa.string()),
    ("instruction", pa.string()),
    ("response", pa.string()),
])

REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERTED = REPO_ROOT / "data" / "converted_sources"
DOWNLOADS = REPO_ROOT / "data" / "downloads" / "datasets"

BATCH_SIZE = 4096


def as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


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


def convert_croco_munin() -> int:
    repo_id = "danish-foundation-models/croco-munin-apertus-8b-da-simpo-full-50k"
    local_dir = DOWNLOADS / "croco_munin_da_50k"
    out_dir = CONVERTED / "croco_munin_da_sft" / "data"
    out_path = out_dir / "croco_munin_da_50k.parquet"

    if not (local_dir / ".complete").exists():
        print(f"  Downloading {repo_id}...")
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            local_dir=str(local_dir),
        )
        (local_dir / ".complete").touch()

    jsonl_files = sorted(local_dir.rglob("*.jsonl"))
    parquet_files = sorted(local_dir.rglob("*.parquet"))

    def iter_rows() -> Iterable[dict[str, str]]:
        if jsonl_files:
            for jf_path in jsonl_files:
                with open(jf_path, "r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        row = json.loads(line)
                        prompt = as_text(row.get("prompt")).strip()
                        chosen = as_text(row.get("chosen")).strip()
                        if not prompt or not chosen:
                            continue
                        yield {"condition": "direct", "instruction": prompt, "response": chosen}
        elif parquet_files:
            for pf_path in parquet_files:
                pf = pq.ParquetFile(pf_path)
                cols = set(pf.schema_arrow.names)
                if "prompt" not in cols or "chosen" not in cols:
                    continue
                for batch in pf.iter_batches(columns=["prompt", "chosen"], batch_size=BATCH_SIZE):
                    prompts = batch.column("prompt").to_pylist()
                    chosens = batch.column("chosen").to_pylist()
                    for prompt, chosen in zip(prompts, chosens):
                        prompt = as_text(prompt).strip()
                        chosen = as_text(chosen).strip()
                        if not prompt or not chosen:
                            continue
                        yield {"condition": "direct", "instruction": prompt, "response": chosen}
        else:
            raise FileNotFoundError(f"No jsonl or parquet files found in {local_dir}")

    count = write_rows(iter_rows(), out_path)
    print(f"  croco_munin_da_sft: {count:,} rows -> {out_path}")
    return count


def convert_gsm_symbolic_da() -> int:
    repo_id = "danish-foundation-models/multilingual-gsm-symbolic"
    local_dir = DOWNLOADS / "multilingual_gsm_symbolic"
    out_dir = CONVERTED / "gsm_symbolic_da" / "data"
    out_path = out_dir / "gsm_symbolic_da.parquet"

    if not (local_dir / ".complete").exists():
        print(f"  Downloading {repo_id}...")
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            local_dir=str(local_dir),
        )
        (local_dir / ".complete").touch()

    parquet_files = sorted(local_dir.rglob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {local_dir}")

    def iter_rows() -> Iterable[dict[str, str]]:
        for pf_path in parquet_files:
            pf = pq.ParquetFile(pf_path)
            cols = set(pf.schema_arrow.names)
            if "language" not in cols or "question" not in cols or "answer" not in cols:
                continue
            for batch in pf.iter_batches(columns=["question", "answer", "language"], batch_size=BATCH_SIZE):
                questions = batch.column("question").to_pylist()
                answers = batch.column("answer").to_pylist()
                languages = batch.column("language").to_pylist()
                for question, answer, lang in zip(questions, answers, languages):
                    lang = as_text(lang).strip().lower()
                    if lang != "dan":
                        continue
                    question = as_text(question).strip()
                    answer = as_text(answer).strip()
                    if not question or not answer:
                        continue
                    yield {"condition": "cot", "instruction": question, "response": answer}

    count = write_rows(iter_rows(), out_path)
    print(f"  gsm_symbolic_da: {count:,} rows -> {out_path}")
    return count


def main() -> None:
    print("Converting DFM9 extension sources...\n")

    print("[1/2] croco-munin-apertus-8b-da-50k (Danish SFT from DPO preferences)...")
    count1 = convert_croco_munin()

    print("\n[2/2] multilingual-gsm-symbolic (Danish subset)...")
    count2 = convert_gsm_symbolic_da()

    print(f"\n=== Summary ===")
    print(f"  croco_munin_da_sft: {count1:,} rows")
    print(f"  gsm_symbolic_da:   {count2:,} rows")
    print(f"  TOTAL:             {count1 + count2:,} rows")


if __name__ == "__main__":
    main()
