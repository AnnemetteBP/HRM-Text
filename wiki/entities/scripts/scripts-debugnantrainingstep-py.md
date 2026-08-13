---
type: Software Reference
title: '`scripts/debug_nan_training_step.py`'
description: 'Part of Script Entities: `scripts/debug_nan_training_step.py`.'
tags:
- scripts
- software
- catalog
- operations
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# `scripts/debug_nan_training_step.py`

Part of [Script Entities](/entities/scripts.md).

Short distributed diagnostic for NaN training failures.

Responsibilities:

- compose the normal Hydra training config
- initialize distributed/FSDP training through `pretrain.py`
- run a bounded number of real data batches without W&B or checkpoints
- optionally use the production `pretrain.train_batch` compiled path with `--compiled-train-batch`
- report supervised token counts and finite checks for metrics, gradients, parameters, and post-optimizer parameters

Known useful command:

```bash
CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
torchrun --nproc_per_node=1 scripts/debug_nan_training_step.py \
  --steps 12 \
  --compiled-train-batch \
  --override data=original_sapient \
  --override arch/size@arch=L \
  --override lr=2.5e-4 \
  --override global_batch_size=21504
```
