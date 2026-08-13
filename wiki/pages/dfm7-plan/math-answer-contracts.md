---
type: Plan Record
title: Math Answer Contracts
description: 'Part of DFM7 Plan: Math Answer Contracts.'
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
# Math Answer Contracts

Part of [DFM7 Plan](/pages/dfm7-plan.md).

DFM7 math data/eval contract investigation, 2026-06-30.
Confidence: high from local inspection of `evaluation/benchmarks.py`,
`evaluation/config/dfm6_vllm_benchmarking.yaml`,
`scripts/tokenize_chat_template.py`, DFM6 tokenized arrays, and source Parquet
schemas. Math has related but less severe format issues than BFCL tool calling.

Verified facts:

- Standard eval uses three different math-ish contracts:
  - `GSM8k`: raw question, `condition=direct`, `max_tokens=512`; scorer accepts
    a bare final integer or a boxed final integer.
  - `MATH`: raw problem, default `condition=synth,cot`, `max_tokens=3072`;
    scorer requires a parseable last `\boxed{...}` via `last_boxed_only_string`.
  - MMLU math subjects: few-shot multiple choice, `condition=direct`,
    `max_tokens=1`; scorer expects exactly one option letter.
- DFM6 vLLM standard eval wraps these prompts with the Gemma chat template and
  `enable_thinking=False`. The older HRM/Sapient eval path used HRM condition
  marker tokens rather than Gemma chat rendering.
- DFM6 contains many math sources with inconsistent answer styles:
  `openmathinstruct2__cot` teaches long `<think>...</think>` plus final natural
  language/boxed answers; `openmathinstruct2__direct` teaches direct expected
  answers for non-original sources; `math_train.jsonl` has both full solutions
  and direct boxed answers; `gsm8k_train.jsonl` direct rows teach bare numeric
  answers; FLAN GSM8K/MathQA, DMMath, AMPS Mathematica, Tulu math, and other
  reasoning sources use still other answer conventions.
- Prior DFM6 step-500000 probes showed MATH invalids often come from long
  reasoning that fails to terminate with a boxed answer under the token cap, and
  MMLU math invalids often start with `<think>` or `\boxed{...}` instead of the
  required single letter.
- Two intended DFM6 AllenAI RLVR math sources currently contribute zero
  tokenized rows:
  `data/tokenized_dfm6/allenai_rlvr_gsm__data__train-00000-of-00001.parquet`
  and
  `data/tokenized_dfm6/allenai_rlvr_math__data__train-00000-of-00001.parquet`
  have `tokens.npy` shape `(0,)` and empty index arrays. Their source Parquet
  files contain one-message `messages=[{"role": "user", ...}]` rows with a
  separate `ground_truth` column, not assistant messages. The chat-template
  tokenizer only emits supervised examples when it sees an assistant message
  with content or tool calls, and it also rejects examples with no prompt
  history.

Interpretation:

- This is not as binary as the BFCL parser mismatch. The MATH scorer can handle
  many normal CoT solutions if the model eventually emits `\boxed{...}`, and
  GSM8K can handle bare numeric answers. But DFM6 teaches several competing
  math response styles while the evals demand task-specific output contracts.
- The zero-row RLVR GSM/MATH bug is more concrete than a format preference. It
  means two sources intended to strengthen GSM8K/MATH did not enter the sampled
  dataset at all, despite being present in `data_io/prefix_config_dfm6.yaml`.

Recommended data fix:

1. Convert one-message RLVR rows into supervised two-message chat examples by
   splitting the few-shot `Question:/Answer:` prompt so the final target
   question is the user message and `ground_truth` or the final answer trace is
   the assistant message.
2. For GSM-like data, include a strong direct-answer slice whose target ends in
   a parseable final integer, preferably with a consistent phrase such as
   `The answer is N.` or a boxed final answer if we choose to standardize on
   boxed output.
3. For MATH-like data, ensure the supervised CoT target ends with exactly one
   final `\boxed{...}` answer and avoid examples that leave the answer only in
   prose.
4. Keep MCQ math separate from freeform math. For one-letter MCQ evals, either
   train explicit one-letter direct-answer examples or evaluate with an
   extraction/prompt variant deliberately labeled as non-card-comparable.

Preferred math-format policy, 2026-06-30. Confidence: medium until validated
with a rebuilt sample and eval smoke test. To reduce ambiguity between GSM8K
and MATH during evaluation, make the supervised freeform math contract converge
on one universal format: reasoning if useful, then exactly one final
`\boxed{...}` answer. This should work for MATH directly and remains compatible
with the current GSM8K scorer, which first checks for `\boxed{...}` and then
parses the boxed content as an integer. Direct numeric GSM8K-only rows can still
be kept as a smaller auxiliary slice, but the dominant freeform math style
should be boxed-final-answer rather than split between bare integers, prose
answers, and boxed answers.
