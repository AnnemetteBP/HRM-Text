---
type: Plan Record
title: DFM8 L Resume On 2026-08-01
description: 'Part of DFM8 Plan: DFM8 L Resume On 2026-08-01.'
tags:
- dfm8
- data
- synthetic-data
- training
- evaluation
status: stable
last_updated: 2026-07-12
confidence: medium
part_of: /pages/dfm8-plan.md
---
# DFM8 L Resume On 2026-08-01

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Update, 2026-08-01. Confidence: high from inspected checkpoint sidecars,
process state, and live training output.

The DFM8 XXL one-epoch scheduler campaign was stopped before switching models.
Its latest fully written checkpoint at the time of the stop was
`checkpoints/dfm8/XXL-1epoch/fsdp2_ephemeral_step_151000`. The scheduler plan
`logs/scheduler/dfm8_XXL_1epoch_steps50k_100k_persistent_vllm_20260725` retains
its stop request and must not be resumed unintentionally.

The DFM8 L run was resumed from the complete sharded checkpoint
`checkpoints/dfm8/L-gbs131072/fsdp2_step_100000` in W&B run `g2oaotmc`
(`DFM5` / `DFM8-L-gbs131072`). Despite the historical `L-gbs131072` name,
both `all_config.yaml` and `checkpoint_state_step_100000.json` specify
`global_batch_size=262144` and `gradient_accumulation_steps=1`; these
authoritative values must be preserved on resume. The checkpoint sidecar gives
`step=100000`, `epoch=1`, and exact `batch_in_epoch=100000`.

The verified resume command is:

```bash
cd /work/dfm/HRM-Text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 torchrun --nproc_per_node=8 pretrain.py \
  data=dfm8 \
  arch/size@arch=L \
  lr=3e-4 \
  lr_min_ratio=1 \
  lr_warmup_steps=2000 \
  weight_decay=0.1 \
  beta1=0.9 \
  beta2=0.95 \
  ema=0.9999 \
  global_batch_size=262144 \
  gradient_accumulation_steps=1 \
  epochs=1 \
  distributed_strategy=fsdp \
  fsdp_params_precision=fp32 \
  checkpoint_format=sharded \
  fwd_bwd_dtype=bfloat16 \
  accelerator_type=sm100 \
  compile_train_batch=true \
  checkpoint_interval=1 \
  checkpoint_step_interval=10000 \
  ephemeral_checkpoint_step_interval=1000 \
  checkpoint_path=checkpoints/dfm8/L-gbs131072 \
  resume_checkpoint_path=checkpoints/dfm8/L-gbs131072 \
  resume_checkpoint_tag=step_100000 \
  reset_ema_on_resume=false \
  upcast_optimizer_state_on_resume=false \
  project_name=DFM5 \
  run_name=DFM8-L-gbs131072 \
  wandb_run_id=g2oaotmc \
  wandb_resume=allow
```

The process was launched in tmux pane `%146` (currently window `hrm-0:4`) and
was verified advancing beyond step 100079 with all eight GPUs active. W&B had
already received history through step 100079 from an earlier attempt, so resumed
points at or below that tail were rejected as out of order; normal logging
resumed after the process passed that point.

Superseded later on 2026-08-01: the uninterrupted manual resume was stopped
after the complete `ephemeral_step_101000` checkpoint so that training and
evaluation could be orchestrated by one scheduler campaign. Its W&B history had
advanced to step 101366, so the scheduler-managed resume intentionally replays
steps 101001-101366 without logging duplicate W&B points.
