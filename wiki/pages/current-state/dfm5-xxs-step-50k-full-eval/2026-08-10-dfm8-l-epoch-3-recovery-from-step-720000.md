---
type: Operational Record
title: 2026-08-10 DFM8 L Epoch 3 Recovery From Step 720000
description: 'Part of DFM5 XXS Step-50K Full Eval: 2026-08-10 DFM8 L Epoch 3 Recovery
  From Step 720000.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# 2026-08-10 DFM8 L Epoch 3 Recovery From Step 720000

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Confidence: high (verified checkpoint contents, scheduler state, live process
tree, W&B API access, and post-resume optimizer progress).

The interrupted `campaign-train-750000` segment had failed with an NCCL
all-reduce watchdog timeout. The newest complete checkpoint was the regular
`checkpoints/dfm8/L-gbs131072/fsdp2_step_720000` checkpoint: it contains
`.metadata`, all eight `*.distcp` shards, all eight carry files, and
`checkpoint_state_step_720000.json`. The sidecar records exact batch resume
state for epoch 3 at global step 720000.

A replacement scheduler row named
`campaign-train-750000-resume720000` was added to
`logs/scheduler/dfm8_L_campaign_epoch2_20260803/plan.tsv`. It resumes from
`step_720000`, stops at `step_750000`, uses the original DFM8 L training
configuration, and allows three retries. The original failed row remains as
historical evidence and does not block the replacement chain; the existing
`wait_checkpoint step_750000` row will release the normal evaluation and
subsequent training jobs when the replacement writes the checkpoint.

The fresh host initially lacked `/home/ucloud/.netrc`, so the first replacement
attempts stopped during `wandb.init` before taking an optimizer step. W&B login
was restored and API access to `DFM5/g2oaotmc` was verified before relaunch.
The scheduler now runs detached with the required `hrm` PATH and persistent
vLLM:

```bash
cd /work/dfm/HRM-Text
PATH="/home/ucloud/miniforge3/envs/hrm/bin:$PATH" \
setsid /home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm8_L_campaign_epoch2_20260803 \
  --gpus 0,1,2,3,4,5,6,7 \
  --persistent-vllm \
  >> logs/scheduler/dfm8_L_campaign_epoch2_20260803/runner_epoch3_resume720000_20260810.log 2>&1 < /dev/null &
```

The live tmux layout in `hrm-0` is:

- window 3, `training`: follows the newest log under
  `logs/training/dfm8_L_epoch3`;
- window 4, `monitor`: Rich scheduler monitor at a 30-second interval.

The resumed process reported `step=720000`, `start_epoch=3`,
`skip_batches=182700`, and began advancing optimizer steps with all eight GPUs
at 100% utilization. W&B had already received history through step 720961 from
the interrupted process, so replayed train logs below that point are correctly
rejected as non-monotonic; new training metrics resume once the process passes
step 720961.
