---
type: Plan Record
title: Direct Vs CoT
description: 'Part of DFM7 Plan: Direct Vs CoT.'
tags:
- dfm7
- data
- training
- evaluation
status: stable
last_updated: 2026-07-02
confidence: medium
part_of: /pages/dfm7-plan.md
---
# Direct Vs CoT

Part of [DFM7 Plan](/pages/dfm7-plan.md).

Direct-vs-CoT prompt contract for DFM7 math, 2026-06-30.
Confidence: medium until implemented and smoke-tested. DFM7 should keep
`direct` and `cot` as useful data/eval modes, but they must be visible in the
Gemma-rendered prompt. Treat them as prompt contracts, not hidden metadata.

Policy:

- `direct` math means: answer without reasoning and return only the final answer
  in a strict machine-checkable format. For freeform math, prefer
  `\boxed{...}` even for GSM-style problems because GSM8K scoring accepts boxed
  integers and MATH requires boxed answers.
- `cot` math means: reasoning is allowed or requested, but the completion must
  still end with exactly one final `\boxed{...}` answer.
- `direct` must not mean "short but arbitrary"; `cot` must not mean "long
  unconstrained prose." Both modes need an explicit final-answer contract.
- One-letter MCQ math remains a separate direct-answer contract: return exactly
  one of the option letters. It should not share freeform boxed math prompts.

Implementation suggestion:

- In `scripts/tokenize_chat_template.py::hrm_row_to_messages()` or in a
  DFM-specific pre-conversion layer, turn math `condition` values into short
  system/user instructions before rendering with the Gemma chat template.
- For `direct` freeform math rows, prepend an instruction equivalent to:
  `Return only the final answer in \boxed{...}.`
- For `cot`/`synth,cot` freeform math rows, prepend an instruction equivalent
  to: `Solve step by step. End with exactly one final answer in \boxed{...}.`
- For MCQ rows, use a different instruction equivalent to:
  `Return exactly one option letter.`

Evaluation policy:

- Keep the current HRM/card-comparable standard eval path unchanged unless we
  intentionally create a new metric namespace.
- Add any explicit DFM-native math prompt variants under a separate eval prefix
  or task name, so improvements from clearer prompting are not confused with
  card-comparable HRM standard scores.
