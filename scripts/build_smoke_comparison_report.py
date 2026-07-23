#!/usr/bin/env python3
"""Build a human-readable qualitative smoke comparison report."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from textwrap import shorten
from typing import Any


Outcome = str


CURRENT_MANUAL: dict[str, tuple[Outcome, str]] = {
    "basic_user_prompt_en": ("pass", "Correct, concise distinction between weather and climate."),
    "basic_user_prompt_da": ("pass", "Correct Danish explanation with appropriate 30-year framing."),
    "gsm_style_word_problem_en": ("pass", "Correct answer and now uses a boxed final answer."),
    "gsm_style_word_problem_da": ("pass", "Correct boxed answer, although terse."),
    "math_style_algebra_en": ("pass", "Correct boxed answer."),
    "math_style_algebra_da": ("bad", "Wrong final answer: it returns boxed 5 instead of 7."),
    "mcq_math_en": ("pass", "Correct one-letter answer."),
    "mcq_math_da": ("pass", "Correct one-letter answer."),
    "python_function_en": ("pass", "Valid function for English vowels with example."),
    "python_function_da": ("weak", "Valid Python shape, but Danish-vowel handling omits æ/ø/å."),
    "debug_python_en": ("pass", "Correctly fixes indentation."),
    "debug_python_da": ("pass", "Correctly fixes indentation."),
    "multi_turn_memory_en": ("pass", "Remembers Anna and Aarhus context; advice is usable."),
    "multi_turn_memory_da": ("weak", "Remembers Anna, but becomes verbose and includes questionable Aarhus facts."),
    "language_switch_en_da": ("pass", "Answers both language parts correctly, though verbosely."),
    "one_sentence_summary_en": ("pass", "Grounded and one sentence."),
    "two_sentence_summary_da": ("pass", "Grounded and exactly two sentences."),
    "one_sentence_summary_da": ("pass", "Grounded and one sentence."),
    "bullet_summary_en": ("pass", "Grounded 5-bullet summary."),
    "bullet_summary_da": ("pass", "Grounded 5-bullet summary."),
    "donald_duck_astronaut_en": ("weak", "On topic, but repetitive and bland."),
    "anders_and_astronaut_da": ("bad", "Severe repetition/looping; not a coherent story."),
    "json_only_en": ("pass", "Valid JSON-only output."),
    "json_only_da": ("pass", "Valid JSON-only output."),
    "table_only_en": ("weak", "Markdown table, but rows are colors rather than apples vs pears."),
    "table_only_da": ("weak", "Markdown table, but rows are colors rather than apples vs pears."),
    "single_weather_tool_en": ("weak", "Uses native tool-call syntax, but repeats/malforms the call."),
    "single_weather_tool_da": ("weak", "Uses native tool-call syntax, but repeats/malforms the call."),
    "no_tool_needed_en": ("weak", "Avoids tool use but fails the requested Danish greeting."),
    "no_tool_needed_da": ("pass", "Answers directly in English without tool use."),
    "wrong_tool_available_en": ("pass", "Answers directly and ignores irrelevant tool."),
    "wrong_tool_available_da": ("pass", "Answers directly and ignores irrelevant tool."),
    "glass_table_en": ("weak", "Likely outcome is present, but causal explanation is muddled."),
    "glass_table_da": ("weak", "Likely outcome is present, but causal explanation is muddled."),
    "wet_sidewalk_en": ("weak", "Rain and hose are plausible; fire is an odd third reason."),
    "wet_sidewalk_da": ("pass", "Three plausible explanations."),
    "rewrite_polite_email_en": ("pass", "Polite professional email."),
    "rewrite_polite_email_da": ("pass", "Polite professional Danish email."),
    "spelling_correction_en": ("pass", "Fixes the obvious errors."),
    "spelling_correction_da": ("pass", "Fixes the obvious errors."),
}


PREVIOUS_MANUAL: dict[str, tuple[Outcome, str]] = {
    "basic_user_prompt_en": ("pass", "Correct and concise."),
    "basic_user_prompt_da": ("pass", "Correct and concise."),
    "gsm_style_word_problem_en": ("weak", "Correct content, but no boxed final answer."),
    "gsm_style_word_problem_da": ("pass", "Correct boxed answer."),
    "math_style_algebra_en": ("weak", "Correct content, but no boxed final answer."),
    "math_style_algebra_da": ("pass", "Correct boxed answer."),
    "mcq_math_en": ("pass", "Correct one-letter answer."),
    "mcq_math_da": ("pass", "Correct one-letter answer."),
    "python_function_en": ("pass", "Valid function shape."),
    "python_function_da": ("weak", "Valid function shape, but Danish-vowel handling was incomplete."),
    "debug_python_en": ("pass", "Correctly fixed indentation."),
    "debug_python_da": ("pass", "Correctly fixed indentation."),
    "multi_turn_memory_en": ("pass", "Remembered name and trip context."),
    "multi_turn_memory_da": ("pass", "Remembered name and trip context."),
    "language_switch_en_da": ("pass", "Answered both languages."),
    "one_sentence_summary_en": ("pass", "Grounded summary."),
    "two_sentence_summary_da": ("pass", "Grounded summary."),
    "one_sentence_summary_da": ("pass", "Grounded summary."),
    "bullet_summary_en": ("pass", "Grounded bullet summary."),
    "bullet_summary_da": ("pass", "Grounded bullet summary."),
    "donald_duck_astronaut_en": ("weak", "On topic but generic."),
    "anders_and_astronaut_da": ("pass", "Coherent and more vivid than the new answer."),
    "json_only_en": ("pass", "Valid JSON-only output."),
    "json_only_da": ("weak", "Not valid JSON-only output."),
    "table_only_en": ("weak", "Markdown table, but comparison structure was imperfect."),
    "table_only_da": ("weak", "Markdown table, but comparison structure was imperfect."),
    "single_weather_tool_en": ("weak", "Repeated/malformed tool call."),
    "single_weather_tool_da": ("weak", "Mixed repeated tool call with a fabricated answer."),
    "no_tool_needed_en": ("bad", "Refused a simple greeting due to tool confusion."),
    "no_tool_needed_da": ("pass", "Answered directly without tool use."),
    "wrong_tool_available_en": ("pass", "Answered directly."),
    "wrong_tool_available_da": ("pass", "Answered directly."),
    "glass_table_en": ("bad", "Leaked a thinking trace and did not finish cleanly."),
    "glass_table_da": ("pass", "Plausible physical outcome and explanation."),
    "wet_sidewalk_en": ("bad", "Missed ordinary explanations."),
    "wet_sidewalk_da": ("pass", "Plausible explanations."),
    "rewrite_polite_email_en": ("pass", "Polite professional rewrite."),
    "rewrite_polite_email_da": ("pass", "Polite professional rewrite."),
    "spelling_correction_en": ("weak", "Left obvious errors."),
    "spelling_correction_da": ("pass", "Fixed obvious errors."),
}


ORDER = {"bad": 0, "weak": 1, "pass": 2, "manual": 1}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def outcome_delta(previous: Outcome, current: Outcome) -> str:
    diff = ORDER[current] - ORDER[previous]
    if diff > 0:
        return "improved"
    if diff < 0:
        return "regressed"
    return "same"


def count_by(rows: list[dict[str, Any]], manual: dict[str, tuple[Outcome, str]], key: str) -> dict[str, Counter[str]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        outcome = manual.get(row["name"], ("manual", ""))[0]
        grouped[row[key]][outcome] += 1
    return grouped


def summary_table(title: str, grouped: dict[str, Counter[str]]) -> list[str]:
    lines = [f"## {title}", "", "| Group | Pass | Weak | Bad | Manual |", "| --- | ---: | ---: | ---: | ---: |"]
    for group in sorted(grouped):
        counts = grouped[group]
        lines.append(f"| {group} | {counts['pass']} | {counts['weak']} | {counts['bad']} | {counts['manual']} |")
    lines.append("")
    return lines


def fenced(text: str) -> list[str]:
    return ["```text", text.strip(), "```"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous-jsonl", type=Path, required=True)
    parser.add_argument("--current-jsonl", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--previous-label", default="DFM6-DFM7 epoch_5 EMA")
    parser.add_argument("--current-label", default="DFM8 XL step_1350000 EMA")
    parser.add_argument("--current-export", default="exports/dfm8_XL_step1350000_ema_hf")
    args = parser.parse_args()

    previous_rows = {row["name"]: row for row in load_jsonl(args.previous_jsonl)}
    current_rows = load_jsonl(args.current_jsonl)

    current_counts = Counter(CURRENT_MANUAL[row["name"]][0] for row in current_rows)
    previous_counts = Counter(PREVIOUS_MANUAL[row["name"]][0] for row in current_rows)
    delta_counts = Counter(
        outcome_delta(PREVIOUS_MANUAL[row["name"]][0], CURRENT_MANUAL[row["name"]][0])
        for row in current_rows
    )

    lines: list[str] = [
        "# DFM8 XL Step 1350K Qualitative Smoke Test",
        "",
        "Last updated: 2026-07-16",
        "Confidence: high for prompts/outputs captured locally; medium for qualitative assessments.",
        "",
        f"Current model/export: `{args.current_export}`",
        f"Previous comparison point: `{args.previous_label}`",
        "",
        "Generation settings: Gemma4 native chat template, `enable_thinking=false`, temperature 0.0, vLLM with FlashAttention 4.",
        "",
        "This is a qualitative smoke test, not a benchmark. `Pass` means the response broadly satisfied the prompt contract; `weak` means it showed the relevant capability but broke an important contract or had notable quality issues; `bad` means it missed the task in an obvious way.",
        "",
        "## Global Assessment",
        "",
        f"Absolute result for `{args.current_label}`: **{current_counts['pass']} pass, {current_counts['weak']} weak, {current_counts['bad']} bad** over {len(current_rows)} prompts.",
        "",
        f"Previous result under the same stricter manual pass: **{previous_counts['pass']} pass, {previous_counts['weak']} weak, {previous_counts['bad']} bad**.",
        "",
        f"Relative movement: **{delta_counts['improved']} improved, {delta_counts['same']} unchanged, {delta_counts['regressed']} regressed**.",
        "",
        "Bottom line: the 1350K checkpoint is better at explicit boxed-answer and simple format contracts than the previous smoke point, and it fixes several simple refusal/tool-confusion cases. It is still weak on native tool-call termination, has one serious Danish algebra error, and shows worse repetition in creative generation. In absolute terms it is usable for basic chat, code, summarization, simple formatting, and many direct instructions; it is not yet reliable for tool calling, robust commonsense, or long free-form generation quality.",
        "",
    ]
    lines.extend(summary_table("Current Summary By Language", count_by(current_rows, CURRENT_MANUAL, "language")))
    lines.extend(summary_table("Current Summary By Category", count_by(current_rows, CURRENT_MANUAL, "category")))
    lines.extend([
        "## One-By-One Comparison",
        "",
        "| Category | Prompt | Lang | 1350K | Previous | Relative | Short assessment |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ])
    for row in current_rows:
        prev_outcome, _prev_note = PREVIOUS_MANUAL[row["name"]]
        cur_outcome, cur_note = CURRENT_MANUAL[row["name"]]
        lines.append(
            f"| {row['category']} | `{row['name']}` | {row['language']} | {cur_outcome} | {prev_outcome} | "
            f"{outcome_delta(prev_outcome, cur_outcome)} | {cur_note} |"
        )
    lines.append("")

    for row in current_rows:
        prev = previous_rows[row["name"]]
        prev_outcome, prev_note = PREVIOUS_MANUAL[row["name"]]
        cur_outcome, cur_note = CURRENT_MANUAL[row["name"]]
        lines.extend([
            f"## {row['category']}: {row['name']} ({row['language']})",
            "",
            f"Absolute: **{cur_outcome}**. {cur_note}",
            f"Relative to previous: **{outcome_delta(prev_outcome, cur_outcome)}**; previous was **{prev_outcome}**. {prev_note}",
            "",
            "Prompt/messages:",
            "",
            "```json",
            json.dumps(row["messages"], ensure_ascii=False, indent=2),
            "```",
            "",
        ])
        if row.get("tools"):
            lines.extend([
                "Tools:",
                "",
                "```json",
                json.dumps(row["tools"], ensure_ascii=False, indent=2),
                "```",
                "",
            ])
        lines.extend([
            "1350K answer:",
            "",
            *fenced(row["answer"]),
            "",
            "Previous answer excerpt:",
            "",
            *fenced(shorten(prev["answer"].replace("\n", " "), width=700, placeholder=" ...")),
            "",
        ])

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output_md}")


if __name__ == "__main__":
    main()
