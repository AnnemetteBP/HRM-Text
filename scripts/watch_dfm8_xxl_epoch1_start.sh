#!/usr/bin/env bash
set -euo pipefail

ROOT=/work/dfm/HRM-Text
PLAN="$ROOT/logs/scheduler/dfm8_XXL_1epoch_steps50k_100k_persistent_vllm_20260725"
LOG="$PLAN/start-watch.log"
TRAIN_LOG="$ROOT/logs/training/dfm8_XXL_1epoch/step_151000_to_200000/train_until_step_200000.log"
PYTHON=/home/ucloud/miniforge3/envs/hrm/bin/python
MIN_FREE_MIB=178000

exec >>"$LOG" 2>&1
echo "$(date --iso-8601=seconds) watcher started"

while true; do
  mapfile -t free < <(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits)
  if [[ ${#free[@]} -eq 8 ]]; then
    all_free=1
    for mib in "${free[@]}"; do
      if (( mib < MIN_FREE_MIB )); then
        all_free=0
        break
      fi
    done
    if (( all_free )); then
      echo "$(date --iso-8601=seconds) all GPUs satisfy ${MIN_FREE_MIB} MiB gate"
      break
    fi
  fi
  sleep 30
done

sleep 120
echo "$(date --iso-8601=seconds) post-release startup check"
"$PYTHON" -m eval_scheduler status --plan-dir "$PLAN" || true
pgrep -af 'torchrun.*pretrain.py.*arch/size@arch=XXL' || true
if [[ -f "$TRAIN_LOG" ]]; then
  tail -120 "$TRAIN_LOG"
else
  echo "training log not present yet: $TRAIN_LOG"
fi

# Keep observing through the first forward/backward progress or a terminal row.
for _ in $(seq 1 20); do
  state="$($PYTHON - "$PLAN/plan.tsv" <<'PY'
import csv, sys
with open(sys.argv[1]) as handle:
    for row in csv.DictReader(handle, delimiter="\t"):
        if row["job_id"] == "campaign-train-200000":
            print(row["status"])
            break
PY
)"
  if [[ "$state" == done || "$state" == failed ]]; then
    echo "$(date --iso-8601=seconds) training row became $state"
    [[ -f "$TRAIN_LOG" ]] && tail -200 "$TRAIN_LOG"
    exit 0
  fi
  if [[ -f "$TRAIN_LOG" ]] && grep -Eq '[0-9]+/[0-9]+.*(it/s|s/it)' "$TRAIN_LOG"; then
    echo "$(date --iso-8601=seconds) training progress confirmed"
    tail -20 "$TRAIN_LOG"
    exit 0
  fi
  sleep 30
done

echo "$(date --iso-8601=seconds) no training progress confirmed within ten minutes"
[[ -f "$TRAIN_LOG" ]] && tail -200 "$TRAIN_LOG"
exit 2
