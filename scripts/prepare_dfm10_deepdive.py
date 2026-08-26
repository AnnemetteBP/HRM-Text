#!/usr/bin/env python3
"""Convert Z.ai DeepDive SFT trajectories to Gemma4-native tool-use chats."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


TOOL_CALL_RE = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)
THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
TRAIN_TOOLS = ("search", "click", "open")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(
            "data/downloads/datasets/zai_deepdive/data/"
            "trajectories_sft-00000-of-00001.parquet"
        ),
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/dfm10_deepdive_sources")
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_source_id(index: int, question: str) -> str:
    digest = hashlib.blake2b(question.encode("utf-8"), digest_size=10).hexdigest()
    return f"{index:04d}-{digest}"


def extract_tool_schemas(system_text: str) -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for line in system_text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        name = item.get("name")
        if not isinstance(name, str) or not isinstance(item.get("input_schema"), dict):
            continue
        schemas[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": str(item.get("description") or ""),
                "parameters": item["input_schema"],
            },
        }
    expected = set(TRAIN_TOOLS) | {"finish"}
    if set(schemas) != expected:
        raise ValueError(
            f"unexpected DeepDive tool schemas: {sorted(schemas)}; "
            f"expected {sorted(expected)}"
        )
    return schemas


def parse_single_tool_call(content: str) -> dict[str, Any]:
    matches = TOOL_CALL_RE.findall(content)
    if len(matches) != 1:
        raise ValueError(f"expected one tool call, found {len(matches)}")
    call = json.loads(matches[0])
    if not isinstance(call, dict) or not isinstance(call.get("name"), str):
        raise ValueError("invalid tool-call object")
    arguments = call.get("arguments", {})
    if not isinstance(arguments, dict):
        raise ValueError("tool-call arguments must be an object")
    return {"name": call["name"], "arguments": arguments}


def convert_row(
    row: dict[str, Any], index: int, stats: Counter[str]
) -> dict[str, Any]:
    raw_messages = row.get("conversations")
    if not isinstance(raw_messages, list) or len(raw_messages) < 3:
        raise ValueError("missing trajectory messages")
    if raw_messages[0].get("role") != "system":
        raise ValueError("trajectory does not start with the tool-system message")

    schemas = extract_tool_schemas(str(raw_messages[0].get("content") or ""))
    tools = [schemas[name] for name in TRAIN_TOOLS]
    messages: list[dict[str, Any]] = []
    pending: tuple[str, str] | None = None
    final_seen = False

    for message_index, raw in enumerate(raw_messages[1:], start=1):
        role = str(raw.get("role") or "")
        content = str(raw.get("content") or "")
        if role == "user":
            if pending is not None or final_seen:
                raise ValueError(f"message {message_index}: misplaced user message")
            messages.append({"role": "user", "content": content.strip()})
            continue

        if role == "assistant":
            if pending is not None or final_seen:
                raise ValueError(f"message {message_index}: misplaced assistant message")
            call = parse_single_tool_call(content)
            stats["think_blocks_removed"] += len(THINK_RE.findall(content))
            visible = THINK_RE.sub("", TOOL_CALL_RE.sub("", content)).strip()
            if visible:
                stats["legacy_visible_filler_removed"] += 1

            name = call["name"]
            if name == "finish":
                answer = str(row.get("answer") or "").strip()
                if not answer:
                    raise ValueError(f"message {message_index}: empty gold answer")
                messages.append({"role": "assistant", "content": answer})
                stats["final_answers"] += 1
                final_seen = True
                continue
            if name not in TRAIN_TOOLS:
                raise ValueError(f"message {message_index}: unsupported tool {name!r}")
            call_id = f"call_{stats['tool_calls']:08d}"
            messages.append(
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "type": "function",
                            "id": call_id,
                            "function": {
                                "name": name,
                                "arguments": call["arguments"],
                            },
                        }
                    ],
                }
            )
            pending = (call_id, name)
            stats["tool_calls"] += 1
            stats[f"tool_calls_{name}"] += 1
            continue

        if role == "tool":
            if pending is None or final_seen:
                raise ValueError(f"message {message_index}: unmatched tool response")
            call_id, name = pending
            messages.append(
                {
                    "role": "tool",
                    "name": name,
                    "tool_call_id": call_id,
                    "content": content.strip(),
                }
            )
            pending = None
            stats["tool_responses"] += 1
            continue

        raise ValueError(f"message {message_index}: unsupported role {role!r}")

    if pending is not None:
        raise ValueError("trajectory ends with an unanswered tool call")
    if not final_seen or messages[-1].get("role") != "assistant":
        raise ValueError("trajectory has no final answer")
    if not messages or messages[0].get("role") != "user":
        raise ValueError("converted trajectory does not begin with a user message")

    question = str(row.get("question") or "").strip()
    if messages[0]["content"] != question:
        raise ValueError("question field and first user message differ")
    source_id = stable_source_id(index, question)
    return {
        "messages": messages,
        "tools": tools,
        "source": "zai-org/DeepDive",
        "source_id": source_id,
        "source_row_index": index,
        "source_original_id": row.get("id"),
        "split": "trajectories_sft",
    }


def parquet_rows(path: Path) -> Iterator[dict[str, Any]]:
    for batch in pq.ParquetFile(path).iter_batches(batch_size=128):
        yield from batch.to_pylist()


def main() -> None:
    args = parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    if args.output_dir.exists():
        if not args.force:
            raise FileExistsError(f"{args.output_dir} exists; pass --force to rebuild")
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True)

    output = args.output_dir / "zai_deepdive_trajectories_sft__train.jsonl"
    stats: Counter[str] = Counter()
    source_ids: set[str] = set()
    with output.open("w", encoding="utf-8") as handle:
        for index, row in enumerate(parquet_rows(args.input)):
            try:
                converted = convert_row(row, index, stats)
            except Exception as exc:
                raise ValueError(f"DeepDive row {index}: {exc}") from exc
            source_id = converted["source_id"]
            if source_id in source_ids:
                raise ValueError(f"duplicate stable source ID: {source_id}")
            source_ids.add(source_id)
            handle.write(json.dumps(converted, ensure_ascii=False, sort_keys=True) + "\n")
            stats["rows"] += 1

    if stats["rows"] != 858 or stats["final_answers"] != stats["rows"]:
        raise ValueError(f"unexpected DeepDive conversion totals: {dict(stats)}")
    if stats["tool_calls"] != stats["tool_responses"]:
        raise ValueError(f"tool-call/response mismatch: {dict(stats)}")

    manifest = {
        "source": "zai-org/DeepDive",
        "source_file": str(args.input.resolve()),
        "source_sha256": sha256(args.input),
        "source_split": "trajectories_sft",
        "source_original_id_note": (
            "The upstream id column is constant (858); source_id is derived from "
            "the row index and a BLAKE2 hash of the unique question."
        ),
        "conversion": (
            "Old XML/ReAct calls are converted to Gemma4-native structured "
            "search/click/open calls. Visible <think> and legacy filler are removed; "
            "the terminal finish call becomes the upstream gold answer."
        ),
        "stats": dict(sorted(stats.items())),
        "output": str(output.resolve()),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
