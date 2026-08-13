---
type: Operational Record
title: DFM5 XXS Runtime Observation
description: 'Part of Current State: DFM5 XXS Runtime Observation.'
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
# DFM5 XXS Runtime Observation

Part of [Current State](/pages/current-state.md).

Last updated: 2026-06-13
Confidence: high
Scope: Active `dfm5-XXS` 8-GPU training run diagnostics.

The active DFM5 XXS command was observed running at about `22` optimizer
steps/s after compilation, or roughly `4.3M` tokens/s at
`global_batch_size=196,608`. `nvidia-smi dmon` showed B200 SM utilization
around `60-72%` with power draw about `450-480 W/GPU` and only `~8-10 GiB`
GPU memory used. `vmstat` showed no meaningful I/O wait and very low block
input, while `/proc/<pid>/io` for the data workers showed essentially no disk
`read_bytes` during the sample window. This does not look like classic
filesystem/data-loader starvation; it is more likely dominated by the tiny XXS
model size on B200s, per-rank Python/loader overhead, FSDP overhead relative to
the model, and pauses from frequent checkpointing/ephemeral checkpoint cleanup.

Possible future tests: compare FSDP vs DDP for XXS, reduce ephemeral checkpoint
frequency, and test larger per-rank token batches if changing the effective
batch size is acceptable.
