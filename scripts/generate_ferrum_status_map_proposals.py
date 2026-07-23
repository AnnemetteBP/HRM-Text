#!/usr/bin/env python3
"""Generate top-k Ferrum status-map proposals from an exported HRM HF model."""

from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path
from typing import Iterator

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

STATUS_SECTIONS = (
    "solved",
    "transformed_strong",
    "transformed_weak",
    "failed",
    "timeout",
)
STATUS_HEADER_RE = re.compile(r"\b(solved|transformed_strong|transformed_weak|failed|timeout)\s*:")
ATOM_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]*(?:\s*\([^)]*\))?")


def open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open("r", encoding="utf-8")


def iter_rows(path: Path) -> Iterator[dict[str, str]]:
    with open_text(path) as source:
        for line in source:
            row = json.loads(line)
            if isinstance(row.get("instruction"), str):
                yield row


def normalize_atom(atom: str) -> str:
    atom = re.sub(r"\s+", " ", atom.strip())
    atom = re.sub(r"\s*([(),=])\s*", r"\1", atom)
    atom = re.sub(r"=\s*-\s*", "=-", atom)
    return atom


def parse_status_map(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {section: [] for section in STATUS_SECTIONS}
    matches = list(STATUS_HEADER_RE.finditer(text))
    for idx, match in enumerate(matches):
        section = match.group(1)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        seen = set()
        for atom_match in ATOM_RE.finditer(text[start:end]):
            atom = normalize_atom(atom_match.group(0))
            if atom and atom not in STATUS_SECTIONS and atom not in seen:
                sections[section].append(atom)
                seen.add(atom)
    return sections


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--num-proposals", type=int, default=8)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--dtype", default="bfloat16")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dtype = getattr(torch, args.dtype)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=dtype).to(args.device).eval()

    bos_id = tokenizer.convert_tokens_to_ids("[BOS]")
    sep_id = tokenizer.convert_tokens_to_ids("[SEP]")
    eos_id = tokenizer.convert_tokens_to_ids("[EOS]")
    unk_id = tokenizer.convert_tokens_to_ids("[UNK]")
    if None in (bos_id, sep_id, eos_id, unk_id):
        raise SystemExit("export tokenizer must define [BOS], [SEP], [EOS], and [UNK]")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rows_seen = rows_written = skipped_too_long = skipped_unk = 0
    max_context = int(getattr(model.config, "max_position_embeddings", 0) or 0)

    with args.output.open("w", encoding="utf-8") as out:
        for row_idx, row in enumerate(iter_rows(args.input)):
            rows_seen += 1
            prompt = [bos_id] + tokenizer.encode(row["instruction"], add_special_tokens=False) + [sep_id]
            if unk_id in prompt:
                skipped_unk += 1
                continue
            if max_context and len(prompt) + args.max_new_tokens > max_context:
                skipped_too_long += 1
                continue
            input_ids = torch.tensor([prompt], dtype=torch.long, device=args.device)
            token_type_ids = torch.ones_like(input_ids)
            with torch.inference_mode():
                generated = model.generate(
                    input_ids=input_ids,
                    token_type_ids=token_type_ids,
                    do_sample=True,
                    temperature=args.temperature,
                    top_k=args.top_k,
                    top_p=args.top_p,
                    num_return_sequences=args.num_proposals,
                    max_new_tokens=args.max_new_tokens,
                    eos_token_id=eos_id,
                    pad_token_id=tokenizer.pad_token_id or 0,
                )
            proposals = []
            seen_texts = set()
            for sequence in generated.tolist():
                completion_ids = sequence[len(prompt):]
                if eos_id in completion_ids:
                    completion_ids = completion_ids[: completion_ids.index(eos_id)]
                text = tokenizer.decode(completion_ids, skip_special_tokens=True).strip()
                if text in seen_texts:
                    continue
                seen_texts.add(text)
                proposals.append({"text": text, "status_map": parse_status_map(text)})
            out.write(
                json.dumps(
                    {
                        "schema": "ferrum.status-map-proposals.v1",
                        "row_index": row_idx,
                        "num_proposals": len(proposals),
                        "proposals": proposals,
                        "gold": row.get("response"),
                    },
                    sort_keys=True,
                )
                + "\n"
            )
            rows_written += 1
            if args.max_rows is not None and rows_seen >= args.max_rows:
                break

    print(
        json.dumps(
            {
                "rows_seen": rows_seen,
                "rows_written": rows_written,
                "skipped_too_long": skipped_too_long,
                "skipped_unk": skipped_unk,
                "output": str(args.output),
            },
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
