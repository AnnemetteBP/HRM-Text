---
type: Operational Record
title: DFM8 L Resume Point, 2026-07-24
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM8 L Resume Point, 2026-07-24.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# DFM8 L Resume Point, 2026-07-24

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Confidence: high from local checkpoint sidecar/shard inspection and W&B API
configuration readback.

Despite the run name and checkpoint directory containing `gbs131072`, the
actual DFM8 L run used:

```text
global_batch_size=262144
gradient_accumulation_steps=1
lr=3e-4
epochs=1
```

The W&B target is project `DFM5`, run ID `g2oaotmc`, display name
`DFM8-L-gbs131072`. The newest complete checkpoint is
`ephemeral_step_43000` under `checkpoints/dfm8/L-gbs131072`; it has DCP
metadata, all 8 model shards, all 8 carry files, and an exact epoch-1 batch
cursor. Resume must preserve the actual 262144-token global batch despite the
legacy name.
