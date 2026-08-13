---
type: Operational Record
title: DFM5 XXS FSDP fp32-params vs bf16-params 1K loss windows (2026-06-14)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5 XXS FSDP
  fp32-params vs bf16-params 1K loss windows (2026-06-14).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# DFM5 XXS FSDP fp32-params vs bf16-params 1K loss windows (2026-06-14)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5 XXS FSDP fp32-params vs bf16-params 1K loss windows, 2026-06-14.
Confidence: high for W&B API history. Compared run `2tv9u438` (`dfm5-XXS`,
default/fp32 persistent FSDP params) with run `4ch8y3e8`
(`dfm5-XXS-fsdp-bf16`, `fsdp_params_precision=bf16`). The bf16 run had W&B
history through `_step=17140` at inspection. In every complete 1K window
through 17K, bf16-params had substantially higher training loss; the gap grew
from `+0.78` to about `+1.22` after 2K. This supports treating the bf16
persistent-parameter/optimizer-state mode as degraded for this optimizer.
