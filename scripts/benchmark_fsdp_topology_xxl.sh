#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-/work/dfm/HRM-Text}"
PYTHON_ENV="${PYTHON_ENV:-/home/ucloud/miniforge3/envs/hrm}"
OUT="${OUT:-$ROOT/logs/benchmarks/fsdp_hsdp_xxl}"
SOURCE_CHECKPOINT="${SOURCE_CHECKPOINT:-$ROOT/checkpoints/dfm8/XXL-1epoch}"
SOURCE_TAG="${SOURCE_TAG:-ephemeral_step_161000}"
SOURCE_STEP="${SOURCE_STEP:-161000}"
TIMED_STEPS="${TIMED_STEPS:-6}"

mkdir -p "$OUT"

run_case() {
  local name="$1"
  local world_size="$2"
  local gas="$3"
  local shard_degree="$4"
  local reshard="$5"
  local sync_mode="${6:-no_sync}"
  local case_dir="$OUT/$name"
  mkdir -p "$case_dir"
  echo "Running $name: world=$world_size gas=$gas shard_degree=$shard_degree reshard=$reshard sync_mode=$sync_mode"
  WANDB_MODE=disabled \
  BENCH_OUTPUT="$case_dir/bench.json" \
  OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    "$PYTHON_ENV/bin/torchrun" --nproc_per_node="$world_size" "$ROOT/pretrain.py" \
      data=dfm8 arch/size@arch=XXL \
      lr=4e-4 lr_min_ratio=1 lr_warmup_steps=2000 \
      weight_decay=0.1 beta1=0.9 beta2=0.95 ema=0.9999 \
      global_batch_size=262144 gradient_accumulation_steps="$gas" epochs=1 \
      distributed_strategy=fsdp fsdp_params_precision=fp32 \
      fsdp_shard_degree="$shard_degree" \
      fsdp_reshard_after_forward="$reshard" \
      fsdp_accumulation_sync_mode="$sync_mode" \
      activation_checkpointing=full compile_train_batch=false \
      checkpoint_format=sharded fwd_bwd_dtype=bfloat16 accelerator_type=sm100 \
      checkpoint_path="$case_dir/checkpoint" \
      resume_checkpoint_path="$SOURCE_CHECKPOINT" \
      resume_checkpoint_tag="$SOURCE_TAG" \
      max_steps="$((SOURCE_STEP + TIMED_STEPS))" \
      benchmark_state_fingerprint=true memory_log_interval=1 log_interval=1 \
      project_name=disabled run_name="$name" \
      > "$case_dir/train.log" 2>&1
}

# Same world and effective batch: topology and resharding parity/timing.
run_case degree8_auto 8 4 8 null
run_case degree8_no_reshard 8 4 8 false
run_case degree4_auto 8 4 4 null
run_case degree4_no_reshard 8 4 4 false
run_case degree2_auto 8 4 2 null
run_case degree2_no_reshard 8 4 2 false
run_case degree4_reduce_scatter 8 4 4 null reduce_scatter
run_case degree2_reduce_scatter 8 4 2 null reduce_scatter

# Same 262K-token optimizer batch under different accumulation/world sizes.
run_case degree8_gas1 8 1 8 null
run_case world4_degree4_gas8 4 8 4 null
run_case world2_degree2_gas16 2 16 2 null

"$PYTHON_ENV/bin/python" "$ROOT/scripts/summarize_fsdp_topology_benchmark.py" "$OUT"
