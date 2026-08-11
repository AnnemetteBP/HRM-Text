---
type: Operational Record
title: DFM L train-history backfill to Original Plus Mixed project (2026-06-01)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM L train-history
  backfill to Original Plus Mixed project (2026-06-01).'
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
# DFM L train-history backfill to Original Plus Mixed project (2026-06-01)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM L train-history backfill to Original Plus Mixed project, 2026-06-01.
Confidence: high.

The target project `Original Plus Mixed Danish Instruction Rich L`, run
`kgnbdmwf`, initially had only partial DFM L `train/*` history when sampled via
the W&B API: visible train rows reached about step `302575`, while the source
project `DFM L`, run `kgnbdmwf`, reached about step `592395`.

Attempted direct full-file sync from the local full run:

```bash
wandb sync --include-online --no-mark-synced \
  --project "Original Plus Mixed Danish Instruction Rich L" \
  wandb/run-20260528_234406-kgnbdmwf
```

This completed and updated summary state, but the target run still lacked
high-step `train/*` history above `500k`.

A direct API replay with `wandb.log(..., step=<source_step>)` was also attempted
and then stopped. It failed conceptually because eval backfills had already
advanced W&B's internal `_step` to about `900124`; W&B rejected later train
rows at `_step` values `302k..592k` as non-monotonic.

Superseded by the clean-run solution recorded above on 2026-06-01: replay the full DFM L train history into the target run using
W&B's monotonic internal step, while storing the original training step in
`train/source_step` and defining it as the step metric for train curves. The
successful replay logged `118,775` source train points from source step `5` to
`592395` into `Original Plus Mixed Danish Instruction Rich L/kgnbdmwf`.

Verification after replay:

```text
train/source_step = 592395
train/loss = 1.1001414060592651
train/accuracy = 0.7316066026687622
train/exact_accuracy = 0.1923076957464218
train/lr = 0.00025
train/dfm_loss = 1.1001414060592651
train/dfm_accuracy = 0.7316066026687622
train/dfm_exact_accuracy = 0.1923076957464218
train/dfm_lr = 0.00025
```

This same-run replay polluted the original target run and should not be used
for clean train plots. For the clean comparison, use
`Original Plus Mixed Danish Instruction Rich L/dfmlfull0601`; it has native
train `_step` values plus eval and dfm_eval metrics. The
`train/dfm_*` metrics are duplicated aliases intended to make the DFM L
backfilled train curves easy to distinguish from any older partial `train/*`
history in the target project.
