---
type: Operational Record
title: DFM4 XL-DDP resume trace instrumentation (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM4 XL-DDP resume
  trace instrumentation (2026-06-03).'
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
# DFM4 XL-DDP resume trace instrumentation (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM4 XL-DDP resume trace instrumentation, 2026-06-03. Confidence: high.

After the optimized skip path still produced a first-step NCCL timeout, targeted
per-rank tracing was added behind `resume_trace`. This flag prints flushed
messages around resume load, EMA reset, carry load, dataset epoch/start-batch
setup, first dataloader yield, first batch device move, supervised-token
all-reduce begin/end, forward/backward begin/end, optimizer step begin/end,
metric reduction, and W&B logging. Default config keeps `resume_trace: false`.
Use `resume_trace=true` and preferably `log_interval=1` for the next diagnostic
resume from `step_150000`.
