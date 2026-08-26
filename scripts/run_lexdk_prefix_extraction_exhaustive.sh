#!/usr/bin/env bash
set -euo pipefail

cd /work/dfm/HRM-Text

export PATH="/home/ucloud/miniforge3/envs/hrm-cu132/bin:${PATH}"
export CUDA_HOME="/home/ucloud/miniforge3/envs/hrm-cu132"
export VLLM_LOGGING_LEVEL="WARNING"

output_root="${1:-logs/analysis/lexdk_prefix_extraction_step1650000_exhaustive}"
mkdir -p "${output_root}"

declare -a pids=()
for gpu in $(seq 0 7); do
  shard_dir="${output_root}/shard_${gpu}"
  mkdir -p "${shard_dir}"
  echo "Starting LexDK extraction shard ${gpu}/8 on GPU ${gpu}"
  CUDA_VISIBLE_DEVICES="${gpu}" python scripts/eval_lexdk_prefix_extraction.py \
    --model exports/dfm8_XL_step1650000_ema_hf \
    --source data/downloads/datasets/lexdk/lexdk_articles.jsonl.gz \
    --samples 0 \
    --prefix-tokens 4,8,16,32,64,128,256 \
    --target-tokens 64 \
    --num-shards 8 \
    --shard-index "${gpu}" \
    --gpu-memory-utilization 0.08 \
    --batch-size 256 \
    --output-dir "${shard_dir}" \
    > "${shard_dir}/run.log" 2>&1 &
  pids+=("$!")
done

failed=0
for shard in $(seq 0 7); do
  if wait "${pids[$shard]}"; then
    echo "Shard ${shard}/8 completed"
  else
    echo "Shard ${shard}/8 failed; inspect ${output_root}/shard_${shard}/run.log" >&2
    failed=1
  fi
done

if (( failed != 0 )); then
  exit 1
fi

python scripts/merge_lexdk_prefix_extraction.py \
  --input-root "${output_root}" \
  --output-dir "${output_root}/merged" \
  --expected-shards 8

echo "Exhaustive LexDK extraction probe completed: ${output_root}/merged/report.md"
