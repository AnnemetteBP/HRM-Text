---
type: Operational Record
title: DFM4 XL-DDP step 200K EMA vs no-EMA lite eval (2026-06-04)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM4 XL-DDP step
  200K EMA vs no-EMA lite eval (2026-06-04).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm-l-cp2-evaluation-queue.md
---
# DFM4 XL-DDP step 200K EMA vs no-EMA lite eval (2026-06-04)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM4 XL-DDP step 200K EMA vs no-EMA lite eval, 2026-06-04. Confidence: high.

The `step_200000` EMA lite eval completed locally with `WANDB_SYNC=0`, so it
did not sync to W&B. EMA logs are under
`logs/eval/dfm4_XL_ddp_ema_lite_probe_20260604T064428_200k` and
`logs/dfm_evals/dfm4_XL_ddp_ema_lite_probe_20260604T064428_200k`; no-EMA logs
are under `logs/eval/dfm4_XL_ddp_noema_lite_probe_20260604T035517_200k` and
`logs/dfm_evals/dfm4_XL_ddp_noema_lite_probe_20260604T035517_200k`. A local
comparison report was written to
`logs/eval/dfm4_XL_ddp_ema_vs_noema_200k.md`.

Headline aggregate metrics: EMA improved ARC, DROP, GSM8k, HellaSwag, MATH,
MMLU, Winogrande, Danish citizen tests, DALA, GEC-DALA, WMT24++ EN-DA,
MultiWikiQA, NordjyllandNews, and HumanEval in this lite slice. EMA regressed
BoolQ, PIQA, generative Talemaader, and GovReport. This is a lite one-shard
comparison only, not a full benchmark result.
