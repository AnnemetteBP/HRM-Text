---
type: Operational Record
title: DFM5 XXS 50K FSDP-vs-DDP eval table (2026-06-14)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5 XXS 50K
  FSDP-vs-DDP eval table (2026-06-14).'
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
# DFM5 XXS 50K FSDP-vs-DDP eval table (2026-06-14)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5 XXS 50K FSDP-vs-DDP eval table, 2026-06-14. Confidence: high for local
artifact extraction. A Markdown comparison of the workspace panel metrics for
`dfm5-XXS` 50K (`2tv9u438`) and `dfm5-XXS-ddp` 50K (`pqc9g81u`) was generated
from local `merged_metrics.json` files, with training metrics pulled from the
nearest W&B history rows to step 50K. The FSDP 50K headline averages were
originally computed with fewer metrics (`9/7/3` Danish/English/Math-Code)
than the DDP 50K averages (`18/15/4`), so headline averages are not strictly
apples-to-apples even though per-panel rows are directly comparable where both
values exist.
