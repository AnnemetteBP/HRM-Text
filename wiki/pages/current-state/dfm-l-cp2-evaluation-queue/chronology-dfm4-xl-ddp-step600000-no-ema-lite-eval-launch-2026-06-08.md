---
type: Operational Record
title: DFM4 XL-DDP step600000 no-EMA lite eval launch (2026-06-08)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM4 XL-DDP step600000
  no-EMA lite eval launch (2026-06-08).'
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
# DFM4 XL-DDP step600000 no-EMA lite eval launch (2026-06-08)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM4 XL-DDP `step_600000` no-EMA lite eval launch, 2026-06-08. Confidence:
high for local checkpoint state and launch status. The checkpoint exists as an
unsharded checkpoint with carry files, and `checkpoint_state_step_600000.json`
reports `step=600000`, `epoch=2`, `batch_in_epoch=232753`,
`global_batch_size=196608`, and `data_path=data/sampled_dfm4`.

The W&B epoch x-value uses the same epoch-1 boundary (`367247`) as the earlier
DFM4 XL-DDP lite points:

```text
step_600000 -> 1.6337778116635397
```

Launched in tmux window `dfm4_lite_eval:noema_600k`, syncing to W&B run
`dfm4xlddpclean` under `lite_eval_noema/*` and `lite_dfm_eval_noema/*`, with
the same conservative lanes used for the successful `500K/550K` run:

```text
LOG_ROOT_BASE=logs/eval/dfm4_XL_ddp_noema_lite_600k_20260608_tmux
DFM_LOG_ROOT_BASE=logs/dfm_evals/dfm4_XL_ddp_noema_lite_600k_20260608_tmux
CKPT_TAGS=step_600000
EVAL_EPOCHS=1.6337778116635397
GPUS=0,2,7
JUDGE_GPU=0
NO_EMA=1
STANDARD_BATCH_SIZE=1
DFM_BATCH_SIZE=1
IFEVAL_BATCH_SIZE=1
```

Initial status:

```text
QUEUED 19 jobs for 1 checkpoints
START step_600000 dfm_ifeval 0 shard_0_of_32 gpu_0
START step_600000 standard MATH shard_0_of_64 gpu_7
START step_600000 standard GSM8k shard_0_of_8 gpu_2
```
