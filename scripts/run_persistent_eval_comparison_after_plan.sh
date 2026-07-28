#!/usr/bin/env bash
set -euo pipefail

BASELINE_PLAN_DIR="${1:?baseline plan directory is required}"
CANDIDATE_PLAN_DIR="${2:?candidate plan directory is required}"
CHECKPOINT_TAG="${3:-step_100000}"
POLL_SECONDS="${POLL_SECONDS:-30}"

echo "Waiting for baseline plan: ${BASELINE_PLAN_DIR}"
while true; do
  state="$(
    python - "${BASELINE_PLAN_DIR}" <<'PY'
import sys
from collections import Counter
from pathlib import Path

from eval_scheduler.eval_scheduler.model import read_plan

counts = Counter(
    job.status.value
    for job in read_plan(Path(sys.argv[1]) / "plan.tsv")
)
print(
    f"{counts['pending']} {counts['running']} "
    f"{counts['failed']} {counts['done']} {counts['skipped']}"
)
PY
  )"
  read -r pending running failed done skipped <<<"${state}"
  echo "baseline pending=${pending} running=${running} failed=${failed} done=${done} skipped=${skipped}"
  if (( failed > 0 )); then
    echo "Baseline plan has failed rows; comparison will not start." >&2
    exit 2
  fi
  if (( pending == 0 && running == 0 )); then
    break
  fi
  sleep "${POLL_SECONDS}"
done

echo "Starting persistent-vLLM candidate: ${CANDIDATE_PLAN_DIR}"
started_at="$(date +%s)"
python -m eval_scheduler run \
  --plan-dir "${CANDIDATE_PLAN_DIR}" \
  --gpus 0,1,2,3,4,5,6,7 \
  --persistent-vllm
finished_at="$(date +%s)"
printf 'elapsed_seconds=%s\n' "$((finished_at - started_at))" \
  >"${CANDIDATE_PLAN_DIR}/walltime.txt"

echo "Comparing metrics and timing..."
python scripts/compare_eval_scheduler_runs.py \
  --baseline-plan-dir "${BASELINE_PLAN_DIR}" \
  --candidate-plan-dir "${CANDIDATE_PLAN_DIR}" \
  --checkpoint-tag "${CHECKPOINT_TAG}" \
  --output "${CANDIDATE_PLAN_DIR}/comparison.json"

echo "Comparison complete: ${CANDIDATE_PLAN_DIR}/comparison.json"
