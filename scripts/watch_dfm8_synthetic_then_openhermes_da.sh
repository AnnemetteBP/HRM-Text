#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-/work/dfm/HRM-Text}"
cd "$ROOT"

SYNTH_DATA_ROOT="${SYNTH_DATA_ROOT:-data/dfm8_targeted_synthetic}"
SYNTH_LOG_ROOT="${SYNTH_LOG_ROOT:-logs/dfm8_targeted_synthetic_pipeline_c128_20260710T164733}"
EXPECTED_SHARDS="${EXPECTED_SHARDS:-512}"
CHECK_INTERVAL_SECONDS="${CHECK_INTERVAL_SECONDS:-300}"
LOG="${LOG:-logs/dfm8_openhermes_after_targeted_synthetic_$(date +%Y%m%dT%H%M%S).log}"
OPENHERMES_RUN_SCRIPT="${OPENHERMES_RUN_SCRIPT:-dfm8_openhermes_da/scripts/run_openhermes_da_8gpu.sh}"

OPENHERMES_CONCURRENCY="${OPENHERMES_CONCURRENCY:-128}"
OPENHERMES_GPU_MEMORY_UTILIZATION="${OPENHERMES_GPU_MEMORY_UTILIZATION:-0.7}"
OPENHERMES_MAX_NUM_SEQS="${OPENHERMES_MAX_NUM_SEQS:-128}"

mkdir -p "$(dirname "$LOG")"

count_files() {
  local dir="$1"
  find "$dir" -maxdepth 1 -type f -name 'shard_*.jsonl' 2>/dev/null | wc -l
}

count_jobs() {
  local dir="$1"
  find "$dir" -maxdepth 1 -type f -name '*.job' 2>/dev/null | wc -l
}

active_targeted_processes() {
  pgrep -f "dfm8_synthetic\\.cli (generate|audit)|run_dfm8_targeted_synthetic_8gpu\\.sh|vllm.entrypoints.openai.api_server.*--port 850[0-7]" >/dev/null
}

echo "[$(date -Is)] waiting for DFM8 targeted synthetic generation+audit" | tee -a "$LOG"
echo "[$(date -Is)] data_root=$SYNTH_DATA_ROOT log_root=$SYNTH_LOG_ROOT expected_shards=$EXPECTED_SHARDS" | tee -a "$LOG"

while true; do
  generated="$(count_files "$SYNTH_DATA_ROOT/generated")"
  audits="$(count_files "$SYNTH_DATA_ROOT/audits")"
  generate_pending="$(count_jobs "$SYNTH_LOG_ROOT/queue/generate_pending")"
  generate_running="$(count_jobs "$SYNTH_LOG_ROOT/queue/generate_running")"
  generate_failed="$(count_jobs "$SYNTH_LOG_ROOT/queue/generate_failed")"
  audit_pending="$(count_jobs "$SYNTH_LOG_ROOT/queue/audit_pending")"
  audit_running="$(count_jobs "$SYNTH_LOG_ROOT/queue/audit_running")"
  audit_failed="$(count_jobs "$SYNTH_LOG_ROOT/queue/audit_failed")"
  echo "[$(date -Is)] generated=$generated/$EXPECTED_SHARDS audits=$audits/$EXPECTED_SHARDS gen(p/r/f)=${generate_pending}/${generate_running}/${generate_failed} audit(p/r/f)=${audit_pending}/${audit_running}/${audit_failed}" | tee -a "$LOG"

  if [[ "$generate_failed" != "0" || "$audit_failed" != "0" ]]; then
    echo "[$(date -Is)] targeted synthetic has failed jobs; not starting OpenHermes" | tee -a "$LOG"
    exit 1
  fi

  if (( generated >= EXPECTED_SHARDS && audits >= EXPECTED_SHARDS )) \
      && [[ "$generate_pending" == "0" && "$generate_running" == "0" && "$audit_pending" == "0" && "$audit_running" == "0" ]]; then
    break
  fi

  sleep "$CHECK_INTERVAL_SECONDS"
done

echo "[$(date -Is)] targeted synthetic generation+audit complete; waiting for runner/vLLM cleanup" | tee -a "$LOG"
while active_targeted_processes; do
  echo "[$(date -Is)] targeted synthetic processes still active; waiting" | tee -a "$LOG"
  sleep 60
done

echo "[$(date -Is)] starting DFM8 Danish OpenHermes generation+audit" | tee -a "$LOG"
CONCURRENCY="$OPENHERMES_CONCURRENCY" \
GPU_MEMORY_UTILIZATION="$OPENHERMES_GPU_MEMORY_UTILIZATION" \
MAX_NUM_SEQS="$OPENHERMES_MAX_NUM_SEQS" \
bash "$OPENHERMES_RUN_SCRIPT" 2>&1 | tee -a "$LOG"
