#!/usr/bin/env bash
set -euo pipefail

ROOT=${ROOT:-/work/dfm/HRM-Text}
HRM_ENV=${HRM_ENV:-/home/ucloud/miniforge3/envs/hrm}
SOURCE_STEP=${SOURCE_STEP:-175000}
STEPS=${STEPS:-100}
TARGET_STEP=$((SOURCE_STEP + STEPS))
SOURCE_ROOT=${SOURCE_ROOT:-$ROOT/checkpoints/dfm8/XXL-1epoch}
SOURCE_TAG=${SOURCE_TAG:-fsdp2_ephemeral_step_${SOURCE_STEP}}
OUTPUT_ROOT=${OUTPUT_ROOT:-/tmp/hrm_fsdp_wrap_policy_${STEPS}step}
RESUME_VIEW="$OUTPUT_ROOT/resume-view"

mkdir -p "$OUTPUT_ROOT" "$RESUME_VIEW"
exec 9>"$OUTPUT_ROOT/benchmark.lock"
flock -n 9 || { echo "Another FSDP wrap-policy benchmark is running." >&2; exit 2; }

if [[ ! -d "$SOURCE_ROOT/$SOURCE_TAG" ]]; then
  echo "Missing source checkpoint: $SOURCE_ROOT/$SOURCE_TAG" >&2
  exit 1
fi

ln -sfn "$SOURCE_ROOT/$SOURCE_TAG" "$RESUME_VIEW/$SOURCE_TAG"
"$HRM_ENV/bin/python" - \
  "$SOURCE_ROOT/checkpoint_state_ephemeral_step_${SOURCE_STEP}.json" \
  "$RESUME_VIEW/checkpoint_state_ephemeral_step_${SOURCE_STEP}.json" <<'PY'
import json
import sys
from pathlib import Path

source, target = map(Path, sys.argv[1:])
state = json.loads(source.read_text())
if int(state["step"]) != int(target.stem.rsplit("_", 1)[-1]):
    raise SystemExit(f"checkpoint sidecar step mismatch: {state['step']} vs {target}")
if "global_row_cursor_in_epoch" not in state:
    raise SystemExit("checkpoint sidecar has no global row cursor")
state["batch_in_epoch_exact"] = False
target.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
PY

for gpu in 0 1 2 3 4 5 6 7; do
  exec {fd}>"/tmp/hrm-gpu-${gpu}.lock"
  flock "$fd"
done

gpu_process_count() {
  nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null \
    | sed '/^[[:space:]]*$/d' | wc -l
}

if [[ "$(gpu_process_count)" -ne 0 ]] || pgrep -f '^VLLM::EngineCore' >/dev/null 2>&1; then
  echo "GPU process appeared despite holding all benchmark locks." >&2
  exit 3
fi

COMMON=(
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
  resume_checkpoint_path="$RESUME_VIEW"
  resume_checkpoint_tag="$SOURCE_TAG"
  reset_ema_on_resume=false
  upcast_optimizer_state_on_resume=false
  activation_checkpointing=none
  fsdp_shard_degree=null
  fsdp_reshard_after_forward=false
  fsdp_accumulation_sync_mode=no_sync
  max_steps="$TARGET_STEP"
  benchmark_state_fingerprint=true
  stop_after_step=null
  memory_log_interval=25
  log_interval=5
  wandb_run_id=null
  wandb_resume=never
)

run_arm() {
  local label=$1
  local policy=$2
  local output="$OUTPUT_ROOT/$label"
  if [[ -s "$output/summary.json" ]]; then
    echo "[$(date -Is)] Reusing completed $label ($policy)"
    return
  fi
  mkdir -p "$output/wandb"
  echo "[$(date -Is)] Starting $label ($policy)"
  (
    cd "$ROOT"
    WANDB_MODE=disabled \
    WANDB_DIR="$output/wandb" \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    PATH="$HRM_ENV/bin:$PATH" \
    BENCH_OUTPUT="$output/summary.json" \
    "$HRM_ENV/bin/torchrun" --nproc_per_node=8 pretrain.py \
      "${COMMON[@]}" \
      fsdp_wrap_policy="$policy" \
      checkpoint_path="$output/checkpoints-disabled" \
      project_name=fsdp-wrap-policy-disabled \
      run_name="$label"
  ) >"$output/train.log" 2>&1
  echo "[$(date -Is)] Finished $label"
}

run_arm transformer_block transformer_block
run_arm recurrent_level recurrent_level
run_arm transformer_block_repeat transformer_block

"$HRM_ENV/bin/python" - "$OUTPUT_ROOT" <<'PY' | tee "$OUTPUT_ROOT/comparison.json"
import json
import statistics
import sys
from pathlib import Path

root = Path(sys.argv[1])
runs = {
    name: json.loads((root / name / "summary.json").read_text())
    for name in ("transformer_block", "recurrent_level", "transformer_block_repeat")
}

def steady(summary):
    return summary["all_step_seconds"][summary["warmup_dropped"] :]

block = steady(runs["transformer_block"])
level = steady(runs["recurrent_level"])
block_repeat = steady(runs["transformer_block_repeat"])
block_median_center = statistics.fmean(
    (statistics.median(block), statistics.median(block_repeat))
)
block_mean_center = statistics.fmean(
    (statistics.fmean(block), statistics.fmean(block_repeat))
)
comparison = {
    "transformer_block": {
        "median": statistics.median(block),
        "mean": statistics.fmean(block),
        "last_metrics": runs["transformer_block"]["last_metrics"],
    },
    "recurrent_level": {
        "median": statistics.median(level),
        "mean": statistics.fmean(level),
        "last_metrics": runs["recurrent_level"]["last_metrics"],
    },
    "transformer_block_repeat": {
        "median": statistics.median(block_repeat),
        "mean": statistics.fmean(block_repeat),
        "last_metrics": runs["transformer_block_repeat"]["last_metrics"],
    },
    "recurrent_level_speedup_percent": {
        "median": 100 * (1 - statistics.median(level) / statistics.median(block)),
        "mean": 100 * (1 - statistics.fmean(level) / statistics.fmean(block)),
    },
    "recurrent_level_speedup_vs_bracket_center_percent": {
        "median": 100 * (1 - statistics.median(level) / block_median_center),
        "mean": 100 * (1 - statistics.fmean(level) / block_mean_center),
    },
}
print(json.dumps(comparison, indent=2, sort_keys=True))
PY
