---
type: Operational Record
title: Checkpoint format update on (2026-06-02)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Checkpoint format
  update on (2026-06-02).'
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
# Checkpoint format update on (2026-06-02)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Checkpoint format update on 2026-06-02. Confidence: high.

`pretrain.py` now has an explicit `checkpoint_format` config field with
default `sharded`. The default path is intentionally the existing FSDP2/PyTorch
DCP checkpointing path and writes model/optimizer state under `fsdp2_{tag}` plus
rank-local carry files named `carry_{tag}.{rank}.pt`. This is the path to use
for current FSDP training unless a specific experiment needs otherwise.

An opt-in `checkpoint_format=unsharded` path was added. It writes a full
model/optimizer checkpoint from global rank 0 to `unsharded_{tag}.pt`, while
still writing rank-local carry files for every rank. In distributed/FSDP runs it
uses `StateDictOptions(full_state_dict=True, cpu_offload=True)` when saving and
`broadcast_from_rank0=True` when loading, so it is multi-node aware in the sense
that only global rank 0 owns the serialized full checkpoint and all ranks load
through the distributed state-dict API. This path is not the default and may
have much higher CPU RAM and filesystem pressure than the sharded DCP path.

Checkpoint sidecar metadata now records `checkpoint_format` alongside `tag`,
`step`, `epoch`, `batch_in_epoch`, `global_batch_size`, `data_path`, and
`seed`. Validation performed after the change: `python -m py_compile
pretrain.py`, `git diff --check`, and loading `config/cfg_pretrain.yaml` to
verify that the default is `sharded`.
