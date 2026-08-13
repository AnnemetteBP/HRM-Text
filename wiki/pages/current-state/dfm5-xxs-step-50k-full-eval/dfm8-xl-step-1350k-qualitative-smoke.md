---
type: Operational Record
title: DFM8 XL Step 1350K Qualitative Smoke
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM8 XL Step 1350K Qualitative
  Smoke.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# DFM8 XL Step 1350K Qualitative Smoke

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-07-16. Confidence: high for local command/output paths; medium for
manual qualitative scoring.

The extended DFM6-DFM7 epoch_5 smoke prompt suite was rerun on the DFM8 XL
`step_1350000` EMA HF export:

```bash
CUDA_VISIBLE_DEVICES=2 python scripts/smoke_dfm6_dfm7_epoch5_qualitative.py \
  --model exports/dfm8_XL_step1350000_ema_hf \
  --output-jsonl logs/analysis/dfm8_XL_step1350000_smoke/generations.jsonl \
  --output-md docs/dfm8-xl-step1350000-smoke-raw.md \
  --gpu-memory-utilization 0.20 \
  --batch-size 1

python scripts/build_smoke_comparison_report.py \
  --previous-jsonl logs/analysis/dfm6_dfm7_epoch5_extended_smoke/generations.jsonl \
  --current-jsonl logs/analysis/dfm8_XL_step1350000_smoke/generations.jsonl \
  --output-md docs/dfm8-xl-step1350000-smoke.md
```

The comparison report is in `docs/dfm8-xl-step1350000-smoke.md`; raw generations
are in `logs/analysis/dfm8_XL_step1350000_smoke/generations.jsonl`.

Manual qualitative result:

- DFM8 XL `step_1350000` EMA: 27 pass, 11 weak, 2 bad over 40 prompts.
- Previous DFM6-DFM7 `epoch_5` EMA under the same stricter manual pass:
  27 pass, 10 weak, 3 bad.
- Relative movement: 7 improved, 29 unchanged, 4 regressed.

Main interpretation: `step_1350000` improves explicit boxed-answer and simple
format following, fixes several simple refusal/tool-confusion cases, and keeps
basic chat/code/summarization usable. Remaining weaknesses are native tool-call
termination, one serious Danish algebra miss (`\boxed{5}` instead of `7`), and
regressed repetition in creative generation.
