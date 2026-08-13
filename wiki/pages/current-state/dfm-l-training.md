---
type: Operational Record
title: DFM L Training
description: 'Part of Current State: DFM L Training.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# DFM L Training

Part of [Current State](/pages/current-state.md).

Updated on 2026-05-29. Confidence: high.

The active DFM L training run was launched with:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 torchrun --nproc_per_node=8 pretrain.py data=dfm arch/size@arch=L lr=2.5e-4 global_batch_size=172032 +project_name="DFM L" +run_name=dfm-L +checkpoint_path=checkpoints/dfm/L
```

The local W&B run directory is `wandb/run-20260528_234406-kgnbdmwf`. While the run was still active, it was manually synced into the original+mixed W&B project as a second project view with:

```bash
wandb sync --include-online --no-mark-synced --project "Original Plus Mixed Danish Instruction Rich L" wandb/run-20260528_234406-kgnbdmwf
```

W&B reported the target as `peter-sk-sdu/Original Plus Mixed Danish Instruction Rich L/runs/kgnbdmwf` and completed with `done.`.
