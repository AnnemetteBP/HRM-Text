#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f pyproject.toml || ! -f pretrain.py ]]; then
  echo "Run this launcher from the HRM-Text repository root." >&2
  exit 2
fi

DATA_PATH="${DFM9_MINI_PATH:-}"
if [[ -z "$DATA_PATH" ]]; then
  for candidate in \
    /dfm/HRM-Text/data/sampled_dfm9_mini \
    /work/dfm/HRM-Text/data/sampled_dfm9_mini \
    data/sampled_dfm9_mini
  do
    if [[ -f "$candidate/metadata.json" ]]; then
      DATA_PATH="$candidate"
      break
    fi
  done
fi

if [[ -z "$DATA_PATH" || ! -f "$DATA_PATH/metadata.json" ]]; then
  echo "DFM9-mini was not found; set DFM9_MINI_PATH to sampled_dfm9_mini." >&2
  exit 2
fi

for required in \
  tokens.npy \
  epoch_0/inst_start.npy \
  epoch_0/inst_len.npy \
  epoch_0/resp_start.npy \
  epoch_0/resp_len.npy
do
  if [[ ! -f "$DATA_PATH/$required" ]]; then
    echo "DFM9-mini is incomplete: missing $DATA_PATH/$required" >&2
    exit 2
  fi
done

NPROC_PER_NODE="${NPROC_PER_NODE:-8}"
ARCH_SIZE="${ARCH_SIZE:-B}"
GLOBAL_BATCH_SIZE="${GLOBAL_BATCH_SIZE:-196608}"
TOKEN_BUDGET="${TOKEN_BUDGET:-1000000000}"
MAX_STEPS="${MAX_STEPS:-$(( (TOKEN_BUDGET + GLOBAL_BATCH_SIZE - 1) / GLOBAL_BATCH_SIZE ))}"
LR="${LR:-2.2e-4}"
LR_WARMUP_STEPS="${LR_WARMUP_STEPS:-200}"
CHECKPOINT_STEP_INTERVAL="${CHECKPOINT_STEP_INTERVAL:-500}"
RUN_ID="${RUN_ID:-hrm-moe-dfm9-mini-e8k2-${ARCH_SIZE}-$(date +%Y%m%d-%H%M%S)}"
RUN_ROOT="hrm-moe-runs/$RUN_ID"

mkdir -p hrm-moe-runs
mkdir "$RUN_ROOT"
mkdir "$RUN_ROOT/logs" "$RUN_ROOT/results" "$RUN_ROOT/checkpoints"

printf 'Run root: %s\n' "$RUN_ROOT"
printf 'Read-only data: %s\n' "$DATA_PATH"
printf 'Token budget: %s; optimizer steps: %s\n' "$TOKEN_BUDGET" "$MAX_STEPS"

BENCH_OUTPUT="$RUN_ROOT/results/summary.json" \
OMP_NUM_THREADS=1 \
MKL_NUM_THREADS=1 \
torchrun --nproc_per_node="$NPROC_PER_NODE" pretrain.py \
  arch/net@arch=hrm_moe \
  arch/size@arch="$ARCH_SIZE" \
  arch.bp_warmup_ratio=0.2 \
  data=dfm9_mini \
  data.path="$DATA_PATH" \
  accelerator_type=sm100 \
  distributed_strategy=ddp \
  ddp_params_precision=fp32 \
  fwd_bwd_dtype=bfloat16 \
  compile_train_batch=false \
  activation_checkpointing=full \
  ema=0.9999 \
  global_batch_size="$GLOBAL_BATCH_SIZE" \
  epochs=1 \
  lr="$LR" \
  lr_min_ratio=1.0 \
  lr_warmup_steps="$LR_WARMUP_STEPS" \
  max_steps="$MAX_STEPS" \
  stop_after_step="$MAX_STEPS" \
  log_interval=1 \
  moe_collapse_max_load=0.30 \
  moe_collapse_min_load=0.01 \
  moe_collapse_patience=20 \
  moe_collapse_warmup_steps=50 \
  wandb_enabled=false \
  local_metrics_path="$RUN_ROOT/results/metrics.jsonl" \
  checkpoint_step_interval="$CHECKPOINT_STEP_INTERVAL" \
  checkpoint_format=unsharded \
  checkpoint_path="$RUN_ROOT/checkpoints" \
  project_name=HRM-MoE-DFM9-Mini \
  run_name="$RUN_ID" \
  2>&1 | tee "$RUN_ROOT/logs/train.log"

python -m json.tool "$RUN_ROOT/results/summary.json" \
  > "$RUN_ROOT/results/summary.pretty.json"

if python -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1])).get("stopped_for_moe_collapse") else 1)' "$RUN_ROOT/results/summary.json"
then
  echo "Training stopped because the MoE collapse guard fired: $RUN_ROOT" >&2
  exit 3
fi

if python -c 'import matplotlib' >/dev/null 2>&1; then
  python scripts/plot_moe_training.py "$RUN_ROOT"
fi

printf 'Completed HRM-MoE DFM9-mini run: %s\n' "$RUN_ROOT"
