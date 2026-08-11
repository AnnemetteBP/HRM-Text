---
type: Operational Record
title: DFM4 XL-DDP unsharded resume collective mismatch (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM4 XL-DDP unsharded
  resume collective mismatch (2026-06-03).'
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
# DFM4 XL-DDP unsharded resume collective mismatch (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM4 XL-DDP unsharded resume collective mismatch, 2026-06-03. Confidence: high.

The traced `step_150000` DDP resume crash is specific to the unsharded resume
path, not to ordinary fresh training. Rank 0 times out inside
`torch.distributed.checkpoint.set_state_dict()` while running a DCP
`BROADCAST`, whereas ranks 1-7 have already left checkpoint restore and entered
the first training `_supervised_token_count()` `ALLREDUCE`. This mismatched
collective ordering causes the NCCL watchdog timeout. Fresh starts avoid this
because they do not call `load_unsharded_train_state()`. The likely fix is to
replace the DDP unsharded distributed DCP restore path with a DDP-safe loader,
for example all ranks loading the rank-0 unsharded checkpoint locally and then
using ordinary local model/optimizer `load_state_dict`, or saving future DDP
checkpoints in a per-rank/sharded format.
