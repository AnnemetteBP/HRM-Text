---
type: Operational Record
title: DDP parameter precision modes (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DDP parameter
  precision modes (2026-06-03).'
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
# DDP parameter precision modes (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DDP parameter precision modes, 2026-06-03. Confidence: high.

`pretrain.py` now exposes `ddp_params_precision` for DDP-only precision
experiments. The default is `fp32`, which keeps persistent DDP parameters,
optimizer state, and EMA in fp32 while using CUDA autocast with `fwd_bwd_dtype`
for forward/backward compute. This mirrors the important precision property of
the FSDP2 path: low-precision compute without converting the optimizer-updated
weights to bf16. The FSDP path remains the default `distributed_strategy` and
was not changed by this option.

The second mode is `bf16`. In this mode DDP casts the model to `fwd_bwd_dtype`
before wrapping, so persistent parameters and Adam moments follow that
low-precision dtype, while `AdamATan2` is asked to store only `param_ema` in
fp32. A local optimizer smoke check with bf16 parameters confirmed `exp_avg`
and `exp_avg_sq` are bf16 while `param_ema` remains fp32 before and after an
optimizer step. This mode is intended to isolate whether the bad DDP checkpoints
were caused specifically by bf16 EMA, without paying the full memory cost of
fp32 DDP weights and optimizer state.
