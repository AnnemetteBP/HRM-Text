#!/usr/bin/env python3
"""Audit DFM7 tool-calling sources before tokenization.

The audit checks converted native tool-call sources for:

- top-level `tools`
- rendered Gemma native tool declarations
- assistant `tool_calls`
- structured argument dicts rather than raw strings
- no XML function-calling contract remnants
- valid-ish function names after conversion

It also summarizes unconverted tool-adjacent sources so they are not mistaken
for native tool-call SFT.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import jinja2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.tokenize_chat_template import examples_from_messages, render


CONVERTED_SOURCES = {
    "dolci_native_tool_use": "data/dfm7_special_sources/dolci_native_tool_use",
    "glaive_native_tool_use": "data/dfm7_special_sources/glaive_native_tool_use",
    "toolace_native_tool_use": "data/dfm7_special_sources/toolace_native_tool_use",
    "xlam_native_tool_use": "data/dfm7_special_sources/xlam_native_tool_use",
}

UNCONVERTED_SOURCES = {
    "nemotron_agentic_tool_calling": "data/downloads/datasets/nemotron_agentic/data/tool_calling.jsonl",
    "nemotron_agentic_interactive_agent": "data/downloads/datasets/nemotron_agentic/data/interactive_agent.jsonl",
    "nemotron_agentic_search": "data/downloads/datasets/nemotron_agentic/data/search.jsonl",
    "dfm_dyna_instruct_when2call": "data/downloads/datasets/dfm_dyna_instruct/data/when2call/when2call.parquet",
    "dfm_dyna_instruct_agentic_code": "data/downloads/datasets/dfm_dyna_instruct/data/agentic-code-sft-mix-v1/agentic-code-sft-mix-v1.parquet",
}

XML_CONTRACT_RE = re.compile(
    r"<function_calls>|</function_calls>|"
    r"provided with function signatures within\s+<functions>|"
    r"Output any function calls within\s+<function_calls>",
    re.IGNORECASE,
)
FUNCTION_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chat-template", type=Path, default=Path("data_io/chat_templates/gemma4_native_chat.jinja"))
    parser.add_argument("--converted-limit", type=int, default=0, help="Rows per converted source; 0 means all rows.")
    parser.add_argument("--render-limit", type=int, default=2000, help="Rendered examples per converted source.")
    parser.add_argument("--unconverted-limit", type=int, default=5000, help="Rows per unconverted source.")
    parser.add_argument("--json-out", type=Path, default=Path("logs/dfm7_tool_source_audit.json"))
    parser.add_argument("--fail-on-issues", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    template = jinja2.Environment().from_string(args.chat_template.read_text(encoding="utf-8"))
    report: dict[str, Any] = {
        "converted": {},
        "unconverted": {},
        "issues": {},
    }
    total_issues = 0

    for name, root in CONVERTED_SOURCES.items():
        summary, issues = audit_converted_source(name, Path(root), template, args.converted_limit, args.render_limit)
        report["converted"][name] = summary
        report["issues"][name] = issues[:20]
        total_issues += len(issues)

    for name, path in UNCONVERTED_SOURCES.items():
        report["unconverted"][name] = audit_unconverted_source(Path(path), args.unconverted_limit)

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print_summary(report, total_issues, args.json_out)
    if args.fail_on_issues and total_issues:
        raise SystemExit(1)


def audit_converted_source(
    name: str,
    root: Path,
    template: jinja2.Template,
    limit: int,
    render_limit: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    summary = Counter()
    issues: list[dict[str, Any]] = []
    tool_names: Counter[str] = Counter()
    for path in sorted(root.rglob("*.jsonl")):
        for row_index, row in enumerate(iter_jsonl(path)):
            if limit and summary["rows"] >= limit:
                break
            summary["rows"] += 1
            messages = row.get("messages")
            tools = row.get("tools")
            if not isinstance(messages, list):
                add_issue(issues, path, row_index, "messages_not_list")
                continue
            if not isinstance(tools, list) or not tools:
                add_issue(issues, path, row_index, "missing_top_level_tools")
                continue
            for tool in tools:
                function = tool.get("function") if isinstance(tool, dict) else None
                name_value = function.get("name") if isinstance(function, dict) else None
                if isinstance(name_value, str):
                    tool_names[name_value] += 1
                    if not FUNCTION_NAME_RE.match(name_value):
                        add_issue(issues, path, row_index, "invalid_tool_name", name_value)
            if XML_CONTRACT_RE.search(messages_text(messages)):
                add_issue(issues, path, row_index, "xml_tool_contract_remnant")
            try:
                examples = list(examples_from_messages(messages, tools))
            except Exception as exc:  # noqa: BLE001 - audit should capture row-level errors.
                add_issue(issues, path, row_index, "example_extraction_error", repr(exc))
                continue
            summary["examples"] += len(examples)
            if not examples:
                add_issue(issues, path, row_index, "no_supervised_examples")
                continue
            row_has_tool_call = False
            for example_index, example in enumerate(examples):
                tool_calls = example.assistant_message.get("tool_calls") or []
                if tool_calls:
                    row_has_tool_call = True
                    summary["tool_call_examples"] += 1
                for call in tool_calls:
                    function = call.get("function") if isinstance(call, dict) else None
                    if not isinstance(function, dict):
                        add_issue(issues, path, row_index, "malformed_tool_call", {"example": example_index})
                        continue
                    arguments = function.get("arguments")
                    if not isinstance(arguments, dict):
                        add_issue(
                            issues,
                            path,
                            row_index,
                            "tool_call_arguments_not_mapping",
                            {"example": example_index, "arguments": repr(arguments)[:200]},
                        )
                if summary["rendered_examples"] >= render_limit:
                    continue
                if example_index == 0 or tool_calls:
                    prompt = render(template, example.prompt_messages, example.tools, True, False)
                    full = render(template, example.prompt_messages + [example.assistant_message], example.tools, False, False)
                    summary["rendered_examples"] += 1
                    if "<|tool>" not in prompt:
                        add_issue(issues, path, row_index, "rendered_prompt_missing_native_tool")
                    if XML_CONTRACT_RE.search(prompt):
                        add_issue(issues, path, row_index, "rendered_prompt_has_xml_contract")
                    if tool_calls and "<|tool_call>" not in full:
                        add_issue(issues, path, row_index, "rendered_full_missing_native_tool_call")
            if row_has_tool_call:
                summary["rows_with_tool_calls"] += 1
        if limit and summary["rows"] >= limit:
            break
    summary["distinct_tool_names"] = len(tool_names)
    summary["top_tool_names"] = tool_names.most_common(10)
    return dict(summary), issues


def audit_unconverted_source(path: Path, limit: int) -> dict[str, Any]:
    summary = Counter()
    if not path.exists():
        summary["missing"] = 1
        return dict(summary)
    for row in iter_rows(path):
        if limit and summary["rows"] >= limit:
            break
        summary["rows"] += 1
        messages = row.get("messages") or row.get("conversations") or []
        tools = row.get("tools")
        if isinstance(tools, list) and tools:
            summary["rows_with_top_level_tools"] += 1
        if any(isinstance(m, dict) and m.get("functions") for m in messages):
            summary["rows_with_message_functions"] += 1
        if XML_CONTRACT_RE.search(messages_text(messages)):
            summary["rows_with_xml_contract"] += 1
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = str(message.get("role") or message.get("from") or "").lower()
            if role == "assistant":
                summary["assistant_turns"] += 1
                if message.get("tool_calls") or message.get("function_calls"):
                    summary["assistant_turns_with_structured_tool_calls"] += 1
                content = str(message.get("content") or message.get("value") or "")
                if re.search(r"^[A-Za-z_][\w .-]*\([^)]*\)$", content.strip()):
                    summary["assistant_turns_with_call_like_text"] += 1
    return dict(summary)


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                try:
                    yield json.loads(line, strict=False)
                except json.JSONDecodeError:
                    continue


def iter_rows(path: Path):
    if path.suffix == ".jsonl":
        yield from iter_jsonl(path)
        return
    if path.suffix == ".parquet":
        import pyarrow.parquet as pq

        parquet_file = pq.ParquetFile(path)
        for batch in parquet_file.iter_batches():
            yield from batch.to_pylist()
        return
    return


def messages_text(messages: Any) -> str:
    if not isinstance(messages, list):
        return ""
    parts: list[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        value = message.get("content") or message.get("value")
        if isinstance(value, str):
            parts.append(value)
    return "\n".join(parts)


def add_issue(
    issues: list[dict[str, Any]],
    path: Path,
    row_index: int,
    issue: str,
    detail: Any = None,
) -> None:
    record = {"path": str(path), "row": row_index, "issue": issue}
    if detail is not None:
        record["detail"] = detail
    issues.append(record)


def print_summary(report: dict[str, Any], total_issues: int, json_out: Path) -> None:
    print(f"Audit JSON: {json_out}")
    print(f"Converted source issues: {total_issues}")
    print("\nConverted:")
    for name, summary in report["converted"].items():
        issue_count = len(report["issues"].get(name, []))
        print(
            f"  {name}: rows={summary.get('rows', 0)} examples={summary.get('examples', 0)} "
            f"tool_examples={summary.get('tool_call_examples', 0)} issues_shown={issue_count}"
        )
    print("\nUnconverted/tool-adjacent:")
    for name, summary in report["unconverted"].items():
        print(f"  {name}: {summary}")


if __name__ == "__main__":
    main()
