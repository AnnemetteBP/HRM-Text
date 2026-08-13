---
type: Operational Record
title: Superseding launch update (2026-06-07)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Superseding launch
  update (2026-06-07).'
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
# Superseding launch update (2026-06-07)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Superseding launch update, 2026-06-07. Confidence: high for local command and
initial status. A no-EMA lite eval for the current DFM4 XL-DDP `step_500000`
and `step_550000` checkpoints was launched in tmux window
`dfm4_lite_eval:noema_500_550`, syncing to W&B run `dfm4xlddpclean` under
`lite_eval_noema/*` and `lite_dfm_eval_noema/*`. It uses three eval lanes
around the active training memory:

```text
GPUS=0,2,7
JUDGE_GPU=0
STANDARD_BATCH_SIZE=1
DFM_BATCH_SIZE=1
IFEVAL_BATCH_SIZE=1
```

The W&B epoch x-values are:

```text
step_500000 -> 1.3614815097196165
step_550000 -> 1.4976296606915782
```

Log roots:

```text
logs/eval/dfm4_XL_ddp_noema_lite_500k_550k_20260607_tmux
logs/dfm_evals/dfm4_XL_ddp_noema_lite_500k_550k_20260607_tmux
```

Initial status at launch:

```text
QUEUED 38 jobs for 2 checkpoints
START step_500000 dfm_ifeval 0 shard_0_of_32 gpu_0
START step_500000 standard MATH shard_0_of_64 gpu_2
START step_500000 standard GSM8k shard_0_of_8 gpu_7
```

Early check: `step_500000` GSM8k shard completed and merged at
`2026-06-07T15:03:40+02:00`; `MATH` and `IFEval-DA` were still running.
