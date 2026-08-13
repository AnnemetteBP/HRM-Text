---
type: Operational Record
title: DFM4 XL-DDP all-ranks unsharded restore patch (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM4 XL-DDP all-ranks
  unsharded restore patch (2026-06-03).'
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
# DFM4 XL-DDP all-ranks unsharded restore patch (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM4 XL-DDP all-ranks unsharded restore patch, 2026-06-03. Confidence: high.

`pretrain.py` now avoids the rank-0-only broadcast restore for
`distributed_strategy=ddp` and `checkpoint_format=unsharded`. In distributed DDP
jobs, every rank loads `unsharded_{tag}.pt` from CPU and then calls
`torch.distributed.checkpoint.set_state_dict()` with `full_state_dict=True`,
`cpu_offload=True`, and `broadcast_from_rank0=False`. This keeps the FQN-keyed
DCP optimizer state mapping while avoiding the bad collective ordering where
rank 0 was still broadcasting checkpoint tensors after other ranks had entered
training. Non-DDP distributed unsharded restores keep the previous rank-0
broadcast path. Validation passed with `python -m py_compile pretrain.py
dataset_new.py models/adam_atan2.py` and `git diff --check`.
