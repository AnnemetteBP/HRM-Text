---
type: Operational Record
title: Carry state with FSDP vs DDP (2026-06-02)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Carry state with
  FSDP vs DDP (2026-06-02).'
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
# Carry state with FSDP vs DDP (2026-06-02)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Carry state with FSDP vs DDP, 2026-06-02. Confidence: high.

Carry is not managed by FSDP or DDP. It is explicit `TrainState.carry` owned by
each process. The model receives it on every forward pass and returns the next
carry via `train_state.carry, loss, metrics = model(...)`. Checkpointing saves
it separately as `carry_{tag}.{rank}.pt` on every rank and resume reloads the
file matching the current global rank. This is the same mechanism for FSDP and
DDP; only the model/optimizer checkpoint format differs.

For current L-size HRM runs using `baselines.hrm_nocarry_bp_warmup`,
`initial_carry(...)` returns `None`, so the carry files are effectively saved
`None` placeholders. For any future carryful model, resuming should preserve
the same world-size/rank mapping and physical local batch shape unless the carry
implementation is explicitly made reshapeable or reinitializable.
