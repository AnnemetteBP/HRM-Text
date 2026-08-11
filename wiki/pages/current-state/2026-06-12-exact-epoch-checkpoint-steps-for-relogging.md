---
type: Operational Record
title: 2026-06-12 Exact Epoch Checkpoint Steps For Relogging
description: 'Part of Current State: 2026-06-12 Exact Epoch Checkpoint Steps For Relogging.'
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
# 2026-06-12 Exact Epoch Checkpoint Steps For Relogging

Part of [Current State](/pages/current-state.md).

Confidence: high for local sampler reconstruction and checkpoint-state file
inspection.

For W&B history cleanup/relogging, epoch evaluation rows should be logged at
the real training step where the checkpoint was saved, not at artificial
backfill-adjacent steps. Newer checkpoints have `checkpoint_state_*.json`;
older FSDP2 checkpoints were reconstructed by re-running the same
`MultipackDistributedBatchSampler` over each sampled epoch with the original
`global_batch_size` and world size.

Original Sapient L has no `checkpoint_state_*.json`. Reconstructed from
`data/sampled_original_sapient`, `global_batch_size=172032`, world size `8`,
and local `batch_max_length=21504`:

```text
epoch_1:  81478
epoch_2: 162961
epoch_3: 244443
epoch_4: 325928
```

This matches the W&B train history and checkpoint mtimes: train logging was
every five steps, so the last logged step was `325925` even though the
`epoch_4` checkpoint was saved after step `325928`.

Original Plus Mixed Danish Instruction Rich L also lacks checkpoint-state JSON.
Reconstructed from `data/sampled_original_plus_mixed_danish_instruction_rich`
with the same batch geometry:

```text
epoch_1: 161311
epoch_2: 322628
epoch_3: 483939
epoch_4: 645263
```

DFM L checkpoint-state JSON already records exact steps:

```text
epoch_1: 164670
epoch_2: 329380
epoch_3: 494080
epoch_4: 658771
```

DFM4 XL-DDP checkpoint-state JSON records:

```text
epoch_1: 367247
epoch_2: 734484
```

Use these steps when splitting full/lite EMA/no-EMA metrics into separate
clean runs under a new comparison project.
