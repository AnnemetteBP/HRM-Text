#!/usr/bin/env bash
set -euo pipefail

REPO=/work/dfm/HRM-Text
PYTHON=/home/ucloud/miniforge3/envs/hrm-cu132/bin/python
OUTPUT="$REPO/logs/analysis/dfm9_memorisation_categories_ab_step1650000"
SCRIPT="$REPO/scripts/eval_memorisation_categories.py"

mkdir -p "$OUTPUT"
cd "$REPO"

if [[ ! -s "$OUTPUT/prepared.jsonl.gz" ]]; then
  echo "Preparing deterministic Category A+B samples..."
  "$PYTHON" "$SCRIPT" prepare \
    --categories A,B \
    --samples-per-cohort 10000 \
    --candidate-multiplier 20 \
    --output-dir "$OUTPUT" \
    >"$OUTPUT/prepare.log" 2>&1
fi

echo "Waiting for all eight GPUs to become free..."
while true; do
  active=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | sed '/^[[:space:]]*$/d' | wc -l)
  if [[ "$active" -eq 0 ]]; then
    break
  fi
  echo "$(date --iso-8601=seconds) active_gpu_processes=$active"
  sleep 60
done

echo "Launching eight inference shards..."
pids=()
for gpu in $(seq 0 7); do
  result="$OUTPUT/results_shard_$(printf '%02d' "$gpu")_of_08.jsonl.gz"
  if [[ -s "$result" ]]; then
    echo "GPU$gpu shard already complete"
    continue
  fi
  CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON" "$SCRIPT" run-shard \
    --output-dir "$OUTPUT" \
    --num-shards 8 \
    --shard-index "$gpu" \
    --gpu-memory-utilization 0.90 \
    --batch-size 256 \
    >"$OUTPUT/shard_${gpu}.log" 2>&1 &
  pids+=("$!")
done

failed=0
for pid in "${pids[@]}"; do
  if ! wait "$pid"; then
    failed=1
  fi
done
if [[ "$failed" -ne 0 ]]; then
  echo "At least one inference shard failed; inspect $OUTPUT/shard_*.log" >&2
  exit 1
fi

"$PYTHON" "$SCRIPT" merge --output-dir "$OUTPUT" >"$OUTPUT/merge.log" 2>&1
echo "Completed: $OUTPUT/report.md"
