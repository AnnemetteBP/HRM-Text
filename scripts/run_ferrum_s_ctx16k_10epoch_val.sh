#!/usr/bin/env bash
set -euo pipefail

cd /work/dfm/HRM-Text

RUN_ID="${RUN_ID:-ferrum-strategy-s-ctx16k-10epoch-val-$(date +%Y%m%d-%H%M%S)}"
LOG="logs/${RUN_ID}.log"
CKPT="checkpoints/ferrum_strategy_s/${RUN_ID}"
MASTER_PORT="${MASTER_PORT:-29645}"

mkdir -p logs checkpoints/ferrum_strategy_s

echo "RUN_ID=${RUN_ID}"
echo "LOG=/work/dfm/HRM-Text/${LOG}"
echo "CKPT=/work/dfm/HRM-Text/${CKPT}"
echo "WANDB=https://wandb.ai/peter-sk-sdu/Ferrum/runs/${RUN_ID}"
echo "MASTER_PORT=${MASTER_PORT}"

env WANDB_MODE=online OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  /work/dfm/.home/miniforge3/envs/hrm/bin/torchrun \
  --nproc_per_node=8 \
  --master_port="${MASTER_PORT}" \
  pretrain.py \
  arch/size@arch=S \
  data.path=data/sampled_ferrum_strategy_xxs_ctx16k_train \
  +data.validation_path=data/sampled_ferrum_strategy_xxs_ctx16k_validation \
  +data.target_only=true \
  accelerator_type=sm100 \
  distributed_strategy=fsdp \
  compile_train_batch=false \
  fwd_bwd_dtype=bfloat16 \
  global_batch_size=131072 \
  gradient_accumulation_steps=1 \
  epochs=10 \
  checkpoint_path="${CKPT}" \
  checkpoint_interval=1 \
  checkpoint_step_interval=500 \
  checkpoint_format=sharded \
  project_name=Ferrum \
  run_name="${RUN_ID}" \
  wandb_run_id="${RUN_ID}" \
  wandb_resume=allow \
  log_interval=10 \
  +validation_interval=250 \
  +validation_batches=10 \
  lr_warmup_steps=100 \
  lr=2e-4 \
  lr_min_ratio=1.0 \
  weight_decay=0.1 \
  beta1=0.9 \
  beta2=0.95 \
  ema=null 2>&1 | tee -a "${LOG}"
