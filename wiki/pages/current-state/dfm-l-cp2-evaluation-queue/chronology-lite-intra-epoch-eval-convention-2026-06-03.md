---
type: Operational Record
title: Lite intra-epoch eval convention (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Lite intra-epoch
  eval convention (2026-06-03).'
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
# Lite intra-epoch eval convention (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Lite intra-epoch eval convention, 2026-06-03. Confidence: high.

`scripts/schedule_checkpoint_evals.sh` now supports `LITE_EVAL=1` for
intra-epoch checkpoint probes. In lite mode, the scheduler queues at most one
deterministic shard per task using `LITE_SHARD_INDEX` (default `0`). A dry run
for `CKPT_TAG=step_50000` queued `19` jobs: one shard for each of the eight
standard tasks, one shard for each of the ten non-IFEval DFM tasks, and one
IFEval-DA shard. Full single-shard tasks still run on their complete task set;
multi-shard tasks run only `shard_0` by default.

Lite metrics deliberately use separate W&B prefixes so they do not pollute full
eval curves:

- standard evals: `lite_eval/*`, x-axis `lite_eval/epoch`
- DFM evals: `lite_dfm_eval/*`, x-axis `lite_dfm_eval/epoch`

For DFM4, `data/sampled_dfm4` has `418,567` optimizer steps per epoch at
`global_batch_size=172032`, so intra-epoch checkpoint x-axis values are:

```text
step_50000:  lite epoch 0.11945518877503482
step_150000: lite epoch 0.35836556632510447
```

Use `QUEUE_ORDER=heavy_first` for these probes so the single long IFEval-DA,
MATH, DROP, and GSM8k shards start early. CP4 timing evidence suggests each
checkpoint's lite probe should be on the order of tens of minutes rather than a
full multi-hour evaluation, with IFEval-DA shard 0 and DROP shard 0 as likely
tails. Confidence: medium for runtime.

Superseded: the first `scripts/schedule_multiple_checkpoint_evals.sh` wrapper
ran checkpoints sequentially. That was the wrong design for multi-checkpoint
evals, because it could not fill idle GPUs from checkpoint N+1 while checkpoint
N still had a few long tail jobs running. Confidence: high.
