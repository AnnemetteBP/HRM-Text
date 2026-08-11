---
type: Operational Record
title: DDP benchmark path update on (2026-06-02)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DDP benchmark
  path update on (2026-06-02).'
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
# DDP benchmark path update on (2026-06-02)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DDP benchmark path update on 2026-06-02. Confidence: high.

`pretrain.py` now has `distributed_strategy` with default `fsdp`. The default
FSDP behavior is unchanged. An opt-in `distributed_strategy=ddp` wraps the model
in `torch.nn.parallel.DistributedDataParallel` after construction and before
optimizer creation. This path is intended for memory/speed experiments on
large-memory GPUs, not as the default training path. Custom model methods used
by the loop are called through a small unwrap helper so DDP-wrapped models can
still provide `compute_train_extra_args`.

For a DDP L-size DFM4 memory/speed probe, use `data=dfm4`,
`arch/size@arch=L`, `distributed_strategy=ddp`, and strongly consider
`checkpoint_format=unsharded` with a separate checkpoint directory. DDP keeps a
full model, gradients, optimizer state, and EMA state on every GPU, so it is
expected to use far more memory than the FSDP sharded path. Validation performed
after the change: `python -m py_compile pretrain.py` and loading
`config/cfg_pretrain.yaml` verified defaults of `distributed_strategy=fsdp` and
`checkpoint_format=sharded`.
