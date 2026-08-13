---
type: Operational Record
title: DDP fp32-vs-FSDP fp32 continuation caveats (2026-06-14)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DDP fp32-vs-FSDP
  fp32 continuation caveats (2026-06-14).'
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
# DDP fp32-vs-FSDP fp32 continuation caveats (2026-06-14)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DDP fp32-vs-FSDP fp32 continuation caveats, 2026-06-14. Confidence: high for
inspected code; medium for expected numerical effect until directly tested
from a converted checkpoint.

If DDP `ddp_params_precision=fp32` and FSDP `fsdp_params_precision=fp32` are
started from the same model/optimizer/EMA/carry state and the same dataset
position, the logged training loss should be directly comparable because
metrics are logged from raw summed CE and local valid-token counts, then
summed across ranks in `reduce_metrics`. The logging path is independent of
whether gradients are averaged or summed.

There are still two code-level sources of different subsequent losses:

1. Gradient reduction scaling differs. FSDP explicitly calls
   `set_gradient_divide_factor(1.0)` and `set_force_sum_reduction_for_comms`,
   while PyTorch DDP averages gradients by default. The loss divisor is the
   average valid-token count across ranks. Therefore DDP computes the
   conventional global-token mean gradient, while FSDP produces a world-size
   scaled gradient. `AdamATan2` is intended to be scale-invariant for the
   gradient update, so this should mostly cancel, but finite-precision moment
   updates can still differ slightly.

2. Mixed precision is implemented differently. FSDP uses module-level
   `MixedPrecisionPolicy(param_dtype=fwd_bwd_dtype, reduce_dtype=fp32)`.
   DDP fp32 keeps persistent parameters fp32 and enables CUDA autocast around
   the forward/backward batch. Autocast is op-level and FSDP mixed precision is
   module-boundary-level, so exact bf16/fp32 choices can differ for operations
   such as linear projections, RMSNorm, and attention. Starting from identical
   weights can still yield slightly different logits/losses and then divergent
   training trajectories.

Other inspected differences are less concerning for loss equivalence:
DDP `init_sync=True` broadcasts parameters/buffers at wrap time; checkpoint
resume through the unsharded path loads the same full checkpoint on every rank
for DDP; `find_unused_parameters=True` is needed for the HRM warmup/unused
parameter pattern and should not change gradients for used parameters; both
paths use the same dataloader seed/rank/world-size interface.
