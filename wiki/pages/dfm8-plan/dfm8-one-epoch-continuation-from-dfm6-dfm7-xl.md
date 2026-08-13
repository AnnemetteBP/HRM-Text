---
type: Plan Record
title: DFM8 One-Epoch Continuation From DFM6/DFM7 XL
description: 'Part of DFM8 Plan: DFM8 One-Epoch Continuation From DFM6/DFM7 XL.'
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
# DFM8 One-Epoch Continuation From DFM6/DFM7 XL

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Update, 2026-07-14. Confidence: high from local checkpoint metadata and
sampled-data metadata inspection.

The finished DFM6/DFM7 XL checkpoint to continue from is:

```text
checkpoints/dfm7/XL-gas2-from-dfm6-epoch3/checkpoint_state_epoch_5.json
```

Its exact resume state is:

```json
{
  "tag": "epoch_5",
  "step": 1229504,
  "epoch": 5,
  "batch_in_epoch": 0,
  "batch_in_epoch_exact": true
}
```

DFM8 has `70,479,308,606` sampled tokens per epoch. With
`global_batch_size=262144`, this is `268,857` optimizer steps per epoch by the
training loop's floor division. Training one DFM8 epoch on top of the finished
DFM6/DFM7 checkpoint should therefore start at step `1,229,504` and finish at
about step `1,498,361`.

Use `resume_checkpoint_tag=epoch_5` and `epochs=6`. The epoch-tag resume path
starts at `tag_epoch + 1`, so this trains only the sixth configured epoch, which
corresponds to DFM8 sampled epoch index `5`, and then writes `epoch_6` under the
DFM8 checkpoint path.

```bash
cd /work/dfm/HRM-Text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 torchrun --nproc_per_node=8 pretrain.py \
  data=dfm8 \
  arch/size@arch=XL \
  lr=3e-4 \
  lr_min_ratio=1 \
  lr_warmup_steps=2000 \
  weight_decay=0.1 \
  beta1=0.9 \
  beta2=0.95 \
  ema=0.9999 \
  global_batch_size=262144 \
  gradient_accumulation_steps=2 \
  epochs=6 \
  distributed_strategy=fsdp \
  fsdp_params_precision=fp32 \
  checkpoint_format=sharded \
  fwd_bwd_dtype=bfloat16 \
  accelerator_type=sm100 \
  compile_train_batch=true \
  checkpoint_interval=1 \
  checkpoint_step_interval=10000 \
  ephemeral_checkpoint_step_interval=500 \
  checkpoint_path=checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5 \
  resume_checkpoint_path=checkpoints/dfm7/XL-gas2-from-dfm6-epoch3 \
  resume_checkpoint_tag=epoch_5 \
  resume_step=1229504 \
  resume_epoch=5 \
  reset_ema_on_resume=false \
  upcast_optimizer_state_on_resume=false \
  project_name=DFM5 \
  run_name="DFM8-XL clean full from DFM6-DFM7 epoch5" \
  wandb_run_id=dfm8-xl-from-dfm6-dfm7-epoch5-clean-full \
  wandb_resume=allow
```
