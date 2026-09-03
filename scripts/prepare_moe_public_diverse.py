#!/usr/bin/env python3
"""Build an equal-token, ten-family public corpus for HRM-MoE training.

All downloads, caches, temporary files, and outputs are constrained to the
repository.  Upstream dataset revisions are resolved before sampling and
recorded in metadata.  The script refuses to overwrite an existing output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

import numpy as np
from datasets import load_dataset
from huggingface_hub import HfApi
from transformers import AutoTokenizer, PreTrainedTokenizerBase


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from moe_tokenizer_contract import (
    CHAT_TEMPLATE_PATH,
    CORE_SPECIAL_TOKEN_IDS,
    TOKENIZER_FAMILY,
    TOKENIZER_NAME,
    TOKENIZER_REVISION,
    configure_tokenizer,
)
from scripts.prepare_moe_real_pilot import EncodedRow, encode_pair


@dataclass(frozen=True)
class SourceSpec:
    family: str
    repo_id: str
    kind: str
    config: str | None = None
    prompt: str = ""
    split: str = "train"
    license: str = ""


SOURCES: tuple[SourceSpec, ...] = (
    SourceSpec(
        "danish",
        "danish-foundation-models/danish-dynaword",
        "raw",
        prompt="Fortsæt følgende danske tekst:",
        license="mixed open licences; retain per-row provenance",
    ),
    SourceSpec(
        "math",
        "AI-MO/NuminaMath-1.5",
        "math",
        license="Apache-2.0 dataset card; constituent provenance applies",
    ),
    SourceSpec(
        "code_swe",
        "nvidia/Nemotron-SFT-SWE-v2",
        "messages",
        split="agentless",
        license="dataset-card terms and constituent licences apply",
    ),
    SourceSpec(
        "science",
        "nvidia/Nemotron-SFT-Science-v2",
        "messages",
        config="rqa",
        license="CC-BY-SA-4.0",
    ),
    SourceSpec(
        "general_instruction_chat",
        "allenai/tulu-3-sft-mixture",
        "messages",
        license="ODC-By-1.0; constituent provenance applies",
    ),
    SourceSpec(
        "explicit_reasoning",
        "allenai/big-reasoning-traces",
        "messages",
        config="DeepSeek",
        license="dataset-card terms and constituent licences apply",
    ),
    SourceSpec(
        "long_form_instruction",
        "allenai/tulu-v2-sft-long-mixture",
        "messages",
        license="ODC-By-1.0; capped to the pilot sequence limit",
    ),
    SourceSpec(
        "grounded_knowledge",
        "common-pile/wikimedia_filtered",
        "raw",
        prompt="Continue this reference passage:",
        license="CC-BY-SA; retain per-row attribution metadata upstream",
    ),
    SourceSpec(
        "news",
        "PleIAs/US-PD-Newspapers",
        "raw",
        prompt="Continue this historical newspaper passage:",
        license="CC0-1.0 / public domain",
    ),
    SourceSpec(
        "creative_literary",
        "common-pile/project_gutenberg_filtered",
        "raw",
        prompt="Continue this literary passage:",
        license="public-domain rows selected by upstream filtering",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--tokens-per-family", type=int, default=125_000_000)
    parser.add_argument("--max-sequence-tokens", type=int, default=1025)
    parser.add_argument("--shuffle-buffer", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--tokenizer", default=TOKENIZER_NAME)
    parser.add_argument("--tokenizer-revision", default=TOKENIZER_REVISION)
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Resolve revisions and validate access/schema/tokenization, then exit.",
    )
    return parser.parse_args()


def repo_local(path: Path) -> Path:
    resolved = (REPO_ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    if not resolved.is_relative_to(REPO_ROOT.resolve()):
        raise SystemExit(f"Refusing path outside repository root: {resolved}")
    return resolved


def text_pair_from_messages(row: dict[str, Any]) -> tuple[str, str] | None:
    messages = row.get("messages")
    if not isinstance(messages, list):
        return None
    users = [m.get("content") for m in messages if isinstance(m, dict) and m.get("role") == "user"]
    assistants = [
        m.get("content")
        for m in messages
        if isinstance(m, dict) and m.get("role") == "assistant"
    ]
    prompt = next((value for value in users if isinstance(value, str) and value.strip()), None)
    response = next(
        (value for value in reversed(assistants) if isinstance(value, str) and value.strip()),
        None,
    )
    if prompt is None or response is None:
        return None
    return prompt.strip(), response.strip()


def text_pair_from_math(row: dict[str, Any]) -> tuple[str, str] | None:
    prompt = row.get("problem") or row.get("prompt") or row.get("question")
    response = row.get("solution") or row.get("ref_solution") or row.get("answer")
    if not isinstance(prompt, str) or not isinstance(response, str):
        return None
    prompt, response = prompt.strip(), response.strip()
    return (prompt, response) if prompt and response else None


def raw_text(row: dict[str, Any]) -> str | None:
    for key in ("text", "article", "content", "document", "raw_content"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def raw_pairs(text: str, prompt: str, max_chars: int = 3_200) -> Iterator[tuple[str, str]]:
    """Make bounded continuation examples without tokenizing a huge document at once."""
    start = 0
    text_len = len(text)
    while start < text_len:
        window = text[start : start + max_chars].strip()
        start += max_chars
        if len(window) < 320:
            continue
        split = max(160, min(len(window) // 4, 800))
        boundary = window.rfind(" ", 0, split)
        if boundary < 80:
            boundary = split
        prefix = window[:boundary].strip()
        response = window[boundary:].strip()
        if prefix and response:
            yield f"{prompt}\n\n{prefix}", response


def row_pairs(spec: SourceSpec, row: dict[str, Any]) -> Iterable[tuple[str, str]]:
    if spec.kind == "messages":
        pair = text_pair_from_messages(row)
        return () if pair is None else (pair,)
    if spec.kind == "math":
        pair = text_pair_from_math(row)
        return () if pair is None else (pair,)
    if spec.kind == "raw":
        text = raw_text(row)
        return () if text is None else raw_pairs(text, spec.prompt)
    raise ValueError(f"Unknown source kind: {spec.kind}")


def encode_bounded_pair(
    tokenizer: PreTrainedTokenizerBase,
    family: str,
    prompt: str,
    response: str,
    max_sequence_tokens: int,
) -> EncodedRow | None:
    encoded = encode_pair(tokenizer, family, prompt, response, max_sequence_tokens)
    if encoded is not None:
        return encoded

    # Long SWE/science conversations are common. Preserve both sides instead
    # of silently rejecting every example above the sequence limit.
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=False)
    response_ids = tokenizer.encode(response, add_special_tokens=False)
    content_budget = max_sequence_tokens - 32
    if content_budget < 32 or not prompt_ids or not response_ids:
        return None
    prompt_budget = min(len(prompt_ids), content_budget // 2)
    response_budget = min(len(response_ids), content_budget - prompt_budget)
    if response_budget < content_budget - prompt_budget:
        prompt_budget = min(len(prompt_ids), content_budget - response_budget)

    while prompt_budget >= 8 and response_budget >= 8:
        bounded_prompt = tokenizer.decode(prompt_ids[:prompt_budget], skip_special_tokens=False)
        bounded_response = tokenizer.decode(
            response_ids[:response_budget], skip_special_tokens=False
        )
        encoded = encode_pair(
            tokenizer,
            family,
            bounded_prompt,
            bounded_response,
            max_sequence_tokens,
        )
        if encoded is not None:
            return encoded
        if response_budget >= prompt_budget:
            response_budget -= 8
        else:
            prompt_budget -= 8
    return None


def resolve_sources(token: str | None) -> dict[str, dict[str, str]]:
    api = HfApi(token=token)
    resolved: dict[str, dict[str, str]] = {}
    for spec in SOURCES:
        info = api.dataset_info(spec.repo_id)
        if not info.sha:
            raise SystemExit(f"Could not resolve an immutable revision for {spec.repo_id}")
        resolved[spec.family] = {
            "repo_id": spec.repo_id,
            "config": spec.config,
            "revision": info.sha,
            "split": spec.split,
            "kind": spec.kind,
            "license_note": spec.license,
        }
        print(f"resolved {spec.family}: {spec.repo_id}@{info.sha}", flush=True)
    return resolved


def stream_source(
    spec: SourceSpec,
    resolved: dict[str, dict[str, str]],
    work_dir: Path,
    seed: int,
    buffer_size: int,
    token: str | None,
) -> Iterator[dict[str, Any]]:
    dataset = load_dataset(
        spec.repo_id,
        spec.config,
        split=spec.split,
        revision=resolved[spec.family]["revision"],
        streaming=True,
        cache_dir=str(work_dir / "hf-cache"),
        token=token,
    )
    yield from dataset.shuffle(seed=seed, buffer_size=buffer_size)


def select_family(
    spec: SourceSpec,
    resolved: dict[str, dict[str, str]],
    tokenizer: PreTrainedTokenizerBase,
    work_dir: Path,
    target_tokens: int,
    max_sequence_tokens: int,
    seed: int,
    buffer_size: int,
    token: str | None,
    seen: set[bytes],
) -> list[EncodedRow]:
    selected: list[EncodedRow] = []
    total = 0
    rejected = 0
    duplicates = 0
    for raw in stream_source(spec, resolved, work_dir, seed, buffer_size, token):
        for prompt, response in row_pairs(spec, raw):
            digest = hashlib.blake2b(
                (prompt + "\0" + response).encode("utf-8"), digest_size=16
            ).digest()
            if digest in seen:
                duplicates += 1
                continue
            encoded = encode_bounded_pair(
                tokenizer, spec.family, prompt, response, max_sequence_tokens
            )
            if encoded is None:
                rejected += 1
                continue
            seen.add(digest)
            selected.append(encoded)
            total += encoded.train_tokens
            if total >= target_tokens:
                print(
                    f"{spec.family}: {len(selected):,} rows, {total:,} tokens, "
                    f"{rejected:,} rejected, {duplicates:,} duplicates",
                    flush=True,
                )
                return selected
    raise SystemExit(
        f"{spec.family} supplied only {total:,}/{target_tokens:,} tokens "
        f"after {rejected:,} rejected and {duplicates:,} duplicate rows"
    )


def preflight_source(
    spec: SourceSpec,
    resolved: dict[str, dict[str, str]],
    tokenizer: PreTrainedTokenizerBase,
    work_dir: Path,
    max_sequence_tokens: int,
    token: str | None,
) -> None:
    """Fail on access/schema problems before any family performs a long sample."""
    inspected = 0
    for raw in stream_source(spec, resolved, work_dir, 0, 1, token):
        inspected += 1
        for prompt, response in row_pairs(spec, raw):
            if encode_bounded_pair(
                tokenizer, spec.family, prompt, response, max_sequence_tokens
            ):
                print(f"preflight passed: {spec.family}", flush=True)
                return
        if inspected >= 100:
            break
    raise SystemExit(
        f"Preflight could not encode any of the first {inspected} rows from {spec.repo_id}"
    )


def write_sampled(
    rows: list[EncodedRow],
    output: Path,
    tokenizer: PreTrainedTokenizerBase,
    tokenizer_name: str,
    tokenizer_revision: str,
    chat_template_sha256: str,
    resolved_sources: dict[str, dict[str, str]],
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
    domain_ids = np.empty(len(rows), dtype=np.uint8)
    family_names = [spec.family for spec in SOURCES]
    family_to_id = {name: index for index, name in enumerate(family_names)}
    family_counts: dict[str, dict[str, int]] = {}

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
        domain_ids[index] = family_to_id[row.domain]
        counts = family_counts.setdefault(row.domain, {"rows": 0, "train_tokens": 0})
        counts["rows"] += 1
        counts["train_tokens"] += row.train_tokens
    tokens.flush()

    tokenizer_dir = output / "tokenizer"
    tokenizer.save_pretrained(tokenizer_dir)
    rng = np.random.Generator(np.random.Philox(seed=seed))
    for epoch in range(epochs):
        epoch_dir = output / f"epoch_{epoch}"
        epoch_dir.mkdir()
        order = rng.permutation(len(rows))
        np.save(epoch_dir / "inst_start.npy", inst_start[order])
        np.save(epoch_dir / "inst_len.npy", inst_len[order])
        np.save(epoch_dir / "resp_start.npy", resp_start[order])
        np.save(epoch_dir / "resp_len.npy", resp_len[order])
        np.save(epoch_dir / "domain_id.npy", domain_ids[order])

    metadata = {
        "tokenizer_info": {
            "vocab_size": len(tokenizer),
            "name_or_path": tokenizer_name,
            "tokenizer_path": str(tokenizer_dir.relative_to(REPO_ROOT)),
            "tokenizer_path_base": "repo_root",
            "tokenizer_revision": tokenizer_revision,
            "tokenizer_family": TOKENIZER_FAMILY,
            "template_mode": "jinja_chat_template",
            "chat_template_path": str(CHAT_TEMPLATE_PATH.relative_to(REPO_ROOT)),
            "chat_template_sha256": chat_template_sha256,
            "unk": "<unk>",
            "bos": "<bos>",
            "eos": "<eos>",
            "pad": "<pad>",
            "special_token_ids": CORE_SPECIAL_TOKEN_IDS,
        },
        "vocab_size": None,
        "max_seq_len": max(len(row.instruction) + len(row.response) for row in rows),
        "total_length": sum(row.train_tokens for row in rows),
        "sources": resolved_sources,
        "domains": family_counts,
        "domain_ids": {name: index for index, name in enumerate(family_names)},
        "expected_domains": family_names,
        "sampling": "equal train-token target per family; final row may cross target",
        "seed": seed,
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Wrote {output}", flush=True)
    print(json.dumps(metadata, indent=2), flush=True)


def main() -> None:
    args = parse_args()
    if args.tokens_per_family < 1 or args.epochs < 1 or args.max_sequence_tokens < 64:
        raise SystemExit("Token targets/epochs must be positive and max sequence >= 64")
    output = repo_local(args.output)
    work_dir = repo_local(args.work_dir)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    work_dir.mkdir(parents=True, exist_ok=True)
    hf_token = os.environ.get("HF_TOKEN")
    resolved = resolve_sources(hf_token)
    tokenizer = AutoTokenizer.from_pretrained(
        args.tokenizer,
        revision=args.tokenizer_revision,
        cache_dir=str(work_dir / "hf-cache" / "tokenizer"),
        token=hf_token,
        use_fast=True,
    )
    try:
        template_sha256 = configure_tokenizer(tokenizer)
    except ValueError as exc:
        raise SystemExit(f"Tokenizer contract failed: {exc}") from exc

    for spec in SOURCES:
        preflight_source(
            spec,
            resolved,
            tokenizer,
            work_dir,
            args.max_sequence_tokens,
            hf_token,
        )
    if args.preflight_only:
        print(f"All {len(SOURCES)} public source families passed preflight.", flush=True)
        return

    rows: list[EncodedRow] = []
    seen: set[bytes] = set()
    for offset, spec in enumerate(SOURCES):
        rows.extend(
            select_family(
                spec,
                resolved,
                tokenizer,
                work_dir,
                args.tokens_per_family,
                args.max_sequence_tokens,
                args.seed + offset,
                args.shuffle_buffer,
                hf_token,
                seen,
            )
        )
    rng = np.random.Generator(np.random.Philox(seed=args.seed))
    rng.shuffle(rows)
    write_sampled(
        rows,
        output,
        tokenizer,
        args.tokenizer,
        args.tokenizer_revision,
        template_sha256,
        resolved,
        args.epochs,
        args.seed,
    )


if __name__ == "__main__":
    main()
