#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODEL_PATH="${MODEL_PATH:-/work/dfm/.home/.cache/huggingface/hub/models--google--gemma-4-26B-A4B-it/snapshots/4d7ae4984b7db7de8f8457170b3f1a419ee76d52}"
MODEL_NAME="${MODEL_NAME:-openai/gemma-4-26b-a4b-judge}"
VLLM_PYTHON="${VLLM_PYTHON:-/home/ucloud/miniforge3/envs/audit/bin/python}"
CLIENT_PYTHON="${CLIENT_PYTHON:-/home/ucloud/miniforge3/envs/hrm-cu132/bin/python}"
RUN_ROOT="${RUN_ROOT:-logs/data_audits/dfm10_source_quality_a4b_20260826}"
PORT_BASE="${PORT_BASE:-8310}"
CONCURRENCY="${CONCURRENCY:-64}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-64}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"
ALLOW_PENDING_RAW="${ALLOW_PENDING_RAW:-1}"
GPUS=(0 1 2 3)
PARTITIONS="${#GPUS[@]}"

mkdir -p "$RUN_ROOT"/{servers,partitions,pids,cache}
exec 9>"$RUN_ROOT/launcher.lock"
if ! flock -n 9; then
  echo "Another launcher holds $RUN_ROOT/launcher.lock" >&2
  exit 2
fi
exec > >(tee -a "$RUN_ROOT/launcher.log") 2>&1

SERVER_PIDS=()
WORKER_PIDS=()
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

prepare_args=(
  scripts/dfm10_quality_audit.py prepare
  --samples-output "$RUN_ROOT/samples.jsonl"
  --inventory-output "$RUN_ROOT/inventory.json"
  --samples-per-source 100
)
if [[ "$ALLOW_PENDING_RAW" == "1" ]]; then
  prepare_args+=(--allow-pending-raw)
fi
"$CLIENT_PYTHON" "${prepare_args[@]}"

for index in "${!GPUS[@]}"; do
  gpu="${GPUS[$index]}"
  port=$((PORT_BASE + index))
  CUDA_VISIBLE_DEVICES="$gpu" \
    CUDA_HOME="${CUDA_HOME:-/usr/local/cuda}" \
    PATH="${CUDA_HOME:-/usr/local/cuda}/bin:/home/ucloud/miniforge3/envs/audit/bin:$PATH" \
    LD_LIBRARY_PATH="${CUDA_HOME:-/usr/local/cuda}/lib64:${LD_LIBRARY_PATH:-}" \
    VLLM_USE_FLASHINFER_SAMPLER=0 FLASHINFER_DISABLE_VERSION_CHECK=1 \
    TORCHINDUCTOR_CACHE_DIR="$RUN_ROOT/cache/gpu${gpu}/torchinductor" \
    TRITON_CACHE_DIR="$RUN_ROOT/cache/gpu${gpu}/triton" \
    "$VLLM_PYTHON" -m vllm.entrypoints.openai.api_server \
      --model "$MODEL_PATH" --served-model-name "$MODEL_NAME" \
      --host 127.0.0.1 --port "$port" --max-model-len 8192 \
      --limit-mm-per-prompt '{"image":0,"video":0,"audio":0}' \
      --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
      --max-num-seqs "$MAX_NUM_SEQS" --enforce-eager \
      >"$RUN_ROOT/servers/gpu${gpu}.log" 2>&1 &
  SERVER_PIDS+=("$!")
  echo "$!" >"$RUN_ROOT/pids/server_gpu${gpu}.pid"
done

for index in "${!GPUS[@]}"; do
  gpu="${GPUS[$index]}"
  port=$((PORT_BASE + index))
  deadline=$((SECONDS + 900))
  until curl -fsS "http://127.0.0.1:${port}/v1/models" >/dev/null 2>&1; do
    (( SECONDS <= deadline )) || { echo "GPU${gpu} server startup timed out" >&2; exit 1; }
    sleep 2
  done
  echo "server ready: GPU${gpu} port=${port}"
done

for index in "${!GPUS[@]}"; do
  gpu="${GPUS[$index]}"
  port=$((PORT_BASE + index))
  "$CLIENT_PYTHON" scripts/dfm10_quality_audit.py audit \
    --samples "$RUN_ROOT/samples.jsonl" \
    --output "$RUN_ROOT/partitions/partition_${index}.jsonl" \
    --base-url "http://127.0.0.1:${port}/v1" \
    --model "$MODEL_NAME" --partitions "$PARTITIONS" --partition-index "$index" \
    --concurrency "$CONCURRENCY" --max-tokens 512 --retries 3 --resume \
    >"$RUN_ROOT/partitions/partition_${index}.log" 2>&1 &
  WORKER_PIDS+=("$!")
  echo "$!" >"$RUN_ROOT/pids/worker_gpu${gpu}.pid"
done

status=0
for index in "${!GPUS[@]}"; do
  if ! wait "${WORKER_PIDS[$index]}"; then
    echo "quality audit partition ${index} failed" >&2
    status=1
  fi
done
(( status == 0 )) || exit "$status"

"$CLIENT_PYTHON" scripts/dfm10_quality_audit.py merge \
  --samples "$RUN_ROOT/samples.jsonl" \
  --partition-root "$RUN_ROOT/partitions" --partitions "$PARTITIONS" \
  --output "$RUN_ROOT/dfm10_source_quality_audit.jsonl"

echo "DFM10 source quality audit complete: $RUN_ROOT/dfm10_source_quality_audit.jsonl"
