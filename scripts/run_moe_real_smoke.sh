#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f pyproject.toml || ! -f pretrain.py ]]; then
  echo "Run this launcher from the HRM-Text repository root." >&2
  exit 2
fi

NPROC_PER_NODE="${NPROC_PER_NODE:-8}"
TOKENS_PER_DOMAIN="${TOKENS_PER_DOMAIN:-500000}"
MAX_STEPS="${MAX_STEPS:-20}"
ARCH_SIZE="${ARCH_SIZE:-XXS}"
BP_WARMUP_RATIO="${BP_WARMUP_RATIO:-0.0}"
ACTIVATION_CHECKPOINTING="${ACTIVATION_CHECKPOINTING:-none}"
CHECKPOINT_STEP_INTERVAL="${CHECKPOINT_STEP_INTERVAL:-$MAX_STEPS}"
MOE_DATA_PATH="${MOE_DATA_PATH:-}"
MOE_COLLAPSE_MAX_LOAD="${MOE_COLLAPSE_MAX_LOAD:-0.45}"
MOE_COLLAPSE_MIN_LOAD="${MOE_COLLAPSE_MIN_LOAD:-0.01}"
MOE_COLLAPSE_PATIENCE="${MOE_COLLAPSE_PATIENCE:-20}"
MOE_COLLAPSE_WARMUP_STEPS="${MOE_COLLAPSE_WARMUP_STEPS:-20}"
RUN_ID="${RUN_ID:-hrm-moe-open-euro-e4-b200-smoke-$(date +%Y%m%d-%H%M%S)}"
RUN_ROOT="hrm-moe-runs/$RUN_ID"
DATA_ROOT="${MOE_DATA_PATH:-$RUN_ROOT/data}"

mkdir -p hrm-moe-runs
mkdir "$RUN_ROOT"
mkdir "$RUN_ROOT/logs" "$RUN_ROOT/results" "$RUN_ROOT/checkpoints" "$RUN_ROOT/work"
printf 'HRM-MoE smoke run: %s\n' "$RUN_ROOT"

if [[ -n "$MOE_DATA_PATH" ]]; then
  if [[ ! -f "$DATA_ROOT/metadata.json" ]]; then
    echo "MOE_DATA_PATH does not contain metadata.json: $DATA_ROOT" >&2
    exit 2
  fi
  printf 'Reusing read-only MoE data: %s\n' "$DATA_ROOT" \
    | tee "$RUN_ROOT/logs/data-preparation.log"
else
  python scripts/prepare_moe_real_pilot.py \
    --output "$DATA_ROOT" \
    --work-dir "$RUN_ROOT/work" \
    --tokens-per-domain "$TOKENS_PER_DOMAIN" \
    --max-sequence-tokens 1025 \
    --epochs 1 \
    2>&1 | tee "$RUN_ROOT/logs/data-preparation.log"
fi

python scripts/validate_moe_pilot.py \
  "$DATA_ROOT" \
  --receipt "$RUN_ROOT/results/data-validation.json" \
  2>&1 | tee "$RUN_ROOT/logs/data-validation.log"

BENCH_OUTPUT="$RUN_ROOT/results/summary.json" \
OMP_NUM_THREADS=1 \
MKL_NUM_THREADS=1 \
torchrun --nproc_per_node="$NPROC_PER_NODE" pretrain.py \
  arch/net@arch=hrm_moe \
  arch/size@arch="$ARCH_SIZE" \
  arch.bp_warmup_ratio="$BP_WARMUP_RATIO" \
  data=moe_pilot \
  data.path="$DATA_ROOT" \
  accelerator_type=sm100 \
  distributed_strategy=ddp \
  ddp_params_precision=fp32 \
  fwd_bwd_dtype=bfloat16 \
  compile_train_batch=false \
  activation_checkpointing="$ACTIVATION_CHECKPOINTING" \
  ema=null \
  global_batch_size=8192 \
  epochs=1 \
  lr=2.2e-4 \
  lr_min_ratio=1.0 \
  lr_warmup_steps=10 \
  max_steps="$MAX_STEPS" \
  log_interval=1 \
  moe_collapse_max_load="$MOE_COLLAPSE_MAX_LOAD" \
  moe_collapse_min_load="$MOE_COLLAPSE_MIN_LOAD" \
  moe_collapse_patience="$MOE_COLLAPSE_PATIENCE" \
  moe_collapse_warmup_steps="$MOE_COLLAPSE_WARMUP_STEPS" \
  wandb_enabled=false \
  local_metrics_path="$RUN_ROOT/results/metrics.jsonl" \
  checkpoint_step_interval="$CHECKPOINT_STEP_INTERVAL" \
  checkpoint_format=unsharded \
  checkpoint_path="$RUN_ROOT/checkpoints" \
  project_name=HRM-MoE-Smokes \
  run_name="$RUN_ID" \
  2>&1 | tee "$RUN_ROOT/logs/train.log"

python -m json.tool "$RUN_ROOT/results/summary.json" \
  | tee "$RUN_ROOT/results/summary.pretty.json"

printf 'Completed HRM-MoE smoke: %s\n' "$RUN_ROOT"
