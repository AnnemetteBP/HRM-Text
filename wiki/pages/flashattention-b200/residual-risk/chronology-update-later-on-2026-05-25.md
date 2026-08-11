---
type: Technical Reference
title: Update later on (2026-05-25)
description: 'Chronological record from Residual Risk: Update later on (2026-05-25).'
tags:
- flashattention
- b200
- cuda
- performance
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/flashattention-b200/residual-risk.md
---
# Update later on (2026-05-25)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Update later on 2026-05-25: a first custom Metal/MPS PrefixLM attention backend was added at `models/flash_attention_prefixlm_mps.py`. It is now opt-in only via:

```bash
HRM_ENABLE_EXPERIMENTAL_MPS_KERNEL=1
```

Default `accelerator_type=mps` uses the safer dense PyTorch fallback. The prototype streams exact PrefixLM attention without materializing dense attention matrices or masks. It is a correctness/memory prototype, not yet a tiled FlashAttention-class kernel.

Verified numeric parity against the dense fallback on a tiny hand-built PrefixLM batch:

```text
forward max abs diff: 4.77e-7
dq max abs diff:      2.21e-6
dk max abs diff:      2.38e-6
dv max abs diff:      1.91e-6
```

Verified model-level smoke:

```bash
/Users/petersk/Nobackup/miniconda3/bin/conda run -n hrm python scripts/debug_nan_training_step.py \
  --steps 1 \
  --override data.path=data/sampled_original_sapient_partial_smoke \
  --override arch/size@arch=XXS \
  --override accelerator_type=mps \
  --override compile_train_batch=false \
  --override fwd_bwd_dtype=float32 \
  --override global_batch_size=1024 \
  --override gradient_accumulation_steps=1 \
  --override epochs=1 \
  --override lr=2.5e-4 \
  --override lr_warmup_steps=10 \
  --override ema=null \
  --override arch.H_cycles=1 \
  --override arch.L_cycles=1 \
  --override +arch.bp_min_steps=1 \
  --override arch.bp_max_steps=1
```

Result: one MPS training step completed with finite loss, metrics, gradients, and post-optimizer parameters. The larger default-cycle `XXS` probe at `global_batch_size=4096` did not finish quickly; likely cause is the prototype kernel's untiled per-query/per-key loops. A follow-up attempt to vectorize the kernel with threadgroup reductions was unstable enough to lock up the machine during testing, so the experimental kernel must remain opt-in until it is redesigned and tested in much smaller standalone kernels. Confidence: high for tiny correctness probes, low for performance readiness.
