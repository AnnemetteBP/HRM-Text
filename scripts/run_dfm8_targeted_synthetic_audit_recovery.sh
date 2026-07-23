#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/dfm8_synthetic${PYTHONPATH:+:$PYTHONPATH}"

MODEL_PATH="${MODEL_PATH:-${ROOT}/data/models/google/gemma-4-31B-it-fresh-20260604}"
if [[ ! -d "$MODEL_PATH" ]]; then
  MODEL_PATH="/work/dfm/brainsurgery/models/google/gemma-4-31B-it"
fi

SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-posttrain-gemma-teacher}"
GPU_LIST="${GPU_LIST:-0 1 2 3 4 5 6 7}"
PORT_BASE="${PORT_BASE:-8500}"
CONCURRENCY="${CONCURRENCY:-64}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-64}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.7}"
TENSOR_PARALLEL_SIZE="${TENSOR_PARALLEL_SIZE:-1}"
VLLM_PYTHON="${VLLM_PYTHON:-python}"
CLIENT_PYTHON="${CLIENT_PYTHON:-python}"
DEEP_GEMM_WARMUP="${DEEP_GEMM_WARMUP:-skip}"
VLLM_EXTRA_ARGS="${VLLM_EXTRA_ARGS:-}"
DATA_ROOT="${DATA_ROOT:-data/dfm8_targeted_synthetic}"
UPLOAD_ROOT="${UPLOAD_ROOT:-export-upload-dfm8-synthetic}"
LOG_ROOT="${LOG_ROOT:-logs/dfm8_targeted_synthetic_fixed_20260709T223530}"
HELD_QUEUE="${HELD_QUEUE:-audit_held_gpu0_recovery}"

mkdir -p "$LOG_ROOT"/{servers,pids,workers,queue/audit_pending,queue/audit_running,queue/audit_done,queue/audit_failed,cache}

started_servers=()

cleanup() {
  for pidfile in "$LOG_ROOT"/pids/recovery_worker_audit_gpu*.pid; do
    [[ -e "$pidfile" ]] || continue
    kill "$(cat "$pidfile")" >/dev/null 2>&1 || true
  done
  for pidfile in "$LOG_ROOT"/pids/recovery_vllm_gpu*.pid; do
    [[ -e "$pidfile" ]] || continue
    kill "$(cat "$pidfile")" >/dev/null 2>&1 || true
  done
  for pid in "${started_servers[@]:-}"; do
    kill "$pid" >/dev/null 2>&1 || true
  done
}
trap cleanup EXIT

wait_server() {
  local port="$1"
  local deadline=$((SECONDS + 900))
  until curl -fsS "http://127.0.0.1:${port}/v1/models" >/dev/null 2>&1; do
    if (( SECONDS > deadline )); then
      echo "Timed out waiting for vLLM server on port ${port}" >&2
      return 1
    fi
    sleep 2
  done
}

start_or_reuse_server() {
  local gpu="$1"
  local port="$2"
  local log="$LOG_ROOT/servers/recovery_gpu${gpu}.log"
  if curl -fsS "http://127.0.0.1:${port}/v1/models" >/dev/null 2>&1; then
    echo "reusing server: gpu=$gpu port=$port"
    return 0
  fi
  read -r -a extra_args <<<"$VLLM_EXTRA_ARGS"
  mkdir -p "$LOG_ROOT/cache/recovery_gpu${gpu}"
  CUDA_VISIBLE_DEVICES="$gpu" \
  VLLM_DEEP_GEMM_WARMUP="$DEEP_GEMM_WARMUP" \
  TORCHINDUCTOR_CACHE_DIR="$LOG_ROOT/cache/recovery_gpu${gpu}/torchinductor" \
  TRITON_CACHE_DIR="$LOG_ROOT/cache/recovery_gpu${gpu}/triton" \
  "$VLLM_PYTHON" -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name "$SERVED_MODEL_NAME" \
    --host 127.0.0.1 \
    --port "$port" \
    --tensor-parallel-size "$TENSOR_PARALLEL_SIZE" \
    --max-model-len "$MAX_MODEL_LEN" \
    --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" \
    --max-num-seqs "$MAX_NUM_SEQS" \
    "${extra_args[@]}" \
    >"$log" 2>&1 &
  local pid="$!"
  echo "$pid" >"$LOG_ROOT/pids/recovery_vllm_gpu${gpu}.pid"
  started_servers+=("$pid")
  wait_server "$port"
  echo "started recovery server: gpu=$gpu port=$port"
}

release_held_audit_jobs() {
  local held="$LOG_ROOT/queue/$HELD_QUEUE"
  mkdir -p "$held" "$LOG_ROOT/queue/audit_pending"
  shopt -s nullglob
  local files=("$held"/*.job)
  if ((${#files[@]})); then
    mv "${files[@]}" "$LOG_ROOT/queue/audit_pending/"
  fi
}

claim_job() {
  local gpu="$1"
  local job base claimed
  while IFS= read -r -d '' job; do
    base="$(basename "$job")"
    claimed="$LOG_ROOT/queue/audit_running/gpu${gpu}__${base}"
    if mv "$job" "$claimed" 2>/dev/null; then
      printf '%s\n' "$claimed"
      return 0
    fi
  done < <(find "$LOG_ROOT/queue/audit_pending" -maxdepth 1 -type f -name '*.job' -print0 | sort -z)
  return 1
}

worker_loop() {
  local gpu="$1"
  local port="$2"
  local claimed input base out log
  while claimed="$(claim_job "$gpu")"; do
    # shellcheck disable=SC1090
    source "$claimed"
    input="$INPUT"
    base="$(basename "$input")"
    out="$DATA_ROOT/audits/$base"
    log="$LOG_ROOT/workers/recovery_audit_${base}_gpu${gpu}.log"
    mkdir -p "$DATA_ROOT/audits"
    if "$CLIENT_PYTHON" -m dfm8_synthetic.cli audit "$input" \
        --root "$DATA_ROOT" \
        --output "$out" \
        --base-url "http://127.0.0.1:${port}/v1" \
        --model "$SERVED_MODEL_NAME" \
        --concurrency "$CONCURRENCY" \
        >>"$log" 2>&1; then
      mv "$claimed" "$LOG_ROOT/queue/audit_done/$(basename "$claimed")"
    else
      mv "$claimed" "$LOG_ROOT/queue/audit_failed/$(basename "$claimed")"
    fi
  done
}

read -r -a GPUS <<<"$GPU_LIST"
echo "DFM8 targeted synthetic audit recovery log: $LOG_ROOT"
echo "Using Gemma 4 31B judge: $MODEL_PATH"

server_start_pids=()
for idx in "${!GPUS[@]}"; do
  start_or_reuse_server "${GPUS[$idx]}" "$((PORT_BASE + idx))" &
  server_start_pids+=("$!")
done
server_start_status=0
for pid in "${server_start_pids[@]}"; do
  wait "$pid" || server_start_status=1
done
if (( server_start_status != 0 )); then
  echo "At least one recovery vLLM server failed to start" >&2
  exit 1
fi

release_held_audit_jobs
echo "Starting audit jobs=$(find "$LOG_ROOT/queue/audit_pending" -maxdepth 1 -type f -name '*.job' | wc -l)"

status=0
for idx in "${!GPUS[@]}"; do
  gpu="${GPUS[$idx]}"
  port=$((PORT_BASE + idx))
  worker_loop "$gpu" "$port" &
  echo "$!" >"$LOG_ROOT/pids/recovery_worker_audit_gpu${gpu}.pid"
done
for idx in "${!GPUS[@]}"; do
  gpu="${GPUS[$idx]}"
  pid="$(cat "$LOG_ROOT/pids/recovery_worker_audit_gpu${gpu}.pid")"
  wait "$pid" || status=1
done
if (( status != 0 )); then
  echo "At least one audit worker failed" >&2
  exit "$status"
fi

"$CLIENT_PYTHON" -m dfm8_synthetic.cli build-upload \
  --root "$DATA_ROOT" \
  --output-root "$UPLOAD_ROOT" \
  --generator-model "$SERVED_MODEL_NAME" \
  --judge-model "$SERVED_MODEL_NAME" \
  --force

echo "Upload-ready folders: $UPLOAD_ROOT"
