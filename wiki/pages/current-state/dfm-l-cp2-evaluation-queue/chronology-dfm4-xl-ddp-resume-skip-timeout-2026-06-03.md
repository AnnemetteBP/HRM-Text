---
type: Operational Record
title: DFM4 XL-DDP resume skip timeout (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM4 XL-DDP resume
  skip timeout (2026-06-03).'
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
# DFM4 XL-DDP resume skip timeout (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM4 XL-DDP resume skip timeout, 2026-06-03. Confidence: high.

The attempt to resume DFM4 XL-DDP from `step_150000` with
`ddp_params_precision=bf16` and reset fp32 EMA failed after the checkpoint load
with a NCCL watchdog timeout. The stack traces showed ranks stuck in different
collective sequence numbers: several ranks timed out in
`_supervised_token_count()` at a one-scalar `all_reduce`, while rank 0 had a
later DDP `BROADCAST`. This is a distributed desync caused by the resume path
materializing and discarding `batch_in_epoch=150000` batches per rank:

```python
for batch_in_epoch, (batch, batch_info) in enumerate(train_loader, start=1):
    if skip_batches > 0 and batch_in_epoch <= skip_batches:
        continue
```

Because the `continue` happened after `DataLoader` yielded, every skipped batch
still loaded mmap slices, built tensors, computed PrefixLM aux tensors, and in
CUDA runs used the worker/datapipe machinery. Different ranks could therefore
finish the huge skip at different wall-clock times; ranks that entered the first
post-skip collective waited until NCCL's 600s timeout for slower ranks.

`dataset_new.py` now supports `V1Dataset.set_start_batch(start_batch)`.
`__iter__()` advances the deterministic multipack sampler to that batch index
before calling `_load_batch(...)`, so skipped batches are not materialized.
`pretrain.py` calls this on resume and starts the loop enumeration at
`skip_batches + 1`, preserving future `checkpoint_state_step_*.json`
`batch_in_epoch` values. Validation passed with
`python -m py_compile pretrain.py dataset_new.py models/adam_atan2.py`,
`git diff --check`, and a local temporary-dataset smoke test showing
`set_start_batch(1)` skips the only batch.
