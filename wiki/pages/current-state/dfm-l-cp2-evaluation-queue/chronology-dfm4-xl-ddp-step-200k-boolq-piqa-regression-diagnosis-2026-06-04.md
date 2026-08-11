---
type: Operational Record
title: DFM4 XL-DDP step 200K BoolQ/PIQA regression diagnosis (2026-06-04)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM4 XL-DDP step
  200K BoolQ/PIQA regression diagnosis (2026-06-04).'
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
# DFM4 XL-DDP step 200K BoolQ/PIQA regression diagnosis (2026-06-04)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM4 XL-DDP step 200K BoolQ/PIQA regression diagnosis, 2026-06-04.
Confidence: high for PIQA sample logs and BoolQ probe mechanics; medium for
generalizing the BoolQ probe to the full BoolQ run.

PIQA sample-level Inspect logs from the 200K lite eval show that the PIQA
regression is not a formatting/parser issue. No-EMA produced parseable `A`/`B`
answers for `107/108` samples and EMA also produced parseable `A`/`B` answers
for `107/108` samples. The regression is due to answer choice/content: no-EMA
had prediction distribution `A=23`, `B=84`, `<none>=1` on a target distribution
`A=95`, `B=13`; EMA shifted even harder to `B=102`, `A=5`, `<none>=1`. Paired
PIQA changes were `C->W=18`, `C->C=16`, `W->W=74`, and no `W->C`; the observed
loss is mostly no-EMA-correct `A` samples switching to EMA `B`.

BoolQ standard eval does not persist per-sample generations, so a deterministic
256-sample probe was run with the same benchmark class and generation settings
as the lite eval (`condition=direct`, `max_context=4096`, `max_tokens=1`,
`batch_size=1`). The probe wrote
`logs/eval/dfm4_XL_ddp_boolq_ema_vs_noema_200k_probe.json`. Both no-EMA and EMA
outputs were structurally valid on `256/256` samples. The target distribution
was `A=154`, `B=102`; no-EMA predicted `A=232`, `B=24` and scored `146/256`,
while EMA predicted `B=234`, `A=22` and scored `104/256`. Thus the BoolQ
regression is also an answer-prior/content shift rather than invalid output
format.
