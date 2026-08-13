---
type: Plan Record
title: DFM6-DFM7 840K Format Smoke
description: 'Part of DFM7 Plan: DFM6-DFM7 840K Format Smoke.'
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
# DFM6-DFM7 840K Format Smoke

Part of [DFM7 Plan](/pages/dfm7-plan.md).

Step 840000 smoke test, 2026-07-02. Confidence: high from local HF export,
vLLM server, OpenAI tool-call requests, and BFCL proxy smoke outputs.

- Exported EMA checkpoint:
  `exports/dfm6_dfm7_XL_gas2_step_840000_ema_hf_smoke_20260702_083848`
  from `checkpoints/dfm7/XL-gas2-from-dfm6-epoch3` with
  `conversion/convert_to_hf.py --ckpt_tag step_840000 --ckpt_use_ema true`.
- Smoke outputs were written to
  `logs/smoke/dfm6_dfm7_step840000_math_tool_20260702_083929/`.
- vLLM must see `/home/ucloud/miniforge3/envs/hrm/bin` on `PATH`; otherwise
  FlashInfer sampling JIT fails with `FileNotFoundError: ninja`.
- For OpenAI `tool_choice=auto`, vLLM must be launched with
  `--enable-auto-tool-choice --tool-call-parser gemma4`; without those flags
  tool requests fail with HTTP 400 before model inference.

Observed behavior:

- MCQ math format is correct on the probe: the model returned exactly `B` for
  a one-letter arithmetic multiple-choice prompt.
- Freeform math still did not follow the desired boxed-final-answer contract.
  GSM/MATH-style prompts that explicitly requested `\boxed{...}` produced
  correct arithmetic but ended with `$34$`, `$42$`, or prose instead of a final
  boxed answer.
- Tool calling is structurally active with the Gemma4 parser. The first tool
  call is usually the right function/arguments for simple calculator/weather
  prompts, and a no-tool greeting produced no tool call.
- Tool-call stopping/control is still weak. With larger generation budgets the
  model repeats tool calls and can add spurious calls; at short budgets
  (`max_tokens` 16-24) the first call is cleaner but may omit a required
  argument at 16 tokens.
- The BFCL proxy path also converts a BFCL-shaped prompt into native tools and
  returns parser-compatible JSON content, but the calculator smoke still
  repeated the same tool call twice. This suggests the remaining issue is model
  generation/stopping quality, not a complete eval-pipeline mismatch.

DFM7 math-format source audit, 2026-07-02. Confidence: high from local
sampling-config inspection, `data/show_analytics_dfm7.md`, and source-row
sampling. Audit files:
`logs/dfm7_math_format_audit_20260702_corrected.json`.

- The fixed DFM7 RLVR converters do teach boxed-final answers, but their weight
  is far too small to dominate the math response contract. Sampled target
  tokens over 5 epochs:
  - `allenai_rlvr_gsm`: 3.10M target tokens.
  - `allenai_rlvr_math`: 3.66M target tokens.
  - Combined boxed RLVR: 6.76M target tokens over 5 epochs, or 1.35M per
    epoch.
- Major inherited math-ish sources still dominate the target-token budget and
  use mixed/non-boxed answer styles:
  - `openmathinstruct2`: 10.66B target tokens over 5 epochs. Sampled
    `cot.parquet` rows contained `\boxed{...}` often, but only about 3.1% of
    sampled rows ended with a boxed answer; `direct.parquet` rows were mostly
    bare answers.
  - `dmmath`: 11.28B target tokens over 5 epochs. Sampled rows were bare
    numeric direct answers.
  - `ampsmathematica`: 444M target tokens over 5 epochs. Sampled rows were
    `$...$` LaTeX answers, not boxed.
  - `flan`: 24.01B target tokens over 5 epochs. Sampled GSM8K CoT rows used
    prose answer styles such as `The answer: 24.`, not boxed finals.
- Just `openmathinstruct2 + dmmath + ampsmathematica + flan` contribute
  about 46.40B target tokens over 5 epochs, or 9.28B target tokens per epoch.
  That is roughly 6,861x the target-token weight of the corrected boxed RLVR
  sources.
- Conclusion: more DFM7 training can improve math ability, but the current
  DFM7 mix should not be expected to reliably learn the desired freeform math
  output contract (`reasoning, then exactly one final \boxed{...}`) from the
  data as sampled. The boxed-contract signal exists but is swamped by inherited
  bare/prose/`$...$` math answer formats.
