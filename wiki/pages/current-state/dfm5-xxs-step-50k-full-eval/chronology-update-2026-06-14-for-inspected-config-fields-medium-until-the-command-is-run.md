---
type: Operational Record
title: 'Update 2026-06-14: for inspected config fields; medium until the command is
  run'
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Update 2026-06-14:
  for inspected config fields; medium until the command is run.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# Update 2026-06-14: for inspected config fields; medium until the command is run

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-06-14. Confidence: high for inspected config fields; medium until
the command is run. A comparable DDP variant of the DFM5 XXS training command
should keep the same data, architecture, LR, global batch, epoch count, and
checkpoint cadence, but switch to `distributed_strategy=ddp`, use
`checkpoint_format=unsharded`, and write to a separate checkpoint directory.
For precision comparability with the FSDP2 path, use
`ddp_params_precision=fp32` with `fwd_bwd_dtype=bfloat16`; the alternative
`ddp_params_precision=bf16` is lower-memory/higher-throughput but changes
persistent parameter precision.

```bash
cd /work/dfm/HRM-Text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
torchrun --nproc_per_node=8 pretrain.py \
  data=dfm5 \
  arch/size@arch=XXS \
  lr=2.5e-4 \
  global_batch_size=196608 \
  gradient_accumulation_steps=1 \
  epochs=5 \
  distributed_strategy=ddp \
  ddp_params_precision=fp32 \
  ddp_find_unused_parameters=true \
  checkpoint_format=unsharded \
  fwd_bwd_dtype=bfloat16 \
  accelerator_type=sm100 \
  checkpoint_interval=1 \
  checkpoint_step_interval=10000 \
  ephemeral_checkpoint_step_interval=1000 \
  checkpoint_path=checkpoints/dfm5/XXS-ddp \
  project_name="DFM5" \
  run_name=dfm5-XXS-ddp
```
