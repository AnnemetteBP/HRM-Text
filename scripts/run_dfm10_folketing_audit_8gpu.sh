#!/usr/bin/env bash
set -euo pipefail

# Audit the four DFM10 Folketing transformation datasets with one local E4B
# Transformers judge server per GPU and one disjoint row partition per GPU.
# This launcher waits for any HRM training process to exit so it cannot compete
# for the eight GPUs.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODEL_PATH="${MODEL_PATH:-/work/dfm/jacobwashere/brainsurgery/models/google/gemma-4-E4B-it}"
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-openai/gemma-4-e4b-judge}"
VLLM_PYTHON="${VLLM_PYTHON:-/home/ucloud/miniforge3/envs/audit/bin/python}"
CLIENT_PYTHON="${CLIENT_PYTHON:-/home/ucloud/miniforge3/envs/hrm-cu132/bin/python}"
PORT_BASE="${PORT_BASE:-8200}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-64}"
CONCURRENCY="${CONCURRENCY:-64}"
PARTITIONS="${PARTITIONS:-8}"
AUDIT_ROOT="${AUDIT_ROOT:-logs/dfm10_folketing_audit_8gpu_e4b}"
WAIT_FOR_TRAINING="${WAIT_FOR_TRAINING:-1}"
CHAT_TEMPLATE="${CHAT_TEMPLATE:-$ROOT/evaluation/chat_templates/gemma4_native_chat.jinja}"
RESUME="${RESUME:-1}"
GPUS="${GPUS:-0,1,2,3,4,5,6,7}"
PID_PREFIX="${PID_PREFIX:-}"

IFS=',' read -r -a GPU_LIST <<< "$GPUS"
if (( ${#GPU_LIST[@]} == 0 )); then
  echo "GPUS must contain at least one GPU index" >&2
  exit 2
fi

DATASETS=(
  folketingets-dokumenter-denoising
  folketingets-dokumenter-error-correction
  folketingets-dokumenter-prefix-continuation
  folketingets-dokumenter-span-filling
)

mkdir -p "$AUDIT_ROOT"/{servers,workers,pids,cache}
exec > >(tee -a "$AUDIT_ROOT/launcher.log") 2>&1

SERVER_PIDS=()
WORKER_PIDS=()

if [[ "$WAIT_FOR_TRAINING" == "1" ]]; then
  echo "Waiting for HRM training processes to exit before claiming GPUs..."
  while pgrep -af '(^|/)(torchrun|pretrain\.py)( |$)|cfg_pretrain_' >/dev/null; do
    sleep 30
  done
fi

cleanup() {
  local pid
  for pid in "${WORKER_PIDS[@]:-}"; do
    pkill -TERM -P "$pid" 2>/dev/null || true
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
    TORCHINDUCTOR_CACHE_DIR="$AUDIT_ROOT/cache/gpu${gpu}/torchinductor" \
    TRITON_CACHE_DIR="$AUDIT_ROOT/cache/gpu${gpu}/triton" \
    "$VLLM_PYTHON" -m vllm.entrypoints.openai.api_server \
      --model "$MODEL_PATH" \
      --served-model-name "$SERVED_MODEL_NAME" \
      --host 127.0.0.1 --port "$port" \
      --max-model-len 8192 \
      --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
      --max-num-seqs "$MAX_NUM_SEQS" \
      --enforce-eager \
      >"$AUDIT_ROOT/servers/gpu${gpu}.log" 2>&1 &
  echo "$!" >"$AUDIT_ROOT/pids/server_${PID_PREFIX}gpu${gpu}.pid"
  SERVER_PIDS+=("$!")
}

wait_server() {
  local port="$1"
  local deadline=$((SECONDS + 900))
  until curl -fsS "http://127.0.0.1:${port}/v1/models" >/dev/null 2>&1; do
    if (( SECONDS > deadline )); then
      echo "Timed out waiting for server on port $port" >&2
      return 1
    fi
    sleep 2
  done
}

echo "Starting ${#GPU_LIST[@]} E4B servers for GPUs ${GPU_LIST[*]} and ${PARTITIONS} disjoint audit partitions..."
for gpu in "${GPU_LIST[@]}"; do
  start_server "$gpu" "$((PORT_BASE + gpu))"
done
for gpu in "${GPU_LIST[@]}"; do
  wait_server "$((PORT_BASE + gpu))"
  echo "server ready: GPU${gpu} port=$((PORT_BASE + gpu))"
done

run_gpu_partitions() {
  local gpu="$1" ordinal="$2" partition worker_root log resume_arg
  for ((partition=ordinal; partition<PARTITIONS; partition+=${#GPU_LIST[@]})); do
    worker_root="$AUDIT_ROOT/workers/partition_${partition}"
    log="$AUDIT_ROOT/workers/partition_${partition}.log"
    resume_arg="--resume"
    [[ "$RESUME" == "1" ]] || resume_arg="--force"
    "$CLIENT_PYTHON" scripts/audit_export_datasets.py audit \
      --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-denoising \
      --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-error-correction \
      --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-prefix-continuation \
      --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-span-filling \
      --audit-root "$worker_root" \
      --base-url "http://127.0.0.1:$((PORT_BASE + gpu))/v1" \
      --model "$SERVED_MODEL_NAME" \
      --partitions "$PARTITIONS" --partition-index "$partition" \
      --concurrency "$CONCURRENCY" --retries "${RETRIES:-3}" \
      --max-tokens "${MAX_TOKENS:-512}" \
      --progress-interval "${PROGRESS_INTERVAL:-100}" \
      "$resume_arg" >"$log" 2>&1
  done
}

for ordinal in "${!GPU_LIST[@]}"; do
  gpu="${GPU_LIST[$ordinal]}"
  run_gpu_partitions "$gpu" "$ordinal" &
  WORKER_PIDS+=("$!")
  echo "$!" >"$AUDIT_ROOT/pids/worker_${PID_PREFIX}gpu${gpu}.pid"
done

status=0
for ordinal in "${!GPU_LIST[@]}"; do
  gpu="${GPU_LIST[$ordinal]}"
  if wait "${WORKER_PIDS[$ordinal]}"; then
    echo "audit partition group complete: GPU${gpu}"
  else
    echo "audit partition group failed: GPU${gpu}" >&2
    status=1
  fi
done

if (( status == 0 )); then
  missing=0
  for ((partition=0; partition<PARTITIONS; partition++)); do
    if [[ ! -f "$AUDIT_ROOT/workers/partition_${partition}/export_judge.audit.jsonl" ]]; then
      echo "missing completed partition ${partition}" >&2
      missing=1
    fi
  done
  if (( missing != 0 )); then
    exit 1
  fi
  : >"$AUDIT_ROOT/export_judge.audit.jsonl.tmp"
  for ((partition=0; partition<PARTITIONS; partition++)); do
    cat "$AUDIT_ROOT/workers/partition_${partition}/export_judge.audit.jsonl" \
      >>"$AUDIT_ROOT/export_judge.audit.jsonl.tmp"
  done
  mv "$AUDIT_ROOT/export_judge.audit.jsonl.tmp" "$AUDIT_ROOT/export_judge.audit.jsonl"
  echo "merged audit: $AUDIT_ROOT/export_judge.audit.jsonl"
fi
exit "$status"
