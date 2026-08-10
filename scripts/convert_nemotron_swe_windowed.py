#!/usr/bin/env python3
"""Convert nemotron_swe to windowed training examples for 4096-token context.

Two source files, two strategies:

1. agentless.jsonl — Single-turn reasoning traces.
   Keep rows where prompt + response fit in 4096 tokens (flexible split).
   Output: condition/instruction/response parquet (single-turn).

2. swe.jsonl — Multi-turn agent trajectories with tools.
   Sliding window: keep as many previous turns as fit in 3500-token context
   budget (after system prompt), 512-token response limit.
   Output: messages parquet (preserves multi-turn structure for chat template).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm
from transformers import AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parents[1]
FILTERED = REPO_ROOT / "data" / "filtered_sources" / "nemotron_swe" / "data"
CONVERTED = REPO_ROOT / "data" / "converted_sources" / "nemotron_swe_windowed" / "data"

CONTEXT_BUDGET = 4096
SWE_CONTEXT_BUDGET = 3584  # leaves 512 for response
SWE_ISSUE_TOKEN_LIMIT = 1500
SWE_RESPONSE_LIMIT = 512
MIN_RESPONSE_TOKENS = 2
BATCH_SIZE = 4096

OUT_SCHEMA_SIMPLE = pa.schema([
    ("condition", pa.string()),
    ("instruction", pa.string()),
    ("response", pa.string()),
])


def write_messages_jsonl(rows: Iterable[dict], out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def write_simple_parquet(rows: Iterable[dict], out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    writer: pq.ParquetWriter | None = None
    batch: dict[str, list] = {"condition": [], "instruction": [], "response": []}
    count = 0
    for row in rows:
        inst = (row.get("instruction") or "").strip()
        resp = (row.get("response") or "").strip()
        if not resp:
            continue
        batch["condition"].append(row.get("condition") or "direct")
        batch["instruction"].append(inst)
        batch["response"].append(resp)
        count += 1
        if len(batch["response"]) >= BATCH_SIZE:
            table = pa.Table.from_pydict(batch, schema=OUT_SCHEMA_SIMPLE)
            if writer is None:
                writer = pq.ParquetWriter(out_path, schema=OUT_SCHEMA_SIMPLE, compression="zstd")
            writer.write_table(table)
            batch = {"condition": [], "instruction": [], "response": []}
    if batch["response"]:
        table = pa.Table.from_pydict(batch, schema=OUT_SCHEMA_SIMPLE)
        if writer is None:
            writer = pq.ParquetWriter(out_path, schema=OUT_SCHEMA_SIMPLE, compression="zstd")
        writer.write_table(table)
    if writer is not None:
        writer.close()
    return count


def convert_agentless(tok: Any, src_path: Path, out_path: Path) -> int:
    print(f"  Converting agentless (flexible fit <= {CONTEXT_BUDGET} tokens)...")
    kept = 0
    total = 0

    def iter_rows():
        nonlocal kept, total
        with open(src_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                msgs = row.get("messages", [])
                if len(msgs) != 2:
                    continue
                user_msg, asst_msg = msgs[0], msgs[1]
                if user_msg.get("role") != "user" or asst_msg.get("role") != "assistant":
                    continue
                instruction = str(user_msg.get("content", "")).strip()
                response = str(asst_msg.get("content", "")).strip()
                if not instruction or not response:
                    continue
                total += 1
                inst_toks = len(tok.encode(instruction, add_special_tokens=False))
                resp_toks = len(tok.encode(response, add_special_tokens=False))
                if inst_toks + resp_toks > CONTEXT_BUDGET:
                    continue
                kept += 1
                yield {"condition": "direct", "instruction": instruction, "response": response}

    count = write_simple_parquet(iter_rows(), out_path)
    print(f"  agentless: {count:,} rows kept out of {total:,} ({count/max(1,total)*100:.1f}%)")
    return count


def normalize_message(msg: dict) -> dict:
    role = str(msg.get("role", "user"))
    if role == "environment":
        role = "tool"
    content = msg.get("content", "")
    if content is None:
        content = ""
    out: dict[str, Any] = {"role": role, "content": str(content)}
    tc = msg.get("tool_calls")
    if tc:
        out["tool_calls"] = tc
    tcid = msg.get("tool_call_id")
    if tcid is not None:
        out["tool_call_id"] = str(tcid)
    name = msg.get("name")
    if name:
        out["name"] = str(name)
    return out


def convert_swe_windowed(tok: Any, src_path: Path, out_path: Path) -> int:
    print(f"  Converting swe (windowed: {SWE_CONTEXT_BUDGET} ctx, {SWE_RESPONSE_LIMIT} resp)...")
    total_turns = 0
    kept_turns = 0
    total_convs = 0

    def iter_rows():
        nonlocal total_turns, kept_turns, total_convs
        with open(src_path, "r", encoding="utf-8") as fh:
            for line in tqdm(fh, desc="  swe conversations"):
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                msgs = row.get("messages", [])
                if not msgs:
                    continue
                total_convs += 1

                # Precompute token counts for all messages
                msg_toks = []
                for m in msgs:
                    content = str(m.get("content", ""))
                    msg_toks.append(len(tok.encode(content, add_special_tokens=False)))

                # Find user message (skip system prompt — too long for 4096 context)
                user_idx = None
                for j in range(len(msgs)):
                    if msgs[j].get("role") == "user":
                        user_idx = j
                        break

                if user_idx is None:
                    continue

                # Truncate user issue to SWE_ISSUE_TOKEN_LIMIT tokens
                user_content = str(msgs[user_idx].get("content", ""))
                user_toks = msg_toks[user_idx]
                if user_toks > SWE_ISSUE_TOKEN_LIMIT:
                    # Truncate by encoding and decoding
                    encoded = tok.encode(user_content, add_special_tokens=False)[:SWE_ISSUE_TOKEN_LIMIT]
                    user_content = tok.decode(encoded)
                    user_toks = SWE_ISSUE_TOKEN_LIMIT

                # No system prompt, no tools — drop them to fit 4096 context
                # Iterate over all assistant messages
                asst_indices = [j for j in range(len(msgs)) if msgs[j].get("role") == "assistant"]
                total_turns += len(asst_indices)

                for j in asst_indices:
                    resp_toks = msg_toks[j]
                    if resp_toks > SWE_RESPONSE_LIMIT or resp_toks < MIN_RESPONSE_TOKENS:
                        continue

                    # Build window: user (truncated) + as many turns between user and j as fit
                    budget = SWE_CONTEXT_BUDGET - user_toks
                    if budget <= 0:
                        continue

                    # Always include user
                    window_msgs = [{"role": "user", "content": user_content}]

                    # Walk backwards from j-1 to user_idx+1, accumulating tokens
                    window_toks = 0
                    window_start = user_idx + 1
                    for k in range(j - 1, user_idx, -1):
                        window_toks += msg_toks[k]
                        if window_toks > budget:
                            window_start = k + 1
                            break
                        window_start = k

                    # Add messages from window_start to j-1
                    for k in range(window_start, j):
                        window_msgs.append(normalize_message(msgs[k]))

                    # Add the assistant message (the target)
                    window_msgs.append(normalize_message(msgs[j]))

                    kept_turns += 1
                    yield {"messages": window_msgs}

    count = write_messages_jsonl(iter_rows(), out_path)
    print(f"  swe: {count:,} turns kept out of {total_turns:,} from {total_convs:,} conversations ({count/max(1,total_turns)*100:.1f}%)")
    return count


def main():
    print("Converting nemotron_swe with windowing for 4096-token context...\n")
    tok = AutoTokenizer.from_pretrained("/work/dfm/brainsurgery/models/gemma4_31b")
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    agentless_src = FILTERED / "agentless.jsonl"
    swe_src = FILTERED / "swe.jsonl"

    print("[1/2] Agentless (flexible fit)...")
    agentless_out = CONVERTED / "agentless.parquet"
    n1 = convert_agentless(tok, agentless_src, agentless_out)

    print(f"\n[2/2] SWE (sliding window)...")
    swe_out = CONVERTED / "swe.jsonl"
    n2 = convert_swe_windowed(tok, swe_src, swe_out)

    print(f"\n=== Summary ===")
    print(f"  agentless: {n1:,} rows -> {agentless_out}")
    print(f"  swe:       {n2:,} rows -> {swe_out}")
    print(f"  TOTAL:     {n1 + n2:,} rows")


if __name__ == "__main__":
    main()
