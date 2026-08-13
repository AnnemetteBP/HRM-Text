---
type: Plan Record
title: Epoch 5 Qualitative Smoke
description: 'Part of DFM8 Plan: Epoch 5 Qualitative Smoke.'
tags:
- dfm8
- data
- synthetic-data
- training
- evaluation
status: stable
last_updated: 2026-07-12
confidence: medium
part_of: /pages/dfm8-plan.md
---
# Epoch 5 Qualitative Smoke

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Update, 2026-07-09. Confidence: high for local prompt/output capture; medium
for qualitative interpretation.

Final DFM6-to-DFM7 `epoch_5` HF export:

```text
exports/dfm6_dfm7_XL_gas2_epoch_5_ema_hf_hrmenv_202253
```

was loaded through vLLM as `HrmTextForCausalLM` with the Gemma4 native chat
template, `enable_thinking=false`, temperature `0.0`, and FlashAttention 4.

Reusable script and report:

```text
scripts/smoke_dfm6_dfm7_epoch5_qualitative.py
docs/dfm6-dfm7-epoch5-smoke.md
logs/analysis/dfm6_dfm7_epoch5_smoke/generations.jsonl
docs/dfm6-dfm7-epoch5-extended-smoke.md
logs/analysis/dfm6_dfm7_epoch5_extended_smoke/generations.jsonl
```

Observed in the smoke set:

- Basic Danish explanatory chat worked.
- Simple Python code generation worked.
- Multi-turn memory worked for a short three-turn prompt.
- English and Danish summarization were grounded and followed one-/two-sentence
  requests in the tested examples; a requested 4-5 bullet summary instead came
  back as prose, so formatting compliance still needs work.
- Creative freeform generation was coherent but generic in English and better
  in Danish.
- Freeform math gave correct easy answers but did not emit final boxed answers.
- Tool calling showed native-looking syntax but repeated/malformed a call and
  mishandled a no-tool-needed greeting.
- Commonsense was weak in two tested cases: one leaked into `<think>` and did
  not answer; one gave implausible explanations for a wet sidewalk.

Next smoke battery, 2026-07-09. Confidence: medium from the first qualitative
smoke results.

The first smoke was useful but too small. Before finalizing DFM8 sampling,
run a broader targeted smoke battery on `epoch_5`, DFM5/DFM6 reference
checkpoints, and early DFM8 checkpoints:

1. Math contract:
   - easy GSM-style arithmetic with bare-answer, boxed-answer, and "show work"
     prompts;
   - MATH-style algebra/geometry where the final answer must be one
     `\boxed{...}`;
   - long reasoning prompts near the token limit to detect truncation;
   - MCQ math with "answer only A/B/C/D".
2. Tool calling:
   - one required call, no tool needed, wrong tool available, multi-call,
     call-then-use-tool-response, Danish tool prompts, and malformed/repeated
     call detection.
3. Thinking leakage:
   - direct commonsense, direct QA, and direct MCQ prompts with
     `enable_thinking=false`; flag any visible `<think>` as a contract failure.
4. Format following:
   - exact one sentence, exactly two sentences, 4-5 bullet points, JSON-only,
     table-only, and "do not add explanation".
5. Danish practical competence:
   - everyday Danish instructions, rewriting tone/register, spelling/grammar
     correction, and Danish cultural QA including SDU-Daisy-style questions.
6. Coding:
   - one simple function, one debugging task, one small algorithm, one code
     explanation, and one "do not execute, only explain" task.
7. Conversation:
   - five-to-eight turn memory, user correction, refusal-to-tool when no tool
     is needed, and language-switching between Danish and English.
8. Commonsense:
   - short causal prompts where the expected answer is obvious, plus
     multi-cause prompts where the model must not collapse to one cause.

DFM8 implications from the first smoke:

- Add explicit direct-answer/no-thinking SFT rows. The model can leak `<think>`
  even when the Gemma4 template disables thinking, so DFM8 should include
  direct-mode examples that answer plainly without a hidden/reasoning trace.
- Add strong format-following SFT rows for summaries, bullets, JSON, tables,
  exact sentence counts, final-answer-only, and one-boxed-answer math.
- Treat no-tool-needed examples as first-class tool training, not as incidental
  negatives. The model should learn that tools being available does not make a
  simple text answer impossible.
- Add repeated-tool-call loop checks to conversion audits and evals. A row that
  teaches or permits repeated identical calls should be excluded or capped.
- Add Danish commonsense/practical QA rows, not only cultural or encyclopedic
  Danish rows. The wet-sidewalk failure suggests a gap in ordinary causal
  reasoning or direct commonsense answer style.

Extended bilingual smoke, 2026-07-09. Confidence: high for local prompt/output
capture; medium for qualitative scoring heuristics.

The extended smoke is a strict superset of the initial smoke and contains 40
cases: 19 English, 20 Danish, and one bilingual language-switch case. It covers
chat, math, code, conversation, summarization, creative writing, format
following, tool calling, commonsense, and practical rewriting/correction.

Summary from `docs/dfm6-dfm7-epoch5-extended-smoke.md`:

```text
English: 12 pass, 6 weak, 1 bad
Danish:  18 pass, 2 weak, 0 bad
Both:     1 pass
```

Category summary:

```text
chat          2 pass
code          4 pass
conversation  3 pass
creative      2 pass
summarization 5 pass
format        3 pass, 1 weak
math          4 pass, 2 weak
practical     3 pass, 1 weak
tool_calling  3 pass, 3 weak
commonsense   2 pass, 1 weak, 1 bad
```

Notable asymmetries:

- Danish math followed the explicit boxed-answer instruction on two easy
  freeform prompts; English solved the content but omitted the boxed final
  answer. This suggests the format issue is prompt/language/style sensitive,
  not a uniform inability.
- Danish commonsense passed both smoke prompts; English leaked `<think>` on one
  prompt and gave implausible wet-sidewalk causes on another. DFM8 should not
  assume English common-sense/direct-answer behavior is already fixed by
  general English data.
- Danish JSON-only output failed by returning only `{`; English JSON-only
  passed. Structured-output formatting needs bilingual coverage.
- Tool calling remains weak in both languages for required calls: the model
  emits native-looking calls but repeats or malforms them. Danish no-tool-needed
  passed, while English no-tool-needed refused a simple greeting because a web
  search tool was present.
- English spelling/grammar correction leaked into a reasoning trace and did not
  provide the clean corrected sentence. Danish correction passed after heuristic
  correction.

DFM8 implications from the extended smoke:

1. Add bilingual direct-mode/no-thinking data, with English emphasized because
   the English smoke failures show more visible thinking leakage.
2. Add bilingual strict-format data for JSON-only, tables-only, exact sentence
   counts, bullet-only summaries, answer-only MCQ, and boxed math. Do not rely
   on one language transferring these contracts to the other.
3. Add bilingual spelling/grammar correction and practical rewriting data with
   targets that are clean final answers only.
4. Treat tool calling as a separate stabilized curriculum:
   - clean one-call examples,
   - no-tool-needed examples,
   - wrong-tool-available examples,
   - tool-response follow-up,
   - repeated-call loop negatives,
   - Danish and English variants.
5. Build small diagnostic evals from the smoke templates so early DFM8
   checkpoints can be checked before full benchmark runs.
