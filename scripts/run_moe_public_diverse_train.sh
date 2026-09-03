#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f pyproject.toml || ! -f pretrain.py ]]; then
  echo "Run this launcher from the HRM-Text repository root." >&2
  exit 2
fi

NPROC_PER_NODE="${NPROC_PER_NODE:-8}"
ARCH_SIZE="${ARCH_SIZE:-XL}"
TOKENS_PER_FAMILY="${TOKENS_PER_FAMILY:-100000000}"
GLOBAL_BATCH_SIZE="${GLOBAL_BATCH_SIZE:-8192}"
LR="${LR:-2.2e-4}"
LR_WARMUP_STEPS="${LR_WARMUP_STEPS:-500}"
CHECKPOINT_STEP_INTERVAL="${CHECKPOINT_STEP_INTERVAL:-10000}"
MOE_NUM_EXPERTS="${MOE_NUM_EXPERTS:-8}"
MOE_TOP_K="${MOE_TOP_K:-2}"
MOE_EXPERT_EXPANSION_SCALE="${MOE_EXPERT_EXPANSION_SCALE:-0.5}"
RUN_ID="${RUN_ID:-hrm-moe-public10-e${MOE_NUM_EXPERTS}k${MOE_TOP_K}-${ARCH_SIZE}-$(date +%Y%m%d-%H%M%S)}"
RUN_ROOT="hrm-moe-runs/$RUN_ID"
DATA_ROOT="$RUN_ROOT/data"

mkdir -p hrm-moe-runs
mkdir "$RUN_ROOT"
mkdir "$RUN_ROOT/logs" "$RUN_ROOT/results" "$RUN_ROOT/checkpoints" "$RUN_ROOT/work"

printf 'Run root: %s\n' "$RUN_ROOT"
printf 'Architecture: %s; experts: %s; top-k: %s; expert scale: %s\n' \
  "$ARCH_SIZE" "$MOE_NUM_EXPERTS" "$MOE_TOP_K" "$MOE_EXPERT_EXPANSION_SCALE"
printf 'Public data target: %s tokens x 10 families\n' "$TOKENS_PER_FAMILY"

python scripts/prepare_moe_public_diverse.py \
  --output "$DATA_ROOT" \
  --work-dir "$RUN_ROOT/work" \
  --tokens-per-family "$TOKENS_PER_FAMILY" \
  --max-sequence-tokens 1025 \
  --epochs 1 \
  2>&1 | tee "$RUN_ROOT/logs/data-preparation.log"

python scripts/validate_moe_pilot.py \
  "$DATA_ROOT" \
  --receipt "$RUN_ROOT/results/data-validation.json" \
  2>&1 | tee "$RUN_ROOT/logs/data-validation.log"

TOTAL_TOKENS="$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["total_length"])' "$DATA_ROOT/metadata.json")"
MAX_STEPS="${MAX_STEPS:-$(( TOTAL_TOKENS / GLOBAL_BATCH_SIZE ))}"
if (( MAX_STEPS < 1 )); then
  echo "Computed zero optimizer steps from $TOTAL_TOKENS tokens." >&2
  exit 2
fi
printf 'Validated tokens: %s; optimizer steps: %s; global batch: %s\n' \
  "$TOTAL_TOKENS" "$MAX_STEPS" "$GLOBAL_BATCH_SIZE"

BENCH_OUTPUT="$RUN_ROOT/results/summary.json" \
OMP_NUM_THREADS=1 \
MKL_NUM_THREADS=1 \
torchrun --nproc_per_node="$NPROC_PER_NODE" pretrain.py \
  arch/net@arch=hrm_moe \
  arch/size@arch="$ARCH_SIZE" \
  arch.bp_warmup_ratio=0.2 \
  arch.moe_num_experts="$MOE_NUM_EXPERTS" \
  arch.moe_top_k="$MOE_TOP_K" \
  arch.moe_expert_expansion_scale="$MOE_EXPERT_EXPANSION_SCALE" \
  data=moe_pilot \
  data.path="$DATA_ROOT" \
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
  moe_collapse_warmup_steps=100 \
  wandb_enabled=false \
  local_metrics_path="$RUN_ROOT/results/metrics.jsonl" \
  checkpoint_step_interval="$CHECKPOINT_STEP_INTERVAL" \
  checkpoint_format=unsharded \
  checkpoint_path="$RUN_ROOT/checkpoints" \
  project_name=HRM-MoE-Public10 \
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

printf 'Completed public ten-family HRM-MoE run: %s\n' "$RUN_ROOT"
