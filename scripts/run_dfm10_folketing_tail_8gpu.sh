#!/usr/bin/env bash
set -euo pipefail

# Redistribute the unfinished tails of original Folketing audit partitions 6
# and 7 over all eight GPUs without repeating completed judge decisions.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OLD_ROOT="${OLD_ROOT:-logs/dfm10_folketing_audit_8gpu_vllm}"
TAIL_ROOT="${TAIL_ROOT:-$OLD_ROOT/tail_reshard_8gpu}"
MODEL_PATH="${MODEL_PATH:-/work/dfm/jacobwashere/brainsurgery/models/google/gemma-4-E4B-it}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-openai/gemma-4-e4b-judge}"
VLLM_PYTHON="${VLLM_PYTHON:-/home/ucloud/miniforge3/envs/audit/bin/python}"
CLIENT_PYTHON="${CLIENT_PYTHON:-/home/ucloud/miniforge3/envs/hrm-cu132/bin/python}"
PORT_BASE="${PORT_BASE:-8200}"
CONCURRENCY="${CONCURRENCY:-64}"

mkdir -p "$TAIL_ROOT"/{servers,workers,pids,completed_ids}
exec > >(tee -a "$TAIL_ROOT/launcher.log") 2>&1

for partition in 6 7; do
  source_file="$OLD_ROOT/workers/partition_$partition/export_judge.audit.jsonl"
  id_file="$TAIL_ROOT/completed_ids/partition_$partition.txt"
  [[ -s "$source_file" ]] || { echo "Missing original audit: $source_file" >&2; exit 2; }
  if [[ ! -s "$id_file" || "$source_file" -nt "$id_file" ]]; then
    echo "Extracting completed row IDs for original partition $partition..."
    jq -r '.row_id // empty' "$source_file" >"$id_file.tmp"
    mv "$id_file.tmp" "$id_file"
  fi
done

SERVER_PIDS=()
WORKER_PIDS=()
cleanup() {
  local pid
  for pid in "${WORKER_PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
  for pid in "${SERVER_PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

start_server() {
  local gpu="$1" port="$2"
  CUDA_VISIBLE_DEVICES="$gpu" \
    CUDA_HOME="${CUDA_HOME:-/home/ucloud/miniforge3/envs/audit}" \
    PATH="${CUDA_HOME:-/home/ucloud/miniforge3/envs/audit}/bin:/home/ucloud/miniforge3/envs/audit/bin:$PATH" \
    LD_LIBRARY_PATH="${CUDA_HOME:-/home/ucloud/miniforge3/envs/audit}/lib:${LD_LIBRARY_PATH:-}" \
    VLLM_USE_FLASHINFER_SAMPLER=0 \
    FLASHINFER_DISABLE_VERSION_CHECK=1 \
    TORCHINDUCTOR_CACHE_DIR="$OLD_ROOT/cache/gpu${gpu}/torchinductor" \
    TRITON_CACHE_DIR="$OLD_ROOT/cache/gpu${gpu}/triton" \
    "$VLLM_PYTHON" -m vllm.entrypoints.openai.api_server \
      --model "$MODEL_PATH" \
      --served-model-name "$SERVED_MODEL_NAME" \
      --host 127.0.0.1 --port "$port" \
      --max-model-len 8192 \
      --gpu-memory-utilization 0.90 \
      --max-num-seqs 64 \
      --enforce-eager \
      >"$TAIL_ROOT/servers/gpu${gpu}.log" 2>&1 &
  SERVER_PIDS+=("$!")
  echo "$!" >"$TAIL_ROOT/pids/server_gpu${gpu}.pid"
}

wait_server() {
  local port="$1" deadline=$((SECONDS + 900))
  until curl -fsS "http://127.0.0.1:$port/v1/models" >/dev/null 2>&1; do
    (( SECONDS <= deadline )) || return 1
    sleep 2
  done
}

for gpu in {0..7}; do
  start_server "$gpu" "$((PORT_BASE + gpu))"
done
for gpu in {0..7}; do
  wait_server "$((PORT_BASE + gpu))"
  echo "server ready: GPU$gpu"
done

for gpu in {0..7}; do
  if (( gpu < 4 )); then
    primary=6
    secondary="$gpu"
  else
    primary=7
    secondary="$((gpu - 4))"
  fi
  worker_root="$TAIL_ROOT/workers/partition_${primary}_sub_${secondary}"
  "$CLIENT_PYTHON" scripts/audit_export_datasets.py audit \
    --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-denoising \
    --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-error-correction \
    --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-prefix-continuation \
    --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-span-filling \
    --audit-root "$worker_root" \
    --base-url "http://127.0.0.1:$((PORT_BASE + gpu))/v1" \
    --model "$SERVED_MODEL_NAME" \
    --partitions 8 --partition-index "$primary" \
    --secondary-partitions 4 --secondary-partition-index "$secondary" \
    --skip-id-file "$TAIL_ROOT/completed_ids/partition_${primary}.txt" \
    --concurrency "$CONCURRENCY" --retries 3 --max-tokens 512 \
    --progress-interval 100 --resume \
    >"$TAIL_ROOT/workers/partition_${primary}_sub_${secondary}.log" 2>&1 &
  WORKER_PIDS+=("$!")
  echo "$!" >"$TAIL_ROOT/pids/worker_gpu${gpu}.pid"
done

status=0
for pid in "${WORKER_PIDS[@]}"; do
  wait "$pid" || status=1
done
(( status == 0 )) || exit "$status"

merged_tmp="$OLD_ROOT/export_judge.audit.jsonl.tail-reshard.tmp"
: >"$merged_tmp"
for partition in {0..7}; do
  cat "$OLD_ROOT/workers/partition_${partition}/export_judge.audit.jsonl" >>"$merged_tmp"
done
for primary in 6 7; do
  for secondary in {0..3}; do
    cat "$TAIL_ROOT/workers/partition_${primary}_sub_${secondary}/export_judge.audit.jsonl" >>"$merged_tmp"
  done
done
mv "$merged_tmp" "$OLD_ROOT/export_judge.audit.jsonl"
echo "Merged original decisions and audited tails: $OLD_ROOT/export_judge.audit.jsonl"
