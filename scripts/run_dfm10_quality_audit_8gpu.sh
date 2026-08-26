#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODEL_PATH="${MODEL_PATH:-/work/dfm/jacobwashere/brainsurgery/models/google/gemma-4-E4B-it}"
MODEL_NAME="${MODEL_NAME:-openai/gemma-4-e4b-quality-judge}"
VLLM_PYTHON="${VLLM_PYTHON:-/home/ucloud/miniforge3/envs/audit/bin/python}"
CLIENT_PYTHON="${CLIENT_PYTHON:-/home/ucloud/miniforge3/envs/hrm-cu132/bin/python}"
RUN_ROOT="${RUN_ROOT:-logs/data_audits/dfm10_source_quality_e4b_20260826}"
FOLKETING_AUDIT_ROOT="${FOLKETING_AUDIT_ROOT:-logs/dfm10_folketing_audit_8gpu_vllm}"
FOLKETING_LAUNCHER_PID="${FOLKETING_LAUNCHER_PID:-2027591}"
PORT_BASE="${PORT_BASE:-8300}"
CONCURRENCY="${CONCURRENCY:-64}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-64}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"
MIN_FREE_MIB="${MIN_FREE_MIB:-170000}"
PARTITIONS=8

mkdir -p "$RUN_ROOT"/{servers,partitions,pids,cache}
exec 9>"$RUN_ROOT/launcher.lock"
if ! flock -n 9; then
  echo "Another DFM10 quality-audit launcher holds $RUN_ROOT/launcher.lock" >&2
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

if kill -0 "$FOLKETING_LAUNCHER_PID" 2>/dev/null && \
   tr '\0' ' ' <"/proc/$FOLKETING_LAUNCHER_PID/cmdline" | grep -q 'run_dfm10_folketing_audit_8gpu.sh'; then
  echo "Waiting for Folketing audit launcher PID $FOLKETING_LAUNCHER_PID to finish..."
  while kill -0 "$FOLKETING_LAUNCHER_PID" 2>/dev/null; do sleep 60; done
fi

if [[ ! -s "$FOLKETING_AUDIT_ROOT/export_judge.audit.jsonl" ]]; then
  echo "Missing completed Folketing audit: $FOLKETING_AUDIT_ROOT/export_judge.audit.jsonl" >&2
  exit 2
fi

echo "Filtering accepted Folketing rows..."
AUDIT_ROOT="$FOLKETING_AUDIT_ROOT" \
OUTPUT_ROOT="data/dfm10_folketing_transform_sources_audited" \
  bash scripts/filter_dfm10_folketing_tasks.sh

echo "Preparing deterministic source inventory and up-to-100 samples per source..."
"$CLIENT_PYTHON" scripts/dfm10_quality_audit.py prepare \
  --samples-output "$RUN_ROOT/samples.jsonl" \
  --inventory-output "$RUN_ROOT/inventory.json" \
  --samples-per-source 100

echo "Waiting until every GPU has at least ${MIN_FREE_MIB} MiB free..."
while true; do
  ready=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | awk -v minimum="$MIN_FREE_MIB" '$1 >= minimum {count++} END {print count+0}')
  [[ "$ready" == "8" ]] && break
  sleep 30
done

for gpu in {0..7}; do
  port=$((PORT_BASE + gpu))
  CUDA_VISIBLE_DEVICES="$gpu" \
    CUDA_HOME="${CUDA_HOME:-/home/ucloud/miniforge3/envs/audit}" \
    PATH="${CUDA_HOME:-/home/ucloud/miniforge3/envs/audit}/bin:/home/ucloud/miniforge3/envs/audit/bin:$PATH" \
    LD_LIBRARY_PATH="${CUDA_HOME:-/home/ucloud/miniforge3/envs/audit}/lib:${LD_LIBRARY_PATH:-}" \
    VLLM_USE_FLASHINFER_SAMPLER=0 FLASHINFER_DISABLE_VERSION_CHECK=1 \
    TORCHINDUCTOR_CACHE_DIR="$RUN_ROOT/cache/gpu${gpu}/torchinductor" \
    TRITON_CACHE_DIR="$RUN_ROOT/cache/gpu${gpu}/triton" \
    "$VLLM_PYTHON" -m vllm.entrypoints.openai.api_server \
      --model "$MODEL_PATH" --served-model-name "$MODEL_NAME" \
      --host 127.0.0.1 --port "$port" --max-model-len 8192 \
      --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
      --max-num-seqs "$MAX_NUM_SEQS" --enforce-eager \
      >"$RUN_ROOT/servers/gpu${gpu}.log" 2>&1 &
  SERVER_PIDS+=("$!")
  echo "$!" >"$RUN_ROOT/pids/server_gpu${gpu}.pid"
done

for gpu in {0..7}; do
  port=$((PORT_BASE + gpu))
  deadline=$((SECONDS + 900))
  until curl -fsS "http://127.0.0.1:${port}/v1/models" >/dev/null 2>&1; do
    (( SECONDS <= deadline )) || { echo "GPU${gpu} server startup timed out" >&2; exit 1; }
    sleep 2
  done
  echo "server ready: GPU${gpu} port=${port}"
done

for gpu in {0..7}; do
  "$CLIENT_PYTHON" scripts/dfm10_quality_audit.py audit \
    --samples "$RUN_ROOT/samples.jsonl" \
    --output "$RUN_ROOT/partitions/partition_${gpu}.jsonl" \
    --base-url "http://127.0.0.1:$((PORT_BASE + gpu))/v1" \
    --model "$MODEL_NAME" --partitions "$PARTITIONS" --partition-index "$gpu" \
    --concurrency "$CONCURRENCY" --max-tokens 512 --retries 3 --resume \
    >"$RUN_ROOT/partitions/partition_${gpu}.log" 2>&1 &
  WORKER_PIDS+=("$!")
  echo "$!" >"$RUN_ROOT/pids/worker_gpu${gpu}.pid"
done

status=0
for gpu in {0..7}; do
  if ! wait "${WORKER_PIDS[$gpu]}"; then
    echo "quality audit partition ${gpu} failed" >&2
    status=1
  fi
done
(( status == 0 )) || exit "$status"

"$CLIENT_PYTHON" scripts/dfm10_quality_audit.py merge \
  --samples "$RUN_ROOT/samples.jsonl" \
  --partition-root "$RUN_ROOT/partitions" --partitions "$PARTITIONS" \
  --output "$RUN_ROOT/dfm10_source_quality_audit.jsonl"

echo "DFM10 source quality audit complete: $RUN_ROOT/dfm10_source_quality_audit.jsonl"
