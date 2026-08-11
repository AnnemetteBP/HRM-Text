---
type: Operational Record
title: DDP fp32-EMA resume failure/fix (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DDP fp32-EMA resume
  failure/fix (2026-06-03).'
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
# DDP fp32-EMA resume failure/fix (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DDP fp32-EMA resume failure/fix, 2026-06-03. Confidence: high.

The first attempt to resume DFM4 XL-DDP from `checkpoints/dfm4/XL-ddp`
`step_150000` with `ddp_params_precision=bf16` and `reset_ema_on_resume=true`
failed before loading the checkpoint. PyTorch DCP raised
`ValueError: Unexpected value type <class 'torch.dtype'>` while traversing the
new optimizer state dict in `set_state_dict(...)`. The cause was the new
`AdamATan2(ema_dtype=torch.float32)` argument being stored directly in optimizer
param groups; DCP accepts tensor/primitive-like state-dict values but not raw
`torch.dtype` objects. `AdamATan2` now serializes `ema_dtype` as a string such
as `"float32"` in param groups and resolves it internally when allocating
`param_ema`. A local smoke check confirmed bf16 params, bf16 Adam moments, fp32
EMA, and a serialized optimizer param group with string `ema_dtype`.
