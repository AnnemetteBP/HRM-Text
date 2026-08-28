#!/usr/bin/env bash
set -euo pipefail

ROOT=/work/dfm/HRM-Text
MAIN_COMMIT=$(git -C "$ROOT" rev-parse main)
PERFORMANCE_COMMIT=$(git -C "$ROOT" rev-parse HEAD)
MAIN_WORKTREE=/tmp/hrm-main-benchmark-${MAIN_COMMIT:0:12}
PERFORMANCE_WORKTREE=/tmp/hrm-performance-benchmark-${PERFORMANCE_COMMIT:0:12}
OUTPUT_ROOT=/tmp/hrm_fa4_grad_mask_100step
HRM_PYTHON=/home/ucloud/miniforge3/envs/hrm/bin/python
HRM_TORCHRUN=/home/ucloud/miniforge3/envs/hrm/bin/torchrun

mkdir -p "$OUTPUT_ROOT"
exec 9>"$OUTPUT_ROOT/benchmark.lock"
flock -n 9 || { echo "Another FA4 gradient-mask benchmark is already running."; exit 1; }

if [[ ! -e "$MAIN_WORKTREE/.git" ]]; then
  git -C "$ROOT" worktree add --detach "$MAIN_WORKTREE" "$MAIN_COMMIT"
fi
if [[ ! -e "$MAIN_WORKTREE/data" ]]; then
  ln -s "$ROOT/data" "$MAIN_WORKTREE/data"
fi

git -C "$ROOT" diff -- \
  models/flash_attention_prefixlm_dispatch.py \
  models/flash_attention_prefixlm_fa4.py \
  models/flash_attention_prefixlm_v2.py \
  models/layers.py \
  models/transformer.py \
  tests/test_flash_attention_prefixlm_bounds.py \
  > "$OUTPUT_ROOT/performance_changes.patch"
if [[ ! -e "$PERFORMANCE_WORKTREE/.git" ]]; then
  git -C "$ROOT" worktree add --detach "$PERFORMANCE_WORKTREE" "$PERFORMANCE_COMMIT"
  git -C "$PERFORMANCE_WORKTREE" apply "$OUTPUT_ROOT/performance_changes.patch"
fi
if [[ ! -e "$PERFORMANCE_WORKTREE/data" ]]; then
  ln -s "$ROOT/data" "$PERFORMANCE_WORKTREE/data"
fi

{
  printf 'main_commit='
  printf '%s\n' "$MAIN_COMMIT"
  printf 'performance_commit='
  printf '%s\n' "$PERFORMANCE_COMMIT"
} > "$OUTPUT_ROOT/source_state.txt"

foreign_gpu_processes() {
  nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null \
    | sed '/^[[:space:]]*$/d' \
    | wc -l
}

echo "Waiting for all eight GPUs to have no foreign compute processes..."
idle_polls=0
while [[ "$idle_polls" -lt 3 ]]; do
  if [[ "$(foreign_gpu_processes)" -eq 0 ]]; then
    idle_polls=$((idle_polls + 1))
    echo "[$(date -Is)] Idle GPU poll $idle_polls/3"
  else
    idle_polls=0
  fi
  date -Is
  nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
  sleep 30
done

COMMON_OVERRIDES=(
  data=dfm8
  arch/size@arch=XXL
  +arch.bp_min_steps=5
  arch.bp_max_steps=5
  arch.bp_warmup_ratio=0.2
  lr=4e-4
  lr_min_ratio=1
  lr_warmup_steps=2000
  weight_decay=0.1
  beta1=0.9
  beta2=0.95
  ema=0.9999
  global_batch_size=262144
  gradient_accumulation_steps=4
  epochs=1
  distributed_strategy=fsdp
  fsdp_params_precision=fp32
  checkpoint_format=sharded
  fwd_bwd_dtype=bfloat16
  accelerator_type=sm100
  compile_train_batch=true
  checkpoint_interval=1
  checkpoint_step_interval=null
  ephemeral_checkpoint_step_interval=null
  activation_checkpointing=none
  fsdp_shard_degree=null
  fsdp_reshard_after_forward=false
  fsdp_accumulation_sync_mode=no_sync
  max_steps=100
  benchmark_state_fingerprint=true
  stop_after_step=null
  wandb_run_id=null
  wandb_resume=never
  log_interval=1
)

run_one() {
  local worktree=$1
  local label=$2
  shift 2
  local output="$OUTPUT_ROOT/$label"
  mkdir -p "$output"
  echo "[$(date -Is)] Starting $label in $worktree"
  (
    cd "$worktree"
    WANDB_MODE=disabled \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    PATH="/home/ucloud/miniforge3/envs/hrm/bin:$PATH" \
    BENCH_OUTPUT="$output/summary.json" \
    "$HRM_TORCHRUN" --nproc_per_node=8 pretrain.py \
      "${COMMON_OVERRIDES[@]}" \
      checkpoint_path="$output/checkpoints" \
      project_name="fa4-grad-mask-benchmark-disabled" \
      run_name="$label" \
      "$@"
  ) 2>&1 | tee "$output/train.log"
  echo "[$(date -Is)] Finished $label"
}

run_one "$MAIN_WORKTREE" main
run_one "$PERFORMANCE_WORKTREE" seqused_eager \
  +arch.prefixlm_fa4_impl=seqused \
  +arch.prefixlm_fa4_grad_mask_impl=eager
run_one "$PERFORMANCE_WORKTREE" seqused_triton \
  +arch.prefixlm_fa4_impl=seqused \
  +arch.prefixlm_fa4_grad_mask_impl=triton
run_one "$PERFORMANCE_WORKTREE" seqused_eager_repeat \
  +arch.prefixlm_fa4_impl=seqused \
  +arch.prefixlm_fa4_grad_mask_impl=eager

"$HRM_PYTHON" - "$OUTPUT_ROOT" <<'PY' | tee "$OUTPUT_ROOT/comparison.txt"
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
labels = ("main", "seqused_eager", "seqused_triton", "seqused_eager_repeat")
summaries = {
    label: json.loads((root / label / "summary.json").read_text())
    for label in labels
}
for label, summary in summaries.items():
    print(
        label,
        "median=", summary["median_step_seconds"],
        "mean=", summary["mean_step_seconds"],
        "loss=", summary["last_metrics"]["train/loss"],
    )

pairs = (
    ("main", "seqused_eager"),
    ("seqused_eager", "seqused_triton"),
    ("seqused_eager", "seqused_eager_repeat"),
)
for reference_label, candidate_label in pairs:
    reference = summaries[reference_label]["state_fingerprint"]
    candidate = summaries[candidate_label]["state_fingerprint"]
    reference_timing = summaries[reference_label]
    candidate_timing = summaries[candidate_label]
    print(f"\ncomparison: {reference_label} vs {candidate_label}")
    print(
        "  median time reduction:",
        100 * (reference_timing["median_step_seconds"] - candidate_timing["median_step_seconds"])
        / reference_timing["median_step_seconds"],
    )
    print(
        "  final loss delta:",
        candidate_timing["last_metrics"]["train/loss"]
        - reference_timing["last_metrics"]["train/loss"],
    )
    for bucket in sorted(reference):
        for metric in sorted(reference[bucket]):
            left = reference[bucket][metric]
            right = candidate[bucket][metric]
            print(f"  {bucket}/{metric}: {right - left:+.17g}")
PY
