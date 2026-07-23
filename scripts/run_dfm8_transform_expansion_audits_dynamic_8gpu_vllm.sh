#!/usr/bin/env bash
set -euo pipefail

# Dynamically audit DFM8 transformation-expansion candidates with one
# OpenAI-compatible Gemma 4 31B vLLM server per GPU. Unlike the static launcher,
# this splits each family into stable hash shards and lets each GPU worker claim
# the next pending shard when it becomes free.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPORT_ROOT="${EXPORT_ROOT:-${ROOT}/export}"
EXPANSION_ROOT="${EXPANSION_ROOT:-${ROOT}/data/dfm8_transform_expansion}"
MODEL_PATH="${MODEL_PATH:-${ROOT}/data/models/google/gemma-4-31B-it-fresh-20260604}"
if [[ ! -d "$MODEL_PATH" ]]; then
  MODEL_PATH="/work/dfm/brainsurgery/models/google/gemma-4-31B-it"
fi
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-posttrain-gemma-teacher}"
PORT_BASE="${PORT_BASE:-8500}"
GPU_LIST="${GPU_LIST:-0 1 2 3 4 5 6 7}"
SAMPLE_RATE="${SAMPLE_RATE:-1.0}"
CONCURRENCY="${CONCURRENCY:-8}"
MAX_RECORDS="${MAX_RECORDS:-}"
LOG_ROOT="${LOG_ROOT:-${ROOT}/logs/dfm8_transform_expansion_dynamic_audits_$(date +%Y%m%dT%H%M%S)}"
AUDIT_SHARD_ROOT_NAME="${AUDIT_SHARD_ROOT_NAME:-audit_shards}"
VLLM_PYTHON="${VLLM_PYTHON:-python}"
CLIENT_PYTHON="${CLIENT_PYTHON:-python}"
TENSOR_PARALLEL_SIZE="${TENSOR_PARALLEL_SIZE:-1}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.95}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-64}"
VLLM_EXTRA_ARGS="${VLLM_EXTRA_ARGS:-}"
DEEP_GEMM_WARMUP="${DEEP_GEMM_WARMUP:-skip}"

# Family shard counts are intentionally higher for long families. Stable hash
# sharding keeps shards disjoint and allows short families to finish without
# stranding their GPU.
DATASET_SHARDS=(
  "common-pile-denoising 32"
  "common-pile-paragraph-reordering 8"
  "common-pile-prefix-continuation 64"
  "common-pile-span-filling 32"
  "danish-dynaword-denoising 8"
  "danish-dynaword-paragraph-reordering 8"
  "danish-dynaword-prefix-continuation 16"
  "danish-dynaword-span-filling 8"
)

mkdir -p "$LOG_ROOT"/{servers,audits,pids,queue/pending,queue/running,queue/done,queue/failed,cache}

cleanup() {
  for pidfile in "$LOG_ROOT"/pids/worker_gpu*.pid "$LOG_ROOT"/pids/vllm_gpu*.pid; do
    [[ -e "$pidfile" ]] || continue
    pid="$(cat "$pidfile")"
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
  done
}
trap cleanup EXIT

start_server() {
  local gpu="$1"
  local port="$2"
  local log="$LOG_ROOT/servers/gpu${gpu}.log"
  read -r -a extra_args <<<"$VLLM_EXTRA_ARGS"
  mkdir -p "$LOG_ROOT/cache/gpu${gpu}"
  CUDA_VISIBLE_DEVICES="$gpu" \
  VLLM_DEEP_GEMM_WARMUP="$DEEP_GEMM_WARMUP" \
  TORCHINDUCTOR_CACHE_DIR="$LOG_ROOT/cache/gpu${gpu}/torchinductor" \
  TRITON_CACHE_DIR="$LOG_ROOT/cache/gpu${gpu}/triton" \
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
  echo "$!" >"$LOG_ROOT/pids/vllm_gpu${gpu}.pid"
}

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

write_jobs() {
  local serial=0
  for spec in "${DATASET_SHARDS[@]}"; do
    read -r dataset shards <<<"$spec"
    [[ -f "$EXPORT_ROOT/$dataset/recreate_dataset.py" ]] || { echo "Missing recreate script for $dataset" >&2; exit 1; }
    [[ -d "$EXPANSION_ROOT/$dataset/data" ]] || { echo "Missing expansion data for $dataset" >&2; exit 1; }
    for ((shard=0; shard<shards; shard++)); do
      serial=$((serial + 1))
      job="$LOG_ROOT/queue/pending/$(printf '%05d' "$serial")__${dataset}__$(printf '%04d' "$shard")_of_$(printf '%04d' "$shards").job"
      {
        printf 'DATASET=%q\n' "$dataset"
        printf 'SHARD_INDEX=%q\n' "$shard"
        printf 'NUM_SHARDS=%q\n' "$shards"
      } >"$job"
    done
  done
}

claim_job() {
  local gpu="$1"
  local job base claimed
  while IFS= read -r -d '' job; do
    base="$(basename "$job")"
    claimed="$LOG_ROOT/queue/running/gpu${gpu}__${base}"
    if mv "$job" "$claimed" 2>/dev/null; then
      printf '%s\n' "$claimed"
      return 0
    fi
  done < <(find "$LOG_ROOT/queue/pending" -maxdepth 1 -type f -name '*.job' -print0 | sort -z)
  return 1
}

worker_loop() {
  local gpu="$1"
  local port="$2"
  local claimed dataset shard shards audit_root audit_log skip_args max_args
  while claimed="$(claim_job "$gpu")"; do
    # shellcheck disable=SC1090
    source "$claimed"
    dataset="$DATASET"
    shard="$SHARD_INDEX"
    shards="$NUM_SHARDS"
    audit_root="$EXPANSION_ROOT/$dataset/$AUDIT_SHARD_ROOT_NAME/shard_$(printf '%04d' "$shard")_of_$(printf '%04d' "$shards")"
    audit_log="$LOG_ROOT/audits/${dataset}__shard_$(printf '%04d' "$shard")_of_$(printf '%04d' "$shards")__gpu${gpu}.log"
    skip_args=()
    while IFS= read -r -d '' previous_audit; do
      [[ "$previous_audit" == "$audit_root/audit.jsonl" ]] && continue
      skip_args+=(--skip-audit "$previous_audit")
    done < <(find "$EXPANSION_ROOT/$dataset" -path "*/audit.jsonl" -print0)
    max_args=()
    if [[ -n "$MAX_RECORDS" ]]; then
      max_args=(--max-records "$MAX_RECORDS")
    fi
    if {
      echo "START dataset=$dataset shard=$shard/$shards gpu=$gpu port=$port audit_root=$audit_root"
      (
        cd "$EXPORT_ROOT/$dataset"
        "$CLIENT_PYTHON" recreate_dataset.py audit \
          --data-root "$EXPANSION_ROOT/$dataset/data" \
          --glob "*.jsonl.gz" \
          --base-url "http://127.0.0.1:${port}/v1" \
          --model "$SERVED_MODEL_NAME" \
          --sample-rate "$SAMPLE_RATE" \
          --concurrency "$CONCURRENCY" \
          --audit-root "$audit_root" \
          --num-shards "$shards" \
          --shard-index "$shard" \
          --force \
          "${skip_args[@]}" \
          "${max_args[@]}"
      )
      echo "DONE dataset=$dataset shard=$shard/$shards gpu=$gpu"
    } >"$audit_log" 2>&1; then
      mv "$claimed" "$LOG_ROOT/queue/done/$(basename "$claimed")"
    else
      mv "$claimed" "$LOG_ROOT/queue/failed/$(basename "$claimed")"
    fi
  done
}

read -r -a GPUS <<<"$GPU_LIST"
write_jobs

echo "Starting ${#GPUS[@]} dynamic vLLM servers from model: $MODEL_PATH"
echo "GPU memory utilization: $GPU_MEMORY_UTILIZATION"
echo "Job count: $(find "$LOG_ROOT/queue/pending" -maxdepth 1 -type f | wc -l)"
for idx in "${!GPUS[@]}"; do
  gpu="${GPUS[$idx]}"
  port=$((PORT_BASE + idx))
  start_server "$gpu" "$port"
done

for idx in "${!GPUS[@]}"; do
  port=$((PORT_BASE + idx))
  wait_server "$port"
  echo "server ready: gpu=${GPUS[$idx]} port=$port"
done

echo "Launching dynamic audit workers. Logs: $LOG_ROOT"
for idx in "${!GPUS[@]}"; do
  gpu="${GPUS[$idx]}"
  port=$((PORT_BASE + idx))
  worker_loop "$gpu" "$port" &
  echo "$!" >"$LOG_ROOT/pids/worker_gpu${gpu}.pid"
done

status=0
for idx in "${!GPUS[@]}"; do
  gpu="${GPUS[$idx]}"
  pid="$(cat "$LOG_ROOT/pids/worker_gpu${gpu}.pid")"
  if wait "$pid"; then
    echo "worker complete: gpu=$gpu"
  else
    echo "worker failed: gpu=$gpu" >&2
    status=1
  fi
done

done_count="$(find "$LOG_ROOT/queue/done" -maxdepth 1 -type f | wc -l)"
failed_count="$(find "$LOG_ROOT/queue/failed" -maxdepth 1 -type f | wc -l)"
pending_count="$(find "$LOG_ROOT/queue/pending" -maxdepth 1 -type f | wc -l)"
running_count="$(find "$LOG_ROOT/queue/running" -maxdepth 1 -type f | wc -l)"
echo "Dynamic audit logs: $LOG_ROOT"
echo "jobs: done=$done_count failed=$failed_count pending=$pending_count running=$running_count"
(( failed_count == 0 && pending_count == 0 && running_count == 0 )) || status=1
exit "$status"
