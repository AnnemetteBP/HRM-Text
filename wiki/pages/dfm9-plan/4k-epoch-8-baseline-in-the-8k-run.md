---
type: Plan Record
title: 4K Epoch-8 Baseline in the 8K Run
description: 'Part of DFM9 Plan: 4K Epoch-8 Baseline in the 8K Run.'
tags:
- dfm9
- data
- training
- factual-knowledge
- code
status: stable
last_updated: 2026-08-18
confidence: high
part_of: /pages/dfm9-plan.md
---
# 4K Epoch-8 Baseline in the 8K Run

Part of [DFM9 Plan](/pages/dfm9-plan.md).

Update, 2026-08-24. The original 4K epoch-8 EMA checkpoint is already
available as `exports/dfm9_XL_step_2127489_ema_hf`. For the long-context
baseline in the `dfm9-xl-8k` W&B run, the scheduler uses a separate
config-only YaRN-2.0 export:
`exports/dfm9_XL_step_2127489_ema_hf_yarn2_8k`.

The weights and tokenizer are unchanged; its config declares
`max_position_embeddings=8192`, `rope_type=yarn`, `factor=2.0`, and
`original_max_position_embeddings=4096`. This allows the epoch-8 checkpoint
to run the same 8K evaluation suite as the 2150K 8K checkpoint, but it is an
inference-time extrapolation baseline, not a model trained with 8K context.
The original 4K export remains preserved separately.

- Should DFM9 be a full rebuild or an incremental adjustment to DFM8?
- Should the model continue from DFM8 L epoch 3 checkpoint or start fresh?
- Are there additional Wikipedia-derived QA sources worth adding beyond FLAN?
- Should sub-prefixing also separate science from commonsense FLAN?
