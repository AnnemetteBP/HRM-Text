#!/usr/bin/env bash
set -euo pipefail

ROOT=${ROOT:-/work/dfm/HRM-Text}
STEPS=${STEPS:-1000}
SOURCE_STEP=${SOURCE_STEP:-175000}
TARGET_STEP=$((SOURCE_STEP + STEPS))
SOURCE_CHECKPOINT_ROOT=${SOURCE_CHECKPOINT_ROOT:-$ROOT/checkpoints/dfm8/XXL-1epoch}
SOURCE_CHECKPOINT_TAG=${SOURCE_CHECKPOINT_TAG:-fsdp2_ephemeral_step_175000}
OUTPUT_ROOT=${OUTPUT_ROOT:-/tmp/hrm_fa4_long_ab_${STEPS}step}
RESUME_VIEW="$OUTPUT_ROOT/resume-view"
HRM_ENV=${HRM_ENV:-/home/ucloud/miniforge3/envs/hrm}
MAIN_COMMIT=$(git -C "$ROOT" rev-parse main)
PERFORMANCE_COMMIT=$(git -C "$ROOT" rev-parse HEAD)
MAIN_WORKTREE="$OUTPUT_ROOT/worktrees/main-${MAIN_COMMIT:0:12}"
PERFORMANCE_WORKTREE="$OUTPUT_ROOT/worktrees/performance-${PERFORMANCE_COMMIT:0:12}"

mkdir -p "$OUTPUT_ROOT/worktrees"
exec 9>"$OUTPUT_ROOT/benchmark.lock"
flock -n 9 || { echo "Another long FA4 A/B benchmark is already running."; exit 1; }

if [[ ! -d "$SOURCE_CHECKPOINT_ROOT/$SOURCE_CHECKPOINT_TAG" ]]; then
  echo "Missing source checkpoint: $SOURCE_CHECKPOINT_ROOT/$SOURCE_CHECKPOINT_TAG" >&2
  exit 1
fi

prepare_worktree() {
  local path=$1
  local commit=$2
  if [[ ! -e "$path/.git" ]]; then
    git -C "$ROOT" worktree add --detach "$path" "$commit"
  fi
  if [[ ! -e "$path/data" ]]; then
    ln -s "$ROOT/data" "$path/data"
  fi
}

prepare_worktree "$MAIN_WORKTREE" "$MAIN_COMMIT"
prepare_worktree "$PERFORMANCE_WORKTREE" "$PERFORMANCE_COMMIT"

mkdir -p "$RESUME_VIEW"
ln -sfn \
  "$SOURCE_CHECKPOINT_ROOT/$SOURCE_CHECKPOINT_TAG" \
  "$RESUME_VIEW/$SOURCE_CHECKPOINT_TAG"
"$HRM_ENV/bin/python" - \
  "$SOURCE_CHECKPOINT_ROOT/checkpoint_state_ephemeral_step_${SOURCE_STEP}.json" \
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

# Metric history is benchmark-only instrumentation and is applied identically
# to both trees. It does not alter model, optimizer, or data-loader execution.
apply_benchmark_history() {
  local worktree=$1
  if rg -q '"metric_history": bench_metric_history' "$worktree/pretrain.py"; then
    return
  fi
  "$HRM_ENV/bin/python" - "$worktree/pretrain.py" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()
replacements = (
    (
        "    bench_last_metrics: dict[str, float] = {}\n",
        "    bench_last_metrics: dict[str, float] = {}\n"
        "    bench_metric_history: list[dict[str, float | int]] = []\n",
    ),
    (
        "                    bench_last_metrics = dict(metrics)\n"
        "                    progress_bar.update(train_state.step - progress_bar.n)  # type: ignore\n",
        "                    bench_last_metrics = dict(metrics)\n"
        "                    if config.max_steps is not None:\n"
        "                        bench_metric_history.append({\"step\": train_state.step, **metrics})\n"
        "                    progress_bar.update(train_state.step - progress_bar.n)  # type: ignore\n",
    ),
    (
        "            \"last_metrics\": bench_last_metrics,\n",
        "            \"last_metrics\": bench_last_metrics,\n"
        "            \"metric_history\": bench_metric_history,\n",
    ),
)
for old, new in replacements:
    if text.count(old) != 1:
        raise SystemExit(f"benchmark instrumentation anchor count was {text.count(old)}, expected 1: {old!r}")
    text = text.replace(old, new)
path.write_text(text)
PY
}

apply_benchmark_history "$MAIN_WORKTREE"
apply_benchmark_history "$PERFORMANCE_WORKTREE"

cat > "$OUTPUT_ROOT/source_state.txt" <<EOF
main_commit=$MAIN_COMMIT
performance_commit=$PERFORMANCE_COMMIT
source_checkpoint=$SOURCE_CHECKPOINT_ROOT/$SOURCE_CHECKPOINT_TAG
resume_view=$RESUME_VIEW
source_step=$SOURCE_STEP
target_step=$TARGET_STEP
optimizer_steps=$STEPS
EOF

gpu_process_count() {
  local count
  count=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null \
    | sed '/^[[:space:]]*$/d' \
    | wc -l)
  # A vLLM EngineCore may exist for several seconds before it establishes a
  # CUDA context and becomes visible to nvidia-smi.
  if pgrep -f '^VLLM::EngineCore' >/dev/null 2>&1; then
    count=$((count + 1))
  fi
  printf '%s\n' "$count"
}

wait_for_idle_gpus() {
  local idle_polls=0
  echo "[$(date -Is)] Waiting for three consecutive clean 30-second GPU polls"
  while [[ "$idle_polls" -lt 3 ]]; do
    if [[ "$(gpu_process_count)" -eq 0 ]]; then
      idle_polls=$((idle_polls + 1))
    else
      idle_polls=0
    fi
    echo "[$(date -Is)] idle_poll=$idle_polls/3"
    nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu \
      --format=csv,noheader,nounits
    if [[ "$idle_polls" -lt 3 ]]; then
      sleep 30
    fi
  done
}

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
  checkpoint_path="$OUTPUT_ROOT/checkpoints-disabled"
  resume_checkpoint_path="$RESUME_VIEW"
  resume_checkpoint_tag="$SOURCE_CHECKPOINT_TAG"
  reset_ema_on_resume=false
  upcast_optimizer_state_on_resume=false
  activation_checkpointing=none
  fsdp_shard_degree=null
  fsdp_reshard_after_forward=false
  fsdp_accumulation_sync_mode=no_sync
  max_steps="$TARGET_STEP"
  benchmark_state_fingerprint=true
  stop_after_step=null
  log_interval=5
  project_name=fa4-long-ab-disabled
  wandb_run_id=null
  wandb_resume=never
)

run_one() {
  local worktree=$1
  local label=$2
  shift 2
  local output="$OUTPUT_ROOT/$label"
  mkdir -p "$output/wandb"
  if [[ -s "$output/summary.json" ]]; then
    echo "[$(date -Is)] Skipping completed arm $label"
    return
  fi
  while true; do
    wait_for_idle_gpus
    if [[ "$(gpu_process_count)" -eq 0 ]]; then
      break
    fi
    echo "[$(date -Is)] GPU process appeared after idle qualification; retrying gate"
  done
  echo "[$(date -Is)] Starting $label at step $SOURCE_STEP; target $TARGET_STEP"
  (
    cd "$worktree"
    WANDB_MODE=disabled \
    WANDB_DIR="$output/wandb" \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    PATH="$HRM_ENV/bin:$PATH" \
    BENCH_OUTPUT="$output/summary.json" \
    "$HRM_ENV/bin/torchrun" --nproc_per_node=8 pretrain.py \
      "${COMMON_OVERRIDES[@]}" \
      run_name="$label" \
      "$@"
  ) > "$output/train.log" 2>&1
  echo "[$(date -Is)] Finished $label"
}

run_one "$MAIN_WORKTREE" main
run_one "$PERFORMANCE_WORKTREE" seqused_triton \
  +arch.prefixlm_fa4_impl=seqused \
  +arch.prefixlm_fa4_grad_mask_impl=triton

"$HRM_ENV/bin/python" - "$OUTPUT_ROOT" <<'PY'
import json
import math
import statistics
import sys
from pathlib import Path

root = Path(sys.argv[1])
runs = {name: json.loads((root / name / "summary.json").read_text()) for name in ("main", "seqused_triton")}

def steady(summary):
    values = summary["all_step_seconds"]
    return values[summary["warmup_dropped"] :]

def history(summary):
    return {int(row["step"]): row for row in summary["metric_history"]}

base_times = steady(runs["main"])
test_times = steady(runs["seqused_triton"])
base_hist = history(runs["main"])
test_hist = history(runs["seqused_triton"])
steps = sorted(base_hist.keys() & test_hist.keys())
metrics = sorted((set(base_hist[steps[0]]) & set(test_hist[steps[0]])) - {"step"})

comparison = {
    "main": {
        "median_step_seconds": statistics.median(base_times),
        "mean_step_seconds": statistics.fmean(base_times),
    },
    "seqused_triton": {
        "median_step_seconds": statistics.median(test_times),
        "mean_step_seconds": statistics.fmean(test_times),
    },
    "speedup": {
        "median_percent": 100 * (1 - statistics.median(test_times) / statistics.median(base_times)),
        "mean_percent": 100 * (1 - statistics.fmean(test_times) / statistics.fmean(base_times)),
    },
    "trajectory": {},
    "windows": [],
}

for metric in metrics:
    deltas = [float(test_hist[s][metric]) - float(base_hist[s][metric]) for s in steps]
    comparison["trajectory"][metric] = {
        "points": len(deltas),
        "mean_delta_triton_minus_main": statistics.fmean(deltas),
        "mean_absolute_delta": statistics.fmean(abs(x) for x in deltas),
        "rmse": math.sqrt(statistics.fmean(x * x for x in deltas)),
        "final_delta": deltas[-1],
    }

first = min(steps)
for window_start in range(first, max(steps) + 1, 100):
    selected = [s for s in steps if window_start <= s < window_start + 100]
    if not selected:
        continue
    row = {"start_step": window_start, "end_step": selected[-1], "points": len(selected)}
    for metric in metrics:
        row[f"main/{metric}"] = statistics.fmean(float(base_hist[s][metric]) for s in selected)
        row[f"seqused_triton/{metric}"] = statistics.fmean(float(test_hist[s][metric]) for s in selected)
    comparison["windows"].append(row)

(root / "comparison.json").write_text(json.dumps(comparison, indent=2) + "\n")

lines = [
    "# FA4 long A/B result",
    "",
    "| Path | Median step (s) | Mean step (s) |",
    "|---|---:|---:|",
    f"| main | {comparison['main']['median_step_seconds']:.6f} | {comparison['main']['mean_step_seconds']:.6f} |",
    f"| seqused+triton | {comparison['seqused_triton']['median_step_seconds']:.6f} | {comparison['seqused_triton']['mean_step_seconds']:.6f} |",
    "",
    f"Median speedup: **{comparison['speedup']['median_percent']:.3f}%**.  ",
    f"Mean speedup: **{comparison['speedup']['mean_percent']:.3f}%**.",
    "",
    "## Metric trajectory deltas",
    "",
    "| Metric | Mean delta | Mean absolute delta | RMSE | Final delta |",
    "|---|---:|---:|---:|---:|",
]
for metric, values in comparison["trajectory"].items():
    lines.append(
        f"| {metric} | {values['mean_delta_triton_minus_main']:.8g} | "
        f"{values['mean_absolute_delta']:.8g} | {values['rmse']:.8g} | {values['final_delta']:.8g} |"
    )
lines += ["", "## 100-step windows", "", "```json", json.dumps(comparison["windows"], indent=2), "```", ""]
(root / "RESULTS.md").write_text("\n".join(lines))
print(json.dumps(comparison, indent=2))
PY

echo "[$(date -Is)] Results written to $OUTPUT_ROOT/RESULTS.md"
