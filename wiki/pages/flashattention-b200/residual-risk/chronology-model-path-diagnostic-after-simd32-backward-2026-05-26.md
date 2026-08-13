---
type: Technical Reference
title: Model-path diagnostic after SIMD32 backward (2026-05-26)
description: 'Chronological record from Residual Risk: Model-path diagnostic after
  SIMD32 backward (2026-05-26).'
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
# Model-path diagnostic after SIMD32 backward (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Model-path diagnostic after SIMD32 backward, 2026-05-26:

```bash
HRM_ENABLE_EXPERIMENTAL_MPS_KERNEL=1 \
HRM_EXPERIMENTAL_MPS_MAX_TOKENS=4096 \
HRM_EXPERIMENTAL_MPS_MAX_SEQS=4096 \
HRM_EXPERIMENTAL_MPS_MAX_HEADS=2 \
HRM_EXPERIMENTAL_MPS_MAX_HEAD_DIM=128 \
/Users/petersk/Nobackup/miniconda3/bin/conda run -n hrm python scripts/debug_nan_training_step.py \
  --steps 1 \
  --override data.path=data/sampled_original_sapient_partial_smoke \
  --override arch/size@arch=XXS \
  --override accelerator_type=mps \
  --override compile_train_batch=false \
  --override fwd_bwd_dtype=float32 \
  --override global_batch_size=4096 \
  --override gradient_accumulation_steps=1 \
  --override epochs=1 \
  --override lr=2.5e-4 \
  --override lr_warmup_steps=10 \
  --override ema=null
```

Result: one real XXS model training diagnostic step completed on MPS with the experimental kernel enabled. The run reported finite loss (`11.602989196777344`), finite metrics, finite gradients, finite parameters, and finite post-optimizer parameters. Confidence: high.
