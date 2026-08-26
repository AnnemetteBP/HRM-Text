#!/usr/bin/env bash
set -euo pipefail

REPO=/work/dfm/HRM-Text
PYTHON=/home/ucloud/miniforge3/envs/hrm-cu132/bin/python
SAMPLE="$REPO/logs/analysis/dfm9_memorisation_categories_ab_step1650000/prepared.jsonl.gz"
OUTPUT="$REPO/logs/analysis/dfm9_memorisation_category_b_exhaustive_step1650000"
SCRIPT="$REPO/scripts/eval_memorisation_categories.py"

mkdir -p "$OUTPUT"
cd "$REPO"

if [[ ! -s "$OUTPUT/prepared_exhaustive_remaining.jsonl.gz" ]]; then
  echo "Preparing exhaustive Category B remainder..."
  "$PYTHON" "$SCRIPT" prepare-exhaustive \
    --categories B --exclude-prepared "$SAMPLE" --output-dir "$OUTPUT" \
    >"$OUTPUT/prepare.log" 2>&1
fi

echo "Waiting for all eight GPUs to become free..."
while true; do
  active=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null \
    | sed '/^[[:space:]]*$/d' | wc -l)
  if [[ "$active" -eq 0 ]]; then break; fi
  sleep 60
done

pids=()
for gpu in $(seq 0 7); do
  result="$OUTPUT/results_shard_$(printf '%02d' "$gpu")_of_08.jsonl.gz"
  if [[ -s "$result" ]]; then continue; fi
  CUDA_VISIBLE_DEVICES="$gpu" "$PYTHON" "$SCRIPT" run-shard \
    --output-dir "$OUTPUT" \
    --prepared-file "$OUTPUT/prepared_exhaustive_remaining.jsonl.gz" \
    --num-shards 8 --shard-index "$gpu" \
    --gpu-memory-utilization 0.90 \
    --max-num-seqs 1024 --max-num-batched-tokens 209216 \
    --batch-size 1024 --log-stats \
    >"$OUTPUT/shard_${gpu}.log" 2>&1 &
  pids+=("$!")
done

failed=0
for pid in "${pids[@]}"; do
  if ! wait "$pid"; then failed=1; fi
done
if [[ "$failed" -ne 0 ]]; then exit 1; fi

"$PYTHON" "$SCRIPT" merge --output-dir "$OUTPUT" >"$OUTPUT/merge.log" 2>&1
echo "Completed: $OUTPUT/report.md"
