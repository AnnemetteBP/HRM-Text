#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-/work/dfm/HRM-Text}"
cd "$ROOT"

AUDIT_LOG_ROOT="${AUDIT_LOG_ROOT:-logs/dfm8_transform_expansion_dynamic_audits_c64_u070_20260709T110453}"
CHECK_INTERVAL_SECONDS="${CHECK_INTERVAL_SECONDS:-300}"
LOG="${LOG:-logs/dfm8_targeted_synthetic_after_transform_audit_$(date +%Y%m%dT%H%M%S).log}"
RUN_SCRIPT="${RUN_SCRIPT:-dfm8_synthetic/scripts/run_dfm8_targeted_synthetic_8gpu.sh}"

mkdir -p "$(dirname "$LOG")"

echo "[$(date -Is)] waiting for DFM8 transform audit: $AUDIT_LOG_ROOT" | tee -a "$LOG"
while true; do
  pending="$(find "$AUDIT_LOG_ROOT/queue/pending" -maxdepth 1 -type f -name '*.job' 2>/dev/null | wc -l)"
  running="$(find "$AUDIT_LOG_ROOT/queue/running" -maxdepth 1 -type f -name '*.job' 2>/dev/null | wc -l)"
  failed="$(find "$AUDIT_LOG_ROOT/queue/failed" -maxdepth 1 -type f -name '*.job' 2>/dev/null | wc -l)"
  done_count="$(find "$AUDIT_LOG_ROOT/queue/done" -maxdepth 1 -type f -name '*.job' 2>/dev/null | wc -l)"
  echo "[$(date -Is)] audit jobs done=$done_count running=$running pending=$pending failed=$failed" | tee -a "$LOG"
  if [[ "$failed" != "0" ]]; then
    echo "[$(date -Is)] audit has failed jobs; not starting targeted synthetic generation" | tee -a "$LOG"
    exit 1
  fi
  if [[ "$pending" == "0" && "$running" == "0" ]]; then
    break
  fi
  sleep "$CHECK_INTERVAL_SECONDS"
done

echo "[$(date -Is)] transform audit complete; waiting for audit-owned vLLM processes to exit if they are shutting down" | tee -a "$LOG"
sleep 30

echo "[$(date -Is)] starting DFM8 targeted synthetic generation/audit" | tee -a "$LOG"
CONCURRENCY=64 \
MAX_NUM_SEQS=64 \
TARGET_BOUND=min \
bash "$RUN_SCRIPT" 2>&1 | tee -a "$LOG"
