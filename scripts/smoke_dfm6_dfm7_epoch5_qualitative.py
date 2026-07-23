#!/usr/bin/env python3
"""Qualitative smoke prompts for the final DFM6->DFM7 epoch_5 HF export."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jinja2
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams


@dataclass(frozen=True)
class SmokeCase:
    category: str
    name: str
    language: str
    messages: list[dict[str, str]]
    max_tokens: int = 256
    tools: list[dict[str, Any]] | None = None


def default_cases() -> list[SmokeCase]:
    source_text_en = (
        "Photosynthesis is the process by which green plants, algae, and some bacteria convert light energy "
        "into chemical energy. In plants, this mainly happens in chloroplasts, where chlorophyll absorbs "
        "sunlight. Carbon dioxide from the air and water from the roots are transformed into glucose and "
        "oxygen. The glucose can be used immediately for energy or stored for later growth, while oxygen is "
        "released into the atmosphere. Photosynthesis is one reason Earth's atmosphere contains enough oxygen "
        "for animals and humans to breathe."
    )
    source_text_da = (
        "Nordjylland har i de seneste år arbejdet med både grøn energi, kystbeskyttelse og nye uddannelser. "
        "Kommunerne forsøger at tiltrække unge familier, samtidig med at mange mindre byer kæmper med faldende "
        "befolkningstal. Lokale virksomheder peger på, at bedre transportforbindelser og adgang til kvalificeret "
        "arbejdskraft er afgørende for udviklingen."
    )
    weather_tool_en = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a city.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"},
                        "country": {"type": "string", "description": "Country name"},
                    },
                    "required": ["city"],
                },
            },
        }
    ]
    weather_tool_da = [
        {
            "type": "function",
            "function": {
                "name": "hent_vejr",
                "description": "Hent aktuelt vejr for en by.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "by": {"type": "string", "description": "Bynavn"},
                        "land": {"type": "string", "description": "Landenavn"},
                    },
                    "required": ["by"],
                },
            },
        }
    ]
    search_tool_en = [
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the web for current information.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "Search query"}},
                    "required": ["query"],
                },
            },
        }
    ]
    search_tool_da = [
        {
            "type": "function",
            "function": {
                "name": "soeg_web",
                "description": "Søg på nettet efter aktuel information.",
                "parameters": {
                    "type": "object",
                    "properties": {"forespoergsel": {"type": "string", "description": "Søgetekst"}},
                    "required": ["forespoergsel"],
                },
            },
        }
    ]
    return [
        SmokeCase(
            "chat",
            "basic_user_prompt_en",
            "en",
            [{"role": "user", "content": "Give a short helpful answer: what is the difference between climate and weather?"}],
            192,
        ),
        SmokeCase(
            "chat",
            "basic_user_prompt_da",
            "da",
            [{"role": "user", "content": "Skriv et kort og hjælpsomt svar på dansk: Hvad er forskellen på klima og vejr?"}],
            192,
        ),
        SmokeCase(
            "math",
            "gsm_style_word_problem_en",
            "en",
            [{"role": "user", "content": "Solve step by step and finish with exactly one final boxed answer: A class has 24 students. Three eighths of them bike to school. How many students bike to school?"}],
            256,
        ),
        SmokeCase(
            "math",
            "gsm_style_word_problem_da",
            "da",
            [{"role": "user", "content": "Løs opgaven trin for trin og afslut med præcis ét endeligt svar i \\boxed{...}: En klasse har 24 elever. Tre ottendedele cykler i skole. Hvor mange elever cykler i skole?"}],
            256,
        ),
        SmokeCase(
            "math",
            "math_style_algebra_en",
            "en",
            [{"role": "user", "content": "Solve the equation and finish with exactly one final boxed answer: 3(x - 2) + 4 = 19."}],
            256,
        ),
        SmokeCase(
            "math",
            "math_style_algebra_da",
            "da",
            [{"role": "user", "content": "Løs ligningen og afslut med præcis ét endeligt svar i \\boxed{...}: 3(x - 2) + 4 = 19."}],
            256,
        ),
        SmokeCase(
            "math",
            "mcq_math_en",
            "en",
            [{"role": "user", "content": "Answer only A, B, C, or D. What is 7 * 8? A) 54 B) 56 C) 58 D) 64"}],
            32,
        ),
        SmokeCase(
            "math",
            "mcq_math_da",
            "da",
            [{"role": "user", "content": "Svar kun med A, B, C eller D. Hvad er 7 * 8? A) 54 B) 56 C) 58 D) 64"}],
            32,
        ),
        SmokeCase(
            "code",
            "python_function_en",
            "en",
            [{"role": "user", "content": "Write a Python function `count_vowels(text)` that returns the number of vowels in a string. Include a short example."}],
            320,
        ),
        SmokeCase(
            "code",
            "python_function_da",
            "da",
            [{"role": "user", "content": "Skriv en Python-funktion `count_vowels(text)`, der returnerer antallet af vokaler i en tekststreng. Medtag et kort eksempel."}],
            320,
        ),
        SmokeCase(
            "code",
            "debug_python_en",
            "en",
            [{"role": "user", "content": "Find and fix the bug. Return only corrected Python code.\n\n```python\ndef add_numbers(nums):\n    total = 0\n    for n in nums:\n    total += n\n    return total\n```"}],
            256,
        ),
        SmokeCase(
            "code",
            "debug_python_da",
            "da",
            [{"role": "user", "content": "Find og ret fejlen. Returner kun rettet Python-kode.\n\n```python\ndef add_numbers(nums):\n    total = 0\n    for n in nums:\n    total += n\n    return total\n```"}],
            256,
        ),
        SmokeCase(
            "conversation",
            "multi_turn_memory_en",
            "en",
            [
                {"role": "user", "content": "My name is Anna. I am planning a weekend trip to Aarhus."},
                {"role": "assistant", "content": "That sounds nice. What kind of activities do you enjoy?"},
                {"role": "user", "content": "I like museums and quiet cafes. What did I say my name was, and what should I do first?"},
            ],
            256,
        ),
        SmokeCase(
            "conversation",
            "multi_turn_memory_da",
            "da",
            [
                {"role": "user", "content": "Jeg hedder Anna. Jeg planlægger en weekendtur til Aarhus."},
                {"role": "assistant", "content": "Det lyder hyggeligt. Hvilke aktiviteter kan du lide?"},
                {"role": "user", "content": "Jeg kan lide museer og rolige caféer. Hvad sagde jeg, at jeg hed, og hvad bør jeg gøre først?"},
            ],
            256,
        ),
        SmokeCase(
            "conversation",
            "language_switch_en_da",
            "both",
            [
                {"role": "user", "content": "Answer my first question in English and the second in Danish. First: what is a library? Second: hvad er et bibliotek?"},
            ],
            256,
        ),
        SmokeCase(
            "summarization",
            "one_sentence_summary_en",
            "en",
            [{"role": "user", "content": f"Summarize the following text in exactly one sentence:\n\n{source_text_en}"}],
            160,
        ),
        SmokeCase(
            "summarization",
            "two_sentence_summary_da",
            "da",
            [{"role": "user", "content": f"Opsummer denne tekst på dansk i præcis to sætninger:\n\n{source_text_da}"}],
            192,
        ),
        SmokeCase(
            "summarization",
            "one_sentence_summary_da",
            "da",
            [{"role": "user", "content": f"Opsummer denne tekst på dansk i præcis én sætning:\n\n{source_text_da}"}],
            192,
        ),
        SmokeCase(
            "summarization",
            "bullet_summary_en",
            "en",
            [{"role": "user", "content": f"Write a longer, more detailed summary of this text in 4-5 bullet points. Use bullet points only:\n\n{source_text_en}"}],
            320,
        ),
        SmokeCase(
            "summarization",
            "bullet_summary_da",
            "da",
            [{"role": "user", "content": f"Skriv en længere og mere detaljeret opsummering af teksten i 4-5 punkttegn. Brug kun punkttegn:\n\n{source_text_da}"}],
            320,
        ),
        SmokeCase(
            "creative",
            "donald_duck_astronaut_en",
            "en",
            [{"role": "user", "content": "Write a short free-form story paragraph about Donald Duck's adventures as an astronaut. Keep it playful but coherent."}],
            256,
        ),
        SmokeCase(
            "creative",
            "anders_and_astronaut_da",
            "da",
            [{"role": "user", "content": "Skriv et kort, frit afsnit på dansk om Anders And som astronaut. Det skal være fantasifuldt, men sammenhængende."}],
            256,
        ),
        SmokeCase(
            "format",
            "json_only_en",
            "en",
            [{"role": "user", "content": "Return only valid JSON with keys `animal`, `sound`, and `legs` for a cat. Do not add explanation."}],
            128,
        ),
        SmokeCase(
            "format",
            "json_only_da",
            "da",
            [{"role": "user", "content": "Returner kun gyldig JSON med nøglerne `dyr`, `lyd` og `ben` for en kat. Tilføj ingen forklaring."}],
            128,
        ),
        SmokeCase(
            "format",
            "table_only_en",
            "en",
            [{"role": "user", "content": "Return only a Markdown table with two rows comparing apples and pears on color and typical use."}],
            192,
        ),
        SmokeCase(
            "format",
            "table_only_da",
            "da",
            [{"role": "user", "content": "Returner kun en Markdown-tabel med to rækker, der sammenligner æbler og pærer på farve og typisk brug."}],
            192,
        ),
        SmokeCase(
            "tool_calling",
            "single_weather_tool_en",
            "en",
            [{"role": "user", "content": "What is the weather in Copenhagen right now? Use the available tool."}],
            160,
            tools=weather_tool_en,
        ),
        SmokeCase(
            "tool_calling",
            "single_weather_tool_da",
            "da",
            [{"role": "user", "content": "Hvordan er vejret i København lige nu? Brug det tilgængelige værktøj."}],
            160,
            tools=weather_tool_da,
        ),
        SmokeCase(
            "tool_calling",
            "no_tool_needed_en",
            "en",
            [{"role": "user", "content": "Say hello in Danish. Do not use a tool unless it is necessary."}],
            80,
            tools=search_tool_en,
        ),
        SmokeCase(
            "tool_calling",
            "no_tool_needed_da",
            "da",
            [{"role": "user", "content": "Sig hej på engelsk. Brug ikke et værktøj, medmindre det er nødvendigt."}],
            80,
            tools=search_tool_da,
        ),
        SmokeCase(
            "tool_calling",
            "wrong_tool_available_en",
            "en",
            [{"role": "user", "content": "What is 12 plus 5? Answer directly. Do not use the web search tool."}],
            96,
            tools=search_tool_en,
        ),
        SmokeCase(
            "tool_calling",
            "wrong_tool_available_da",
            "da",
            [{"role": "user", "content": "Hvad er 12 plus 5? Svar direkte. Brug ikke websøgningsværktøjet."}],
            96,
            tools=search_tool_da,
        ),
        SmokeCase(
            "commonsense",
            "glass_table_en",
            "en",
            [{"role": "user", "content": "A glass is on the edge of a table. Someone bumps the table hard. What is likely to happen, and why?"}],
            160,
        ),
        SmokeCase(
            "commonsense",
            "glass_table_da",
            "da",
            [{"role": "user", "content": "Et glas står på kanten af et bord. Nogen støder hårdt ind i bordet. Hvad sker der sandsynligvis, og hvorfor?"}],
            160,
        ),
        SmokeCase(
            "commonsense",
            "wet_sidewalk_en",
            "en",
            [{"role": "user", "content": "If the sidewalk is wet in the morning, list three plausible reasons. Do not assume only one cause."}],
            192,
        ),
        SmokeCase(
            "commonsense",
            "wet_sidewalk_da",
            "da",
            [{"role": "user", "content": "Hvis fortovet er vådt om morgenen, så nævn tre plausible grunde. Antag ikke kun én årsag."}],
            192,
        ),
        SmokeCase(
            "practical",
            "rewrite_polite_email_en",
            "en",
            [{"role": "user", "content": "Rewrite this as a polite professional email in English:\n\nsend me the report today because I need it"}],
            220,
        ),
        SmokeCase(
            "practical",
            "rewrite_polite_email_da",
            "da",
            [{"role": "user", "content": "Omskriv dette til en høflig professionel e-mail på dansk:\n\nsend mig rapporten i dag fordi jeg skal bruge den"}],
            220,
        ),
        SmokeCase(
            "practical",
            "spelling_correction_en",
            "en",
            [{"role": "user", "content": "Correct the spelling and grammar only: The wether are bad but we goes anyway."}],
            128,
        ),
        SmokeCase(
            "practical",
            "spelling_correction_da",
            "da",
            [{"role": "user", "content": "Ret kun stavning og grammatik: Jeg syndes vejret er dårligt men vi gå alligevel."}],
            128,
        ),
    ]


def render_prompt(
    template: jinja2.Template,
    tokenizer: Any,
    messages: list[dict[str, str]],
    tools: list[dict[str, Any]] | None,
) -> str:
    return template.render(
        messages=messages,
        tools=tools,
        add_generation_prompt=True,
        enable_thinking=False,
        bos_token=tokenizer.bos_token or "",
        eos_token=tokenizer.eos_token or "",
    )


def assess(case: SmokeCase, output: str) -> str:
    text = output.strip()
    lower = text.lower()
    if not text:
        return "bad: empty output."
    if case.category == "chat":
        if ("weather" in lower and "climate" in lower) or ("vejr" in lower and "klima" in lower):
            return "reasonable: gives a short correct explanation."
        return "weak: does not clearly answer the basic explanatory prompt."
    if case.category == "math":
        if case.name.startswith("mcq_math"):
            compact = re.sub(r"[^A-Da-d]", "", text)
            if compact[:1].upper() == "B" and len(compact) <= 2:
                return "good: follows one-letter MCQ contract and selects B."
            if "56" in text:
                return "weak: content appears correct but violates one-letter MCQ contract."
            return "bad: misses the simple MCQ math answer."
        if "\\boxed{" in text:
            return "good format: includes boxed final answer."
        return "weak format: no boxed final answer despite explicit instruction."
    if case.category == "code":
        if "python_function" in case.name:
            return (
                "reasonable: contains a Python function and vowel logic." if "def " in text and ("vowel" in lower or "vokal" in lower)
                else "weak: does not clearly provide the requested Python function."
            )
        if "debug_python" in case.name:
            if "total += n" in text and re.search(r"^\s+total \+= n", text, re.MULTILINE):
                return "reasonable: fixes the indentation bug."
            return "weak: does not clearly return corrected code for the indentation bug."
    if case.category == "conversation":
        if "language_switch" in case.name:
            has_english = "library" in lower
            has_danish = "bibliotek" in lower
            return (
                "reasonable: answers both language parts." if has_english and has_danish
                else "weak: misses one side of the requested language switch."
            )
        return (
            "reasonable: remembers the user name and responds to the trip context." if "anna" in lower and ("aarhus" in lower or "museum" in lower or "cafe" in lower or "café" in lower)
            else "weak: misses either the remembered name or the trip context."
        )
    if case.category == "tool_calling":
        has_call = "call:" in text or "<|tool_call" in text or "tool_call" in lower
        if case.name.startswith("single_weather_tool"):
            expected_tool = "hent_vejr" if case.language == "da" else "get_weather"
            repeated = text.count(f"call:{expected_tool}") > 1
            return (
                f"weak: emits a native {expected_tool} call but repeats/malforms it instead of one clean call." if has_call and repeated
                else f"reasonable format: appears to emit one native {expected_tool} tool call." if has_call and expected_tool in text
                else f"weak: does not clearly emit the requested {expected_tool} tool call."
            )
        if case.name.startswith("no_tool_needed"):
            return (
                "reasonable: answers directly without an unnecessary tool call." if not has_call and ("hej" in lower or "hello" in lower) and "can't" not in lower and "kan ikke" not in lower
                else "weak: avoids the tool but refuses/fails a simple greeting."
            )
        if case.name.startswith("wrong_tool_available"):
            if has_call:
                return "weak: used a tool even though the prompt required a direct answer."
            if "17" in text:
                return "reasonable: answers directly and ignores the irrelevant tool."
            return "bad: neither uses the right direct answer nor appropriate tool behavior."
    if case.category == "summarization":
        if "bullet" in case.name:
            bullet_lines = [line for line in text.splitlines() if line.lstrip().startswith(("-", "*", "•"))]
            return (
                "reasonable: uses bullet points and stays grounded." if 4 <= len(bullet_lines) <= 5
                else "weak format: summary may be grounded but does not satisfy the 4-5 bullet-only contract."
            )
        return "reasonable if concise and grounded in the supplied text; check exact sentence-count compliance manually."
    if case.category == "creative":
        return "reasonable if coherent, playful, and on topic; check copyright/style issues manually."
    if case.category == "format":
        if "json_only" in case.name:
            try:
                json.loads(text)
            except json.JSONDecodeError:
                return "weak: not valid JSON-only output."
            return "reasonable: valid JSON-only output."
        if "table_only" in case.name:
            return (
                "reasonable: returns a Markdown table." if "|" in text and "---" in text
                else "weak: does not clearly return only a Markdown table."
            )
    if case.category == "commonsense":
        if "<think>" in lower:
            return "weak: leaked/entered a thinking trace and did not produce a final answer."
        if case.name.startswith("wet_sidewalk") and not re.search(r"\b(rain|sprinkler|dew|clean|washed|regn|dug|regnvejr|vasket|rengjort)\b", lower):
            return "bad: listed implausible causes and missed ordinary explanations such as rain, dew, or cleaning."
        if case.name.startswith("glass_table") and not re.search(r"\b(fall|falls|slide|break|tip|vælte|falde|glide|gå i stykker)\b", lower):
            return "weak: does not clearly state the likely physical outcome."
        return "reasonable if it gives plausible causal reasoning without overclaiming."
    if case.category == "practical":
        if "rewrite_polite_email" in case.name:
            polite_markers = ("please", "could", "thank", "venlig", "tak", "vil du", "kunne")
            return (
                "reasonable: rewrites into a polite professional request." if any(marker in lower for marker in polite_markers)
                else "weak: does not clearly make the request polite/professional."
            )
        if "spelling_correction" in case.name:
            bad_patterns = (
                r"\bwether\b",
                r"\bare bad\b",
                r"\bwe goes\b",
                r"\bsyndes\b",
                r"\bvi gå\b",
            )
            return (
                "reasonable: fixes the obvious spelling/grammar errors." if not any(re.search(pattern, lower) for pattern in bad_patterns)
                else "weak: leaves obvious spelling/grammar errors."
            )
    return "manual review needed."


def outcome_label(assessment: str) -> str:
    if assessment.startswith(("good", "reasonable")):
        return "pass"
    if assessment.startswith("weak"):
        return "weak"
    if assessment.startswith("bad"):
        return "bad"
    return "manual"


def write_markdown(path: Path, model: str, rows: list[dict[str, Any]]) -> None:
    by_language: dict[str, dict[str, int]] = {}
    by_category: dict[str, dict[str, int]] = {}
    for row in rows:
        outcome = outcome_label(row["assessment"])
        by_language.setdefault(row["language"], {"pass": 0, "weak": 0, "bad": 0, "manual": 0})[outcome] += 1
        by_category.setdefault(row["category"], {"pass": 0, "weak": 0, "bad": 0, "manual": 0})[outcome] += 1

    def table(title: str, data: dict[str, dict[str, int]]) -> list[str]:
        lines = [f"## {title}", "", "| Group | Pass | Weak | Bad | Manual |", "| --- | ---: | ---: | ---: | ---: |"]
        for key in sorted(data):
            counts = data[key]
            lines.append(
                f"| {key} | {counts.get('pass', 0)} | {counts.get('weak', 0)} | {counts.get('bad', 0)} | {counts.get('manual', 0)} |"
            )
        lines.append("")
        return lines

    lines = [
        "# DFM6-DFM7 Epoch 5 Qualitative Smoke Test",
        "",
        "Last updated: 2026-07-09",
        "Confidence: high for prompts/outputs captured locally; medium for qualitative assessments.",
        "",
        f"Model/export: `{model}`",
        "",
        "Generation settings: Gemma4 native chat template, `enable_thinking=false`, temperature 0.0.",
        "",
        "This is a qualitative smoke test, not a benchmark. `Pass` means the response broadly satisfied the local prompt contract; `weak` means it showed capability but broke an important contract; `bad` means it missed the task in an obvious way.",
        "",
    ]
    lines.extend(table("Summary By Language", by_language))
    lines.extend(table("Summary By Category", by_category))
    for row in rows:
        lines.extend([
            f"## {row['category']}: {row['name']} ({row['language']})",
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
            "Answer:",
            "",
            "```text",
            row["answer"].strip(),
            "```",
            "",
            f"Assessment: {row['assessment']}",
            "",
        ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="exports/dfm6_dfm7_XL_gas2_epoch_5_ema_hf_hrmenv_202253")
    parser.add_argument("--chat-template", default="evaluation/chat_templates/gemma4_native_chat.jinja")
    parser.add_argument("--output-jsonl", default="logs/analysis/dfm6_dfm7_epoch5_smoke/generations.jsonl")
    parser.add_argument("--output-md", default="docs/dfm6-dfm7-epoch5-smoke.md")
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.20)
    parser.add_argument("--max-model-len", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=1)
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    template = jinja2.Environment().from_string(Path(args.chat_template).read_text(encoding="utf-8"))
    cases = default_cases()
    prompts = [render_prompt(template, tokenizer, case.messages, case.tools) for case in cases]

    llm = LLM(
        model=args.model,
        dtype="bfloat16",
        max_model_len=args.max_model_len,
        gpu_memory_utilization=args.gpu_memory_utilization,
        enforce_eager=True,
        trust_remote_code=False,
        attention_backend="FLASH_ATTN",
    )

    rows: list[dict[str, Any]] = []
    for start in range(0, len(cases), max(1, args.batch_size)):
        batch_cases = cases[start:start + max(1, args.batch_size)]
        batch_prompts = prompts[start:start + max(1, args.batch_size)]
        max_tokens = max(case.max_tokens for case in batch_cases)
        outputs = llm.generate(
            batch_prompts,
            SamplingParams(
                temperature=0.0,
                max_tokens=max_tokens,
                stop_token_ids=[tokenizer.eos_token_id] if tokenizer.eos_token_id is not None else None,
                skip_special_tokens=True,
            ),
        )
        for case, out in zip(batch_cases, outputs, strict=True):
            answer = out.outputs[0].text
            rows.append(
                {
                    "category": case.category,
                    "name": case.name,
                    "language": case.language,
                    "messages": case.messages,
                    "tools": case.tools,
                    "max_tokens": max_tokens,
                    "answer": answer,
                    "assessment": assess(case, answer),
                }
            )

    out_jsonl = Path(args.output_jsonl)
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    write_markdown(Path(args.output_md), args.model, rows)
    print(f"Wrote {out_jsonl}")
    print(f"Wrote {args.output_md}")


if __name__ == "__main__":
    main()
