#!/usr/bin/env python3
"""Count text characters in the unique source records underlying DFM8."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pyarrow.parquet as pq
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tokenize_chat_template as chat_tokenizer  # noqa: E402


SOURCE_TREES = {
    "tokenized_dfm6_direct_jinja": Path("data/dfm6_chat_sources"),
    "tokenized_dfm7_jinja": Path("data/dfm7_chat_sources"),
    "tokenized_dfm8_jinja": Path("data/dfm8_chat_sources"),
}

IGNORED_MESSAGE_KEYS = {"role", "tool_call_id", "id", "type"}


@dataclass(frozen=True)
class Count:
    chars: int = 0
    rows: int = 0
    bytes: int = 0

    def __add__(self, other: "Count") -> "Count":
        return Count(self.chars + other.chars, self.rows + other.rows, self.bytes + other.bytes)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokenized-tree", type=Path, default=Path("data/tokenized_dfm8"))
    parser.add_argument("--workers", type=int, default=8)
    return parser.parse_args()


def text_chars(value: Any, *, ignored_keys: set[str] = frozenset()) -> int:
    if isinstance(value, str):
        return len(value)
    if isinstance(value, list):
        return sum(text_chars(item, ignored_keys=ignored_keys) for item in value)
    if isinstance(value, dict):
        return sum(
            text_chars(item, ignored_keys=ignored_keys)
            for key, item in value.items()
            if key not in ignored_keys
        )
    return 0


def count_row(row: dict[str, Any]) -> tuple[int, bool]:
    if "response" in row:
        condition = str(row.get("condition") or "direct")
        instruction = str(row.get("instruction") or "")
        response = str(row.get("response") or "")
        return len(condition) + len(instruction) + len(response), True

    messages = row.get("messages")
    if isinstance(messages, list):
        last_target = -1
        for index, raw in enumerate(messages):
            if not isinstance(raw, dict):
                continue
            message = chat_tokenizer.normalize_message(raw)
            content = message.get("content", "")
            if str(message.get("role", "")).lower() == "assistant" and (
                (isinstance(content, str) and content.strip()) or message.get("tool_calls")
            ):
                last_target = index
        if last_target < 0:
            return 0, False
        chars = text_chars(messages[: last_target + 1], ignored_keys=IGNORED_MESSAGE_KEYS)
        tools = row.get("tools")
        if isinstance(tools, list):
            chars += text_chars(tools, ignored_keys={"type"})
        else:
            chars += text_chars(chat_tokenizer.tools_from_messages(messages), ignored_keys={"type"})
        return chars, True

    example = chat_tokenizer.generic_row_to_messages(row)
    if example is None:
        return 0, False
    return len(example.condition) + len(example.instruction) + len(example.response), True


def iter_json_rows(path: Path) -> Iterable[dict[str, Any]]:
    opener = gzip.open if path.name.endswith(".gz") else open
    decoder = json.JSONDecoder(strict=False)
    with opener(path, "rt", encoding="utf-8") as handle:
        buffer = ""
        for line in handle:
            if not line.strip() and not buffer:
                continue
            buffer += line
            try:
                row, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                if "\x00" in buffer:
                    buffer = ""
                continue
            if buffer[end:].strip():
                raise ValueError(f"Trailing data in {path}")
            buffer = ""
            if isinstance(row, dict):
                yield row


def parquet_columns(path: Path) -> list[str] | None:
    names = set(pq.ParquetFile(path).schema_arrow.names)
    if {"condition", "instruction", "response"}.issubset(names):
        return ["condition", "instruction", "response"]
    if "messages" in names:
        return [name for name in ("messages", "tools") if name in names]
    generic = (
        "instruction", "prompt", "question", "input", "text", "source", "document", "article",
        "response", "completion", "answer", "target", "output", "summary", "translation", "label",
        "condition", "task",
    )
    return [name for name in generic if name in names] or None


def count_file(path_string: str) -> Count:
    path = Path(path_string)
    chars = rows = 0
    if path.suffix == ".parquet":
        parquet = pq.ParquetFile(path)
        for batch in parquet.iter_batches(columns=parquet_columns(path)):
            for row in batch.to_pylist():
                row_chars, used = count_row(row)
                chars += row_chars
                rows += int(used)
    else:
        for row in iter_json_rows(path):
            row_chars, used = count_row(row)
            chars += row_chars
            rows += int(used)
    return Count(chars=chars, rows=rows, bytes=path.stat().st_size)


def resolve_sources(tokenized_tree: Path) -> list[Path]:
    source_maps: dict[str, dict[str, Path]] = {}
    for output_name, source_root in SOURCE_TREES.items():
        source_maps[output_name] = {
            found.safe_name: found.path.resolve()
            for found in chat_tokenizer.scan_inputs([source_root])
        }

    sources: list[Path] = []
    for link in sorted(tokenized_tree.iterdir()):
        if not link.is_symlink():
            continue
        artifact = link.resolve()
        if not artifact.is_dir():
            continue
        output_name = artifact.parent.name
        try:
            source = source_maps[output_name][artifact.name]
        except KeyError as error:
            raise KeyError(f"Cannot map tokenized artifact to source: {artifact}") from error
        expected = json.loads((artifact / "metadata.json").read_text())
        actual = chat_tokenizer.current_metadata(source)
        if expected != actual:
            raise RuntimeError(f"Source changed since tokenization: {source}; expected={expected}, actual={actual}")
        sources.append(source)
    if len(sources) != len(set(sources)):
        raise RuntimeError("DFM8 tokenized tree maps to duplicate physical source files")
    return sources


def main() -> None:
    args = parse_args()
    sources = resolve_sources(args.tokenized_tree)
    total_bytes = sum(path.stat().st_size for path in sources)
    total = Count()
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(count_file, str(path)): path for path in sources}
        with tqdm(total=total_bytes, unit="B", unit_scale=True, desc="Counting source text") as progress:
            for future in as_completed(futures):
                result = future.result()
                total += result
                progress.update(result.bytes)
                progress.set_postfix(chars=f"{total.chars:,}", rows=f"{total.rows:,}")
    print(json.dumps({"source_files": len(sources), "source_rows": total.rows, "source_chars": total.chars, "source_bytes": total.bytes}, indent=2))


if __name__ == "__main__":
    main()
