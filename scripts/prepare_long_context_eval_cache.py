#!/usr/bin/env python3
"""Pre-build and exactly verify deterministic long-context evaluation inputs."""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from transformers import AutoTokenizer


_TOKENIZER = None
_CHAT_TEMPLATE = ""
_MAX_INPUT_TOKENS = 0
_TRUNCATION_MARKER = "\n[... context truncated ...]\n"


def _init_worker(tokenizer_path: str, chat_template_path: str, max_input_tokens: int) -> None:
    global _TOKENIZER, _CHAT_TEMPLATE, _MAX_INPUT_TOKENS
    _TOKENIZER = AutoTokenizer.from_pretrained(
        tokenizer_path,
        trust_remote_code=True,
        local_files_only=True,
    )
    _CHAT_TEMPLATE = Path(chat_template_path).read_text(encoding="utf-8")
    _MAX_INPUT_TOKENS = max_input_tokens


def _rendered_token_count(text: str) -> int:
    assert _TOKENIZER is not None
    rendered = _TOKENIZER.apply_chat_template(
        [{"role": "user", "content": text}],
        chat_template=_CHAT_TEMPLATE,
        tokenize=False,
        add_generation_prompt=True,
    )
    return len(_TOKENIZER.encode(rendered, add_special_tokens=False))


def _candidate(ids: list[int], retained: int) -> str:
    assert _TOKENIZER is not None
    if retained >= len(ids):
        return _TOKENIZER.decode(ids, skip_special_tokens=False)
    head = max(1, int(retained * 0.65))
    tail = max(0, retained - head)
    return (
        _TOKENIZER.decode(ids[:head], skip_special_tokens=False)
        + _TRUNCATION_MARKER
        + (_TOKENIZER.decode(ids[-tail:], skip_special_tokens=False) if tail else "")
    )


def _fit_row(item: tuple[int, dict[str, Any]]) -> tuple[int, dict[str, Any], int, bool]:
    index, row = item
    assert _TOKENIZER is not None
    text = str(row["input"])
    count = _rendered_token_count(text)
    truncated = count > _MAX_INPUT_TOKENS
    if truncated:
        ids = _TOKENIZER.encode(text, add_special_tokens=False)
        low, high = 1, len(ids)
        best_text = _candidate(ids, 1)
        best_count = _rendered_token_count(best_text)
        if best_count > _MAX_INPUT_TOKENS:
            raise ValueError(f"row {index}: framing alone exceeds input budget")
        while low <= high:
            middle = (low + high) // 2
            candidate = _candidate(ids, middle)
            candidate_count = _rendered_token_count(candidate)
            if candidate_count <= _MAX_INPUT_TOKENS:
                best_text, best_count = candidate, candidate_count
                low = middle + 1
            else:
                high = middle - 1
        text, count = best_text, best_count

    if count > _MAX_INPUT_TOKENS:
        raise AssertionError(f"row {index}: {count} > {_MAX_INPUT_TOKENS}")
    row = dict(row)
    row["input"] = text
    metadata = dict(row.get("metadata") or {})
    metadata["rendered_input_tokens"] = count
    metadata["rendered_input_limit"] = _MAX_INPUT_TOKENS
    row["metadata"] = metadata
    return index, row, count, truncated


def _atomic_write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/eval_cache/long_context/v7_longalign_en_gen512.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/eval_cache/long_context/v8_longalign_en_gen512.jsonl"),
    )
    parser.add_argument(
        "--tokenizer-path",
        default="exports/dfm9_8k_step_2150000_ema_hf",
    )
    parser.add_argument(
        "--chat-template",
        type=Path,
        default=Path("evaluation/chat_templates/gemma4_native_chat.jinja"),
    )
    parser.add_argument("--context-length", type=int, default=8192)
    parser.add_argument("--max-output-tokens", type=int, default=512)
    parser.add_argument("--safety-tokens", type=int, default=32)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    max_input_tokens = args.context_length - args.max_output_tokens - args.safety_tokens
    if args.workers < 1 or max_input_tokens < 1:
        raise ValueError("workers and the computed input budget must be positive")

    with args.source.open(encoding="utf-8") as source:
        rows = [json.loads(line) for line in source if line.strip()]
    print(
        f"Fitting {len(rows):,} rows with {args.workers} processes; "
        f"rendered input <= {max_input_tokens:,} tokens",
        flush=True,
    )
    context = mp.get_context("spawn")
    with ProcessPoolExecutor(
        max_workers=args.workers,
        mp_context=context,
        initializer=_init_worker,
        initargs=(str(args.tokenizer_path), str(args.chat_template), max_input_tokens),
    ) as pool:
        fitted = list(pool.map(_fit_row, enumerate(rows), chunksize=8))

    fitted.sort(key=lambda item: item[0])
    output_rows = [item[1] for item in fitted]
    counts = [item[2] for item in fitted]
    truncated = sum(item[3] for item in fitted)
    if len({str(row["id"]) for row in output_rows}) != len(output_rows):
        raise AssertionError("prepared row IDs are not unique")
    _atomic_write_jsonl(args.output, output_rows)
    print(
        f"Wrote {len(output_rows):,} rows to {args.output}; "
        f"truncated={truncated:,}, rendered_min={min(counts):,}, "
        f"rendered_max={max(counts):,}",
        flush=True,
    )


if __name__ == "__main__":
    main()
