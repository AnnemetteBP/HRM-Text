#!/usr/bin/env bash
set -euo pipefail

cd /work/dfm/HRM-Text
roots=(
  "logs/training/dfm8_L"
  "logs/training/dfm8_L_epoch2"
)

while true; do
  latest="$({ find "${roots[@]}" -type f -name 'train_until_step_*.log' -printf '%T@ %p\n' 2>/dev/null || true; } | sort -n | tail -1 | cut -d' ' -f2-)"
  clear
  date --iso-8601=seconds
  if [[ -n "$latest" ]]; then
    echo "$latest"
    lines="${LINES:-48}"
    tail -n "$((lines > 4 ? lines - 4 : 1))" "$latest"
  else
    echo "Waiting for the first scheduler-managed DFM8 L training segment..."
  fi
  sleep 5
done
