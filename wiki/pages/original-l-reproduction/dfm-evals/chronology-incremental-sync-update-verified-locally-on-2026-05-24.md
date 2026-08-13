---
type: Operational Record
title: Incremental sync update, verified locally on (2026-05-24)
description: 'Chronological record from dfm-evals: Incremental sync update, verified
  locally on (2026-05-24).'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction/dfm-evals.md
---
# Incremental sync update, verified locally on (2026-05-24)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Incremental sync update, verified locally on 2026-05-24: `scripts/sync_completed_dfm_evals.py` was added and `scripts/run_dfm_evals_on_checkpoints.sh` now starts it by default with `INCREMENTAL_WANDB_SYNC=1`. It scans the Inspect log directory, treats `.eval` files as complete only when the zip contains `header.json`, `summaries.json`, and `reductions.json`, exports each completed test separately, and logs it to W&B immediately. `FINAL_WANDB_SYNC` now defaults to `0` to avoid logging the full epoch a second time after incremental sync; the wrapper still exports the full EEE directory for archival use. Confidence: high.
