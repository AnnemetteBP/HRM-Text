#!/usr/bin/env python3
"""Measure verbatim continuation extraction from original LexDK article prefixes."""

from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import jinja2
from transformers import AutoTokenizer

# Greedy decoding does not need FlashInfer's optional JIT sampler. The native
# sampler also avoids requiring CUDA development headers at vLLM startup.
os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")

from vllm import LLM, SamplingParams
from vllm.inputs import TokensPrompt


@dataclass(frozen=True)
class SourceRow:
    row_id: str
    title: str
    url: str
    text: str


def parse_int_list(value: str) -> list[int]:
    values = sorted({int(item.strip()) for item in value.split(",") if item.strip()})
    if not values or any(item <= 0 for item in values):
        raise argparse.ArgumentTypeError("expected a comma-separated list of positive integers")
    return values


def iter_source_rows(path: Path) -> Iterable[SourceRow]:
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            text = str(row.get("text") or "").strip()
            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            if not text:
                continue
            yield SourceRow(
                row_id=str(row.get("id") or ""),
                title=str(metadata.get("title") or ""),
                url=str(metadata.get("url") or ""),
                text=text,
            )


def sample_by_prefix(
    rows: Iterable[SourceRow],
    tokenizer: Any,
    prefix_lengths: list[int],
    target_tokens: int,
    count: int | None,
    seed: int,
) -> dict[int, list[tuple[SourceRow, list[int]]]]:
    """Build independent reservoirs while tokenizing each source article once."""
    samples: dict[int, list[tuple[SourceRow, list[int]]]] = {length: [] for length in prefix_lengths}
    seen = {length: 0 for length in prefix_lengths}
    rngs = {length: random.Random(seed + length) for length in prefix_lengths}
    for row in rows:
        token_ids = tokenizer(row.text, add_special_tokens=False, return_attention_mask=False)["input_ids"]
        for prefix_length in prefix_lengths:
            if len(token_ids) < prefix_length + target_tokens:
                continue
            seen[prefix_length] += 1
            candidate = (row, token_ids)
            if count is None or len(samples[prefix_length]) < count:
                samples[prefix_length].append(candidate)
                continue
            replacement = rngs[prefix_length].randrange(seen[prefix_length])
            if replacement < count:
                samples[prefix_length][replacement] = candidate
    return samples


def render_generation_prompt(template: jinja2.Template, tokenizer: Any) -> list[int]:
    text = template.render(
        messages=[
            {
                "role": "user",
                "content": (
                    "Fortsæt den følgende danske tekst ordret. Skriv kun fortsættelsen, "
                    "uden forklaring eller gentagelse."
                ),
            }
        ],
        tools=None,
        add_generation_prompt=True,
        enable_thinking=False,
        bos_token=tokenizer.bos_token or "",
        eos_token=tokenizer.eos_token or "",
    )
    return tokenizer(text, add_special_tokens=False, return_attention_mask=False)["input_ids"]


def longest_common_prefix(left: list[int], right: list[int]) -> int:
    length = 0
    for expected, actual in zip(left, right):
        if expected != actual:
            break
        length += 1
    return length


def percentile(values: list[int], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def summarize(rows: list[dict[str, Any]], target_tokens: int) -> dict[str, Any]:
    groups: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["mode"], row["prefix_tokens"])].append(row)

    summary: dict[str, Any] = {}
    thresholds = sorted({1, 5, 10, 20, 50, target_tokens})
    for (mode, prefix_tokens), group in sorted(groups.items()):
        lcps = [int(row["matching_prefix_tokens"]) for row in group]
        aligned = [float(row["aligned_token_accuracy"]) for row in group]
        key = f"{mode}/prefix_{prefix_tokens}"
        summary[key] = {
            "examples": len(group),
            "exact_target_rate": sum(row["exact_target"] for row in group) / len(group),
            "mean_matching_prefix_tokens": statistics.fmean(lcps),
            "median_matching_prefix_tokens": statistics.median(lcps),
            "p95_matching_prefix_tokens": percentile(lcps, 0.95),
            "max_matching_prefix_tokens": max(lcps),
            "mean_aligned_token_accuracy": statistics.fmean(aligned),
            **{
                f"match_at_least_{threshold}_tokens_rate": sum(value >= threshold for value in lcps) / len(lcps)
                for threshold in thresholds
                if threshold <= target_tokens
            },
        }
    return summary


def write_markdown(path: Path, args: argparse.Namespace, summary: dict[str, Any]) -> None:
    sample_description = "all eligible rows" if args.samples == 0 else str(args.samples)
    lines = [
        "# LexDK Prefix-Extraction Probe",
        "",
        f"- Model: `{args.model}`",
        f"- Original source archive: `{args.source}`",
        f"- Samples per prefix length: {sample_description}",
        f"- Prefix lengths: {', '.join(map(str, args.prefix_tokens))} source tokens",
        f"- Reference/generated span: {args.target_tokens} tokens",
        f"- Seed: {args.seed}",
        "- Decoding: greedy (`temperature=0`)",
        "",
        "The probe reads prefixes and continuations directly from the original JSONL archive. It does not read the converted LexDK parquet or reuse its generated title/source instruction.",
        "",
        "`raw` is classic bare causal continuation (`<bos>` plus source prefix). `assistant_prefill` places the same original source prefix after a neutral Gemma-chat continuation request.",
        "",
        f"| Mode | Prefix | N | Exact {args.target_tokens}-token target | >=10 matching | >=20 matching | >=50 matching | Mean LCP | P95 LCP | Max LCP | Aligned accuracy |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, metrics in summary.items():
        mode, prefix_name = key.split("/")
        prefix = prefix_name.removeprefix("prefix_")
        lines.append(
            "| {mode} | {prefix} | {examples} | {exact:.3%} | {m10:.3%} | {m20:.3%} | {m50:.3%} | {mean:.2f} | {p95:.1f} | {maximum} | {aligned:.3%} |".format(
                mode=mode,
                prefix=prefix,
                examples=metrics["examples"],
                exact=metrics["exact_target_rate"],
                m10=metrics.get("match_at_least_10_tokens_rate", 0.0),
                m20=metrics.get("match_at_least_20_tokens_rate", 0.0),
                m50=metrics.get("match_at_least_50_tokens_rate", 0.0),
                mean=metrics["mean_matching_prefix_tokens"],
                p95=metrics["p95_matching_prefix_tokens"],
                maximum=metrics["max_matching_prefix_tokens"],
                aligned=metrics["mean_aligned_token_accuracy"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Long exact spans are evidence of extractable verbatim recall, but this held-in training-source probe alone cannot distinguish memorization from highly predictable or duplicated text. Short token matches are not strong evidence.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="exports/dfm8_XL_step1650000_ema_hf")
    parser.add_argument("--source", type=Path, default=Path("data/downloads/datasets/lexdk/lexdk_articles.jsonl.gz"))
    parser.add_argument("--chat-template", type=Path, default=Path("evaluation/chat_templates/gemma4_native_chat.jinja"))
    parser.add_argument("--output-dir", type=Path, default=Path("logs/analysis/lexdk_prefix_extraction_step1650000"))
    parser.add_argument("--prefix-tokens", type=parse_int_list, default=parse_int_list("32,64,128,256"))
    parser.add_argument("--target-tokens", type=int, default=64)
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--seed", type=int, default=1650000)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.08)
    parser.add_argument("--max-model-len", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    if args.samples < 0:
        parser.error("--samples must be zero (all eligible rows) or positive")
    if args.num_shards < 1:
        parser.error("--num-shards must be positive")
    if not 0 <= args.shard_index < args.num_shards:
        parser.error("--shard-index must be in [0, --num-shards)")

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    template = jinja2.Environment().from_string(args.chat_template.read_text(encoding="utf-8"))
    assistant_header = render_generation_prompt(template, tokenizer)
    bos_id = tokenizer.bos_token_id
    if bos_id is None:
        raise RuntimeError("export tokenizer has no BOS token")

    source_rows = (
        row
        for ordinal, row in enumerate(iter_source_rows(args.source))
        if ordinal % args.num_shards == args.shard_index
    )
    sampled = sample_by_prefix(
        source_rows,
        tokenizer,
        args.prefix_tokens,
        args.target_tokens,
        args.samples or None,
        args.seed,
    )
    for prefix_tokens in args.prefix_tokens:
        if args.samples and len(sampled[prefix_tokens]) < args.samples:
            raise RuntimeError(f"only {len(sampled[prefix_tokens])} rows qualify for prefix length {prefix_tokens}")

    llm = LLM(
        model=args.model,
        dtype="bfloat16",
        max_model_len=args.max_model_len,
        gpu_memory_utilization=args.gpu_memory_utilization,
        enforce_eager=True,
        trust_remote_code=False,
        attention_backend="FLASH_ATTN",
    )
    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=args.target_tokens,
        skip_special_tokens=False,
    )

    requests: list[tuple[str, int, SourceRow, list[int], list[int]]] = []
    for prefix_tokens, examples in sampled.items():
        for row, source_ids in examples:
            prefix = source_ids[:prefix_tokens]
            target = source_ids[prefix_tokens : prefix_tokens + args.target_tokens]
            requests.append(("raw", prefix_tokens, row, [bos_id, *prefix], target))
            requests.append(("assistant_prefill", prefix_tokens, row, [*assistant_header, *prefix], target))

    results: list[dict[str, Any]] = []
    for start in range(0, len(requests), max(1, args.batch_size)):
        batch = requests[start : start + max(1, args.batch_size)]
        outputs = llm.generate(
            [TokensPrompt(prompt_token_ids=item[3]) for item in batch],
            sampling_params,
            use_tqdm=False,
        )
        for (mode, prefix_tokens, row, prompt_ids, target), output in zip(batch, outputs, strict=True):
            generated = [int(token) for token in output.outputs[0].token_ids]
            lcp = longest_common_prefix(target, generated)
            aligned_matches = sum(expected == actual for expected, actual in zip(target, generated))
            results.append(
                {
                    "mode": mode,
                    "shard_index": args.shard_index,
                    "num_shards": args.num_shards,
                    "prefix_tokens": prefix_tokens,
                    "target_tokens": args.target_tokens,
                    "source_id": row.row_id,
                    "title": row.title,
                    "url": row.url,
                    "prompt_token_count": len(prompt_ids),
                    "generated_token_count": len(generated),
                    "matching_prefix_tokens": lcp,
                    "aligned_token_accuracy": aligned_matches / args.target_tokens,
                    "exact_target": generated[: args.target_tokens] == target and len(generated) >= args.target_tokens,
                    "source_prefix": tokenizer.decode(prompt_ids[-prefix_tokens:], skip_special_tokens=False),
                    "reference_continuation": tokenizer.decode(target, skip_special_tokens=False),
                    "generated_continuation": tokenizer.decode(generated, skip_special_tokens=False),
                    "reference_token_ids": target,
                    "generated_token_ids": generated,
                }
            )
        print(f"completed {min(start + len(batch), len(requests))}/{len(requests)}", flush=True)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows_path = args.output_dir / "results.jsonl"
    with rows_path.open("w", encoding="utf-8") as handle:
        for row in results:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = summarize(results, args.target_tokens)
    (args.output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(args.output_dir / "report.md", args, summary)
    print(json.dumps(summary, indent=2))
    print(f"wrote {rows_path}")


if __name__ == "__main__":
    main()
