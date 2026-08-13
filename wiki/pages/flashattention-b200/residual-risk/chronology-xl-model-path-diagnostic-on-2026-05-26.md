---
type: Technical Reference
title: XL model-path diagnostic on (2026-05-26)
description: 'Chronological record from Residual Risk: XL model-path diagnostic on
  (2026-05-26).'
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
# XL model-path diagnostic on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

XL model-path diagnostic on 2026-05-26:

```bash
HRM_ENABLE_EXPERIMENTAL_MPS_KERNEL=1 \
HRM_EXPERIMENTAL_MPS_MAX_TOKENS=1024 \
HRM_EXPERIMENTAL_MPS_MAX_SEQS=1024 \
HRM_EXPERIMENTAL_MPS_MAX_HEADS=12 \
HRM_EXPERIMENTAL_MPS_MAX_HEAD_DIM=128 \
/Users/petersk/Nobackup/miniconda3/bin/conda run -n hrm python scripts/debug_nan_training_step.py \
  --steps 1 \
  --override data.path=data/sampled_original_sapient_partial_smoke \
  --override arch/size@arch=XL \
  --override accelerator_type=mps \
  --override compile_train_batch=false \
  --override fwd_bwd_dtype=float32 \
  --override global_batch_size=1024 \
  --override gradient_accumulation_steps=1 \
  --override epochs=1 \
  --override lr=2.5e-4 \
  --override lr_warmup_steps=10 \
  --override ema=null
```

Result: one real XL model diagnostic step completed on MPS with the experimental kernel enabled. The run reported finite loss (`11.610648155212402`), finite metrics, finite gradients, finite parameters, and finite post-optimizer parameters.

Memory readout:

```text
mps_memory startup: current=0.000 MiB driver=0.375 MiB
mps_memory after_init: current=13544.016 MiB driver=14416.438 MiB
mps_memory step_1_before_train: current=13545.035 MiB driver=14416.422 MiB
mps_memory step_1_after_train: current=18533.056 MiB driver=24064.703 MiB
mps_memory step_1_after_zero_grad: current=13545.056 MiB driver=24066.859 MiB
```

Interpretation: at `global_batch_size=1024`, the XL diagnostic needs about `13.5 GiB` live MPS allocation after model/optimizer init and peaks at about `18.5 GiB` live allocation after the train/optimizer step. The Metal/MPS driver allocator retained about `24.1 GiB`. Confidence: high.
