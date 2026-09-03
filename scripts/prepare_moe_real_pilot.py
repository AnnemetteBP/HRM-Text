#!/usr/bin/env python3
"""Build a capped real-data Danish/math/code corpus for HRM-MoE training."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import numpy as np
from datasets import load_dataset
from transformers import AutoTokenizer, PreTrainedTokenizerBase


SOURCES = {
    "danish": "oliverkinch/da-instruct-dynaword-hq",
    "math": "AI-MO/NuminaMath-1.5",
    "code": "allenai/tulu-3-sft-personas-code",
}


@dataclass(frozen=True)
class EncodedRow:
    domain: str
    instruction: list[int]
    response: list[int]

    @property
    def train_tokens(self) -> int:
        return len(self.instruction) + len(self.response) - 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/moe_pilot/real_balanced"))
    parser.add_argument("--work-dir", type=Path, default=Path("data/moe_pilot/work"))
    parser.add_argument("--tokenizer", default="danish-foundation-models/DFM-Mimir")
    parser.add_argument("--tokens-per-domain", type=int, default=500_000)
    parser.add_argument("--max-sequence-tokens", type=int, default=1025)
    parser.add_argument("--shuffle-buffer", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=1)
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repo_local(path: Path) -> Path:
    root = repo_root().resolve()
    resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
    if not resolved.is_relative_to(root):
        raise SystemExit(f"Refusing path outside repository root: {resolved}")
    return resolved


def row_pair(domain: str, row: dict[str, Any]) -> tuple[str, str] | None:
    if domain == "danish":
        prompt, response = row.get("prompt"), row.get("target")
    elif domain == "math":
        prompt, response = row.get("problem"), row.get("solution") or row.get("ref_solution")
    elif domain == "code":
        messages = row.get("messages")
        if not isinstance(messages, list):
            return None
        users = [message.get("content") for message in messages if message.get("role") == "user"]
        assistants = [message.get("content") for message in messages if message.get("role") == "assistant"]
        if not users or not assistants:
            return None
        prompt, response = users[0], assistants[-1]
    else:
        raise ValueError(f"Unknown domain: {domain}")

    if not isinstance(prompt, str) or not isinstance(response, str):
        return None
    prompt, response = prompt.strip(), response.strip()
    return (prompt, response) if prompt and response else None


def encode_pair(
    tokenizer: PreTrainedTokenizerBase,
    domain: str,
    prompt: str,
    response: str,
    max_sequence_tokens: int,
) -> EncodedRow | None:
    user = [{"role": "user", "content": prompt}]
    conversation = user + [{"role": "assistant", "content": response}]
    instruction = list(tokenizer.apply_chat_template(user, tokenize=True, add_generation_prompt=True))
    full = list(tokenizer.apply_chat_template(conversation, tokenize=True, add_generation_prompt=False))
    if not instruction or full[: len(instruction)] != instruction:
        return None
    response_tokens = full[len(instruction) :]
    if len(response_tokens) < 2 or len(instruction) + len(response_tokens) > max_sequence_tokens:
        return None
    return EncodedRow(domain, instruction, response_tokens)


def stream_rows(domain: str, work_dir: Path, seed: int, buffer_size: int) -> Iterator[dict[str, Any]]:
    dataset = load_dataset(
        SOURCES[domain],
        split="train",
        streaming=True,
        cache_dir=str(work_dir / "hf-cache"),
        token=os.environ.get("HF_TOKEN"),
    )
    yield from dataset.shuffle(seed=seed, buffer_size=buffer_size)


def select_domain(
    domain: str,
    tokenizer: PreTrainedTokenizerBase,
    work_dir: Path,
    target_tokens: int,
    max_sequence_tokens: int,
    seed: int,
    buffer_size: int,
) -> list[EncodedRow]:
    selected: list[EncodedRow] = []
    total = 0
    rejected = 0
    for raw in stream_rows(domain, work_dir, seed, buffer_size):
        pair = row_pair(domain, raw)
        encoded = None if pair is None else encode_pair(
            tokenizer, domain, pair[0], pair[1], max_sequence_tokens
        )
        if encoded is None:
            rejected += 1
            continue
        selected.append(encoded)
        total += encoded.train_tokens
        if total >= target_tokens:
            break
    if total < target_tokens:
        raise SystemExit(
            f"{domain} supplied only {total:,}/{target_tokens:,} requested tokens "
            f"after rejecting {rejected:,} rows"
        )
    print(f"{domain}: {len(selected):,} rows, {total:,} tokens, {rejected:,} rejected", flush=True)
    return selected


def write_sampled(
    rows: list[EncodedRow],
    output: Path,
    tokenizer: PreTrainedTokenizerBase,
    epochs: int,
    seed: int,
) -> None:
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    output.mkdir(parents=True)
    stored_tokens = sum(len(row.instruction) + len(row.response) for row in rows)
    tokens = np.lib.format.open_memmap(
        output / "tokens.npy", mode="w+", dtype=np.uint32, shape=(stored_tokens,)
    )
    inst_start = np.empty(len(rows), dtype=np.uint64)
    inst_len = np.empty(len(rows), dtype=np.uint32)
    resp_start = np.empty(len(rows), dtype=np.uint64)
    resp_len = np.empty(len(rows), dtype=np.uint32)
    domain_counts: dict[str, dict[str, int]] = {}

    cursor = 0
    for index, row in enumerate(rows):
        inst_start[index] = cursor
        inst_len[index] = len(row.instruction)
        tokens[cursor : cursor + len(row.instruction)] = row.instruction
        cursor += len(row.instruction)
        resp_start[index] = cursor
        resp_len[index] = len(row.response)
        tokens[cursor : cursor + len(row.response)] = row.response
        cursor += len(row.response)
        counts = domain_counts.setdefault(row.domain, {"rows": 0, "train_tokens": 0})
        counts["rows"] += 1
        counts["train_tokens"] += row.train_tokens
    tokens.flush()

    rng = np.random.Generator(np.random.Philox(seed=seed))
    for epoch in range(epochs):
        epoch_dir = output / f"epoch_{epoch}"
        epoch_dir.mkdir()
        order = rng.permutation(len(rows))
        np.save(epoch_dir / "inst_start.npy", inst_start[order])
        np.save(epoch_dir / "inst_len.npy", inst_len[order])
        np.save(epoch_dir / "resp_start.npy", resp_start[order])
        np.save(epoch_dir / "resp_len.npy", resp_len[order])

    metadata = {
        "tokenizer_info": {"vocab_size": len(tokenizer), "name_or_path": tokenizer.name_or_path},
        "vocab_size": None,
        "max_seq_len": max(len(row.instruction) + len(row.response) for row in rows),
        "total_length": sum(row.train_tokens for row in rows),
        "sources": SOURCES,
        "domains": domain_counts,
        "seed": seed,
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Wrote {output}", flush=True)
    print(json.dumps(metadata, indent=2), flush=True)


def main() -> None:
    args = parse_args()
    if args.tokens_per_domain < 1 or args.epochs < 1 or args.max_sequence_tokens < 3:
        raise SystemExit("Token targets and epochs must be positive; sequence length must be at least 3")
    output = repo_local(args.output)
    work_dir = repo_local(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(
        args.tokenizer,
        cache_dir=str(work_dir / "hf-cache" / "tokenizer"),
        token=os.environ.get("HF_TOKEN"),
        use_fast=True,
    )
    if tokenizer.chat_template is None:
        raise SystemExit(f"Tokenizer {args.tokenizer} has no chat template")

    rows: list[EncodedRow] = []
    for offset, domain in enumerate(("danish", "math", "code")):
        rows.extend(
            select_domain(
                domain,
                tokenizer,
                work_dir,
                args.tokens_per_domain,
                args.max_sequence_tokens,
                args.seed + offset,
                args.shuffle_buffer,
            )
        )
    rng = np.random.Generator(np.random.Philox(seed=args.seed))
    rng.shuffle(rows)
    write_sampled(rows, output, tokenizer, args.epochs, args.seed)


if __name__ == "__main__":
    main()
