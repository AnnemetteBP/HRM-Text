---
type: Operational Record
title: DDP XL memory observation on (2026-06-02)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DDP XL memory
  observation on (2026-06-02).'
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
# DDP XL memory observation on (2026-06-02)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DDP XL memory observation on 2026-06-02. Confidence: high.

The user reported, and local `nvidia-smi` confirmed, that an HRM XL DDP run on
DFM4 fits on 8 B200 GPUs at roughly `78-81GB` used per GPU with active GPU
utilization around `89-91%`. This is after the DDP bf16 cast and
`find_unused_parameters=True` fixes. The observed memory is much lower than the
earlier worst-case expectation for full DDP state, so DDP is a viable benchmark
path for at least XL on these 180GB GPUs. Current live query showed:

```text
GPU0 77696 MiB, GPU1 78348 MiB, GPU2 80778 MiB, GPU3 81224 MiB,
GPU4 81030 MiB, GPU5 81358 MiB, GPU6 79026 MiB, GPU7 81364 MiB
```

This observation is hardware/config specific and should not be generalized to
H100-80 without a separate run.
