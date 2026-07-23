#!/usr/bin/env bash
set -euo pipefail

cd /work/dfm/HRM-Text
source /work/dfm/.home/miniforge3/etc/profile.d/conda.sh
conda activate hrm

ckpt="checkpoints/ferrum_status_map_xs_joint/ferrum-status-map-joint-xs-ctx16k-10epoch-gbs131k-20260722-223736"
outroot="logs/ferrum_status_map_xs_joint/ferrum-status-map-joint-xs-ctx16k-10epoch-gbs131k-20260722-223736/eval_validation_epochs_v2"
mkdir -p "$outroot"
: > "$outroot/run.stdout.txt"
: > "$outroot/run.stderr.txt"
printf 'status=running\nstarted_at=%s\n' "$(date -Is)" > "$outroot/run.status"

export PYTHONWARNINGS="ignore::DeprecationWarning"

for epoch in $(seq 1 10); do
  echo "eval-start epoch_${epoch} $(date -Is)" | tee -a "$outroot/run.stdout.txt"
  torchrun --nproc_per_node=8 --master_port=$((29660 + epoch)) \
    scripts/eval_ferrum_checkpoint.py \
    --checkpoint "$ckpt" \
    --tag "epoch_${epoch}" \
    --data data/sampled_ferrum_status_map_joint_v2_validation_ctx16k \
    --output "$outroot/epoch_${epoch}.json" \
    >"$outroot/epoch_${epoch}.stdout.txt" \
    2>"$outroot/epoch_${epoch}.stderr.txt"
  echo "eval-done epoch_${epoch} $(date -Is)" | tee -a "$outroot/run.stdout.txt"
done

python - <<'PY'
import json
from pathlib import Path

out = Path("logs/ferrum_status_map_xs_joint/ferrum-status-map-joint-xs-ctx16k-10epoch-gbs131k-20260722-223736/eval_validation_epochs_v2")
rows = []
for p in sorted(out.glob("epoch_*.json"), key=lambda p: int(p.stem.split("_")[1])):
    rows.append(json.loads(p.read_text()))

summary = {
    "rows": rows,
    "best_by_correct_processor": max(
        rows,
        key=lambda r: (
            r.get("correct_processor") or -1,
            r.get("exact_accuracy") or -1,
            -(r.get("loss") or 1e9),
        ),
    )
    if rows
    else None,
    "best_by_exact_accuracy": max(
        rows,
        key=lambda r: (
            r.get("exact_accuracy") or -1,
            r.get("correct_processor") or -1,
            -(r.get("loss") or 1e9),
        ),
    )
    if rows
    else None,
    "best_by_loss": min(rows, key=lambda r: r.get("loss") if r.get("loss") is not None else 1e9)
    if rows
    else None,
}

(out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(json.dumps(summary["best_by_correct_processor"], indent=2, sort_keys=True))
PY

printf 'status=0\nfinished_at=%s\n' "$(date -Is)" > "$outroot/run.status"
