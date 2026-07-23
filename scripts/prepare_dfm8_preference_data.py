#!/usr/bin/env python3
"""Build a Gemma4-template-safe DFM8 preference-pair export.

The output is JSONL, not a sampled SFT dataset. Each row contains:

- prompt_messages: messages before the assistant response
- tools: OpenAI/Gemma-style tool declarations
- chosen_completion_messages: preferred assistant/tool continuation
- rejected_completion_messages: rejected assistant/tool continuation

This keeps DPO data separate from SFT data and avoids teaching ChatML, XML
tool-call tags, or Llama-Factory wrappers as literal target text.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import jinja2
import pyarrow.parquet as pq


ROOTS = {
    "roborovski_glaive_tool_usage_dpo": "tool_calling",
    "roborovski_synthetic_tool_calls_v2_dpo_pairs": "tool_calling_structured",
    "roborovski_synthetic_toolformer_dpo_pairs": "tool_calling_structured",
    "interstellarninja_tool_calls_dpo": "tool_calling",
    "hodfa71_saga_da_delta_dpo_r1": "danish_grammar_completion",
    "hodfa71_saga_da_delta_dpo_r2": "danish_grammar_completion",
    "allenai_dolci_think_dpo_7b": "general_reasoning",
    "argilla_distilabel_math_preference_dpo": "math_preference",
    "tzwilliam0_instruction_following_dpo_filtered": "instruction_following",
    "tzwilliam0_instruction_following_dpo_filtered_add": "instruction_following",
    "mlabonne_chatml_openhermes25_dpo_binarized_alpha": "format_following_openhermes",
    "capx_agentic_dpo_v01": "agentic_general",
}

ADJACENT_NOT_DPO = {
    "qnguyen3_dpo_r1": "SFT-shaped tool messages; no chosen/rejected pair columns.",
    "zake7749_qwen36_35b_a3b_tool_calling": "Tool-call SFT rows; card describes preference pipeline, but local file is final SFT.",
    "kkachi_hub_tool_dpo_llama_factory": "Gated; local metadata may exist, but file download still awaited repo-author approval.",
}

OLD_TEMPLATE_MARKERS = ("<|im_start|>", "<|im_end|>", "<tool_call>", "</tool_call>", "<tools>", "</tools>", "[/INST]", "<s>[INST]")
MAX_RAW_RECORD_CHARS = 300_000
TOOL_XML_RE = re.compile(r"<tools>(.*?)</tools>", re.DOTALL)
TOOL_CALL_XML_RE = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)


@dataclass
class ConvertResult:
    rows: int = 0
    skipped: int = 0
    render_failed: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download-root", type=Path, default=Path("data/downloads/datasets"))
    parser.add_argument("--output-root", type=Path, default=Path("data/dfm8_preference_pairs"))
    parser.add_argument("--chat-template", type=Path, default=Path("data_io/chat_templates/gemma4_native_chat.jinja"))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--max-rows-per-source", type=int, default=None)
    return parser.parse_args()


def clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("<|endoftext|>", "").replace("<|endoftext|", "").strip()


def parse_literal(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return None
    for loader in (json.loads, ast.literal_eval):
        try:
            return loader(text)
        except Exception:
            pass
    return None


def balanced_object_after_marker(text: str, marker: str = " - ") -> Any:
    if marker in text:
        text = text.split(marker, 1)[1]
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    quote = ""
    escape = False
    for pos in range(start, len(text)):
        ch = text[pos]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_string = False
            continue
        if ch in {"'", '"'}:
            in_string = True
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return parse_literal(text[start:pos + 1])
    return None


def normalize_tool(tool: Any) -> dict[str, Any] | None:
    if isinstance(tool, str):
        tool = parse_literal(tool)
    if not isinstance(tool, dict):
        return None
    if tool.get("type") == "function" and isinstance(tool.get("function"), dict):
        function = dict(tool["function"])
    else:
        function = dict(tool)
    name = function.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    params = function.get("parameters")
    if not isinstance(params, dict):
        params = {"type": "object", "properties": {}, "required": []}
    params.setdefault("type", "object")
    params.setdefault("properties", {})
    params.setdefault("required", [])
    out = {
        "type": "function",
        "function": {
            "name": name.strip(),
            "description": str(function.get("description") or "").strip(),
            "parameters": params,
        },
    }
    return out


def normalize_tools(value: Any) -> list[dict[str, Any]]:
    parsed = parse_literal(value)
    if isinstance(parsed, dict):
        items = [parsed]
    elif isinstance(parsed, list):
        items = parsed
    else:
        items = []
    tools = [tool for item in items if (tool := normalize_tool(item)) is not None]
    return tools


def extract_tools_from_system(system: str) -> tuple[str, list[dict[str, Any]]]:
    match = TOOL_XML_RE.search(system)
    if match:
        tools = normalize_tools(match.group(1))
        cleaned = TOOL_XML_RE.sub("", system).strip()
        cleaned = re.sub(r"You are provided with function signatures.*?(query\\.|$)", "Use the available tools when they are relevant.", cleaned, flags=re.I | re.S)
        return cleaned or "Use the available tools when they are relevant.", tools
    tool_obj = balanced_object_after_marker(system)
    if tool_obj is not None:
        prefix = system.split(" - ", 1)[0].strip() if " - " in system else "Use the available tools when they are relevant."
        return prefix, normalize_tools(tool_obj)
    return system.strip(), []


def tool_name(tools: list[dict[str, Any]]) -> str:
    if tools:
        return str(tools[0]["function"]["name"])
    return "tool"


def tool_call_message(name: str, args: Any, call_id: str = "call_0") -> dict[str, Any]:
    parsed_args = parse_literal(args)
    if not isinstance(parsed_args, dict):
        parsed_args = {}
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [{
            "id": call_id,
            "type": "function",
            "function": {"name": name, "arguments": parsed_args},
        }],
    }


def tool_response_message(name: str, result: Any, call_id: str = "call_0") -> dict[str, Any]:
    parsed = parse_literal(result)
    content = json.dumps(parsed, ensure_ascii=False, default=str) if parsed is not None else clean_text(result)
    return {"role": "tool", "tool_call_id": call_id, "name": name, "content": content}


def simple_pair(
    source: str,
    idx: int,
    task_family: str,
    prompt: str,
    chosen: str,
    rejected: str,
    *,
    system: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    language: str = "en",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    prompt = clean_text(prompt)
    chosen = clean_text(chosen)
    rejected = clean_text(rejected)
    if not prompt or not chosen or not rejected:
        return None
    prompt_messages = []
    if system and system.strip():
        prompt_messages.append({"role": "system", "content": clean_text(system)})
    prompt_messages.append({"role": "user", "content": prompt})
    return {
        "id": f"{source}:{idx}",
        "source": source,
        "task_family": task_family,
        "language": language,
        "prompt_messages": prompt_messages,
        "tools": tools or [],
        "chosen_completion_messages": [{"role": "assistant", "content": chosen}],
        "rejected_completion_messages": [{"role": "assistant", "content": rejected}],
        "metadata": metadata or {},
    }


def danish_completion_pair(source: str, idx: int, row: dict[str, Any], task_family: str) -> dict[str, Any] | None:
    prompt = clean_text(row.get("prompt"))
    return simple_pair(
        source,
        idx,
        task_family,
        f"Fortsæt den danske tekst på en grammatisk korrekt og naturlig måde.\n\nTekst:\n{prompt}",
        clean_text(row.get("chosen")),
        clean_text(row.get("rejected")),
        language="da",
        metadata={k: row.get(k) for k in ("chosen_score", "rejected_score", "delta")},
    )


def tool_text_pair(source: str, idx: int, row: dict[str, Any], task_family: str) -> dict[str, Any] | None:
    system, tools = extract_tools_from_system(clean_text(row.get("system")))
    chosen = clean_text(row.get("chosen"))
    rejected = clean_text(row.get("rejected"))
    # XML tool-call targets are old-template text. Parse them to native tool
    # calls when they occur, otherwise skip if they cannot be normalized.
    if TOOL_CALL_XML_RE.search(chosen) or TOOL_CALL_XML_RE.search(rejected):
        chosen_msgs = parse_xml_tool_completion(chosen, tools)
        rejected_msgs = parse_xml_tool_completion(rejected, tools)
        if chosen_msgs is None or rejected_msgs is None:
            return None
        rec = simple_pair(source, idx, task_family, clean_text(row.get("question")), "placeholder", "placeholder", system=system, tools=tools)
        if rec is None:
            return None
        rec["chosen_completion_messages"] = chosen_msgs
        rec["rejected_completion_messages"] = rejected_msgs
        return rec
    return simple_pair(source, idx, task_family, clean_text(row.get("question")), chosen, rejected, system=system, tools=tools)


def parse_xml_tool_completion(text: str, tools: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    match = TOOL_CALL_XML_RE.search(text)
    if not match:
        content = clean_text(text)
        return [{"role": "assistant", "content": content}] if content else None
    parsed = parse_literal(match.group(1).strip())
    if not isinstance(parsed, dict):
        return None
    name = parsed.get("name") or tool_name(tools)
    args = parsed.get("arguments")
    return [tool_call_message(str(name), args)]


def structured_tool_pair(source: str, idx: int, row: dict[str, Any], task_family: str) -> dict[str, Any] | None:
    tools = normalize_tools(row.get("tool"))
    name = tool_name(tools)
    rec = simple_pair(
        source,
        idx,
        task_family,
        clean_text(row.get("question")),
        "placeholder",
        "placeholder",
        system="Use the available tools when they are relevant.",
        tools=tools,
    )
    if rec is None:
        return None
    rec["chosen_completion_messages"] = [
        tool_call_message(name, row.get("tool_call_accepted")),
        tool_response_message(name, row.get("call_result_accepted")),
        {"role": "assistant", "content": clean_text(row.get("agent_output_accepted"))},
    ]
    rec["rejected_completion_messages"] = [
        tool_call_message(name, row.get("tool_call_rejected")),
        tool_response_message(name, row.get("call_result_rejected")),
        {"role": "assistant", "content": clean_text(row.get("agent_output_rejected"))},
    ]
    return rec


def dolci_pair(source: str, idx: int, row: dict[str, Any], task_family: str) -> dict[str, Any] | None:
    chosen = row.get("chosen")
    rejected = row.get("rejected")
    if not isinstance(chosen, list) or not isinstance(rejected, list):
        return None
    prompt_messages = normalize_prompt_from_conversation(chosen)
    chosen_completion = normalize_completion_from_conversation(chosen, len(prompt_messages))
    rejected_completion = normalize_completion_from_conversation(rejected, len(prompt_messages))
    if not prompt_messages or not chosen_completion or not rejected_completion:
        return None
    return {
        "id": f"{source}:{idx}",
        "source": source,
        "task_family": task_family,
        "language": "en",
        "prompt_messages": prompt_messages,
        "tools": [],
        "chosen_completion_messages": chosen_completion,
        "rejected_completion_messages": rejected_completion,
        "metadata": {k: row.get(k) for k in ("chosen_model", "rejected_model", "dataset_source", "preference_type", "id")},
    }


def normalize_prompt_from_conversation(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for message in messages:
        role = str(message.get("role") or "").lower()
        content = clean_text(message.get("content"))
        if role == "assistant":
            break
        if role in {"system", "developer"}:
            out.append({"role": "system", "content": content})
        elif role == "user" and content:
            out.append({"role": "user", "content": content})
    return out


def normalize_completion_from_conversation(messages: list[dict[str, Any]], prompt_len: int) -> list[dict[str, Any]]:
    out = []
    for message in messages[prompt_len:]:
        role = str(message.get("role") or "").lower()
        content = clean_text(message.get("content"))
        if role == "assistant" and content:
            out.append({"role": "assistant", "content": content})
        elif role == "user":
            break
    return out[:1]


def argilla_math_pair(source: str, idx: int, row: dict[str, Any], task_family: str) -> dict[str, Any] | None:
    return simple_pair(
        source,
        idx,
        task_family,
        clean_text(row.get("instruction")),
        clean_text(row.get("chosen_response")),
        clean_text(row.get("rejected_response")),
        metadata={k: row.get(k) for k in ("metadata", "chosen_rating", "rejected_rating")},
    )


def capx_pair(source: str, idx: int, row: dict[str, Any], task_family: str) -> dict[str, Any] | None:
    return simple_pair(
        source,
        idx,
        task_family,
        clean_text(row.get("prompt")),
        clean_text(row.get("chosen")),
        clean_text(row.get("rejected")),
        system=clean_text(row.get("instruction")),
        metadata={"id": row.get("id")},
    )


def converter_for(source: str):
    if source.startswith("hodfa71_saga"):
        return danish_completion_pair
    if source in {"roborovski_glaive_tool_usage_dpo", "interstellarninja_tool_calls_dpo"}:
        return tool_text_pair
    if source in {"roborovski_synthetic_tool_calls_v2_dpo_pairs", "roborovski_synthetic_toolformer_dpo_pairs"}:
        return structured_tool_pair
    if source == "allenai_dolci_think_dpo_7b":
        return dolci_pair
    if source == "argilla_distilabel_math_preference_dpo":
        return argilla_math_pair
    if source == "capx_agentic_dpo_v01":
        return capx_pair
    return lambda source, idx, row, task_family: simple_pair(
        source, idx, task_family,
        clean_text(row.get("prompt") or row.get("question")),
        clean_text(row.get("chosen")),
        clean_text(row.get("rejected")),
    )


def iter_rows(root: Path) -> Iterable[dict[str, Any]]:
    parquet_files = sorted(root.rglob("*.parquet"))
    if parquet_files:
        for path in parquet_files:
            for row in pq.read_table(path).to_pylist():
                yield row
        return
    data_json = root / "data.json"
    if data_json.exists():
        data = json.loads(data_json.read_text(encoding="utf-8"))
        if isinstance(data, list):
            yield from data


def render_pair(template: jinja2.Template, record: dict[str, Any]) -> None:
    raw = json.dumps({
        "prompt_messages": record.get("prompt_messages"),
        "chosen_completion_messages": record.get("chosen_completion_messages"),
        "rejected_completion_messages": record.get("rejected_completion_messages"),
    }, ensure_ascii=False, default=str)
    if len(raw) > MAX_RAW_RECORD_CHARS:
        raise ValueError(f"converted row too long for preference export: {len(raw)} chars")
    if any(marker in raw for marker in OLD_TEMPLATE_MARKERS):
        raise ValueError("old template marker present in raw converted messages")
    for side in ("chosen_completion_messages", "rejected_completion_messages"):
        messages = record["prompt_messages"] + record[side]
        rendered = template.render(
            messages=messages,
            tools=record.get("tools") or [],
            bos_token="<bos>",
            add_generation_prompt=False,
            enable_thinking=False,
        )
        if any(marker in rendered for marker in OLD_TEMPLATE_MARKERS):
            raise ValueError("old template marker leaked into rendered Gemma4 text")
        if "<|turn>" not in rendered:
            raise ValueError("Gemma4 turn marker missing")


def main() -> None:
    args = parse_args()
    if args.output_root.exists() and args.force:
        shutil.rmtree(args.output_root)
    args.output_root.mkdir(parents=True, exist_ok=True)
    # Match scripts/tokenize_chat_template.py: the template deliberately treats
    # missing optional fields such as enum, nullable, and tool_calls as false.
    template = jinja2.Environment().from_string(args.chat_template.read_text())

    manifest: dict[str, Any] = {
        "output_root": str(args.output_root),
        "chat_template": str(args.chat_template),
        "sources": {},
        "adjacent_not_dpo": ADJACENT_NOT_DPO,
        "notes": [
            "All rows are rendered through the Gemma4 native chat template during conversion.",
            "Rows that would preserve old XML/ChatML tool markers as target text are skipped unless normalized.",
            "This is a DPO/preference export, not an SFT tokenized dataset.",
        ],
    }
    family_counts: Counter[str] = Counter()
    language_counts: Counter[str] = Counter()

    for source, task_family in ROOTS.items():
        root = args.download_root / source
        result = ConvertResult()
        if not root.exists():
            manifest["sources"][source] = {"status": "missing", "task_family": task_family}
            continue
        converter = converter_for(source)
        out = args.output_root / f"{source}.jsonl"
        with out.open("w", encoding="utf-8") as handle:
            for idx, row in enumerate(iter_rows(root)):
                if args.max_rows_per_source is not None and result.rows >= args.max_rows_per_source:
                    break
                record = converter(source, idx, dict(row), task_family)
                if record is None:
                    result.skipped += 1
                    continue
                try:
                    render_pair(template, record)
                except Exception as exc:
                    result.render_failed += 1
                    result.skipped += 1
                    if result.render_failed <= 5:
                        (args.output_root / "render_failures.jsonl").open("a", encoding="utf-8").write(json.dumps({
                            "source": source,
                            "idx": idx,
                            "error": str(exc),
                        }, ensure_ascii=False) + "\n")
                    continue
                handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
                result.rows += 1
                family_counts[task_family] += 1
                language_counts[str(record.get("language") or "unknown")] += 1
        manifest["sources"][source] = {
            "status": "converted",
            "task_family": task_family,
            "path": str(out),
            "rows": result.rows,
            "skipped": result.skipped,
            "render_failed": result.render_failed,
        }

    manifest["family_counts"] = dict(sorted(family_counts.items()))
    manifest["language_counts"] = dict(sorted(language_counts.items()))
    manifest["total_rows"] = int(sum(family_counts.values()))
    (args.output_root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
