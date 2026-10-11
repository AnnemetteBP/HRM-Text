---
type: Runbook
title: XL Andersen Evaluation Backfill
description: Coverage inventory and prerequisites for historical Andersen modernization evaluation.
tags: [evaluation, andersen, xl, dfm10]
status: draft
last_updated: 2026-10-11
confidence: high
---
# XL Andersen Evaluation Backfill

The user requested Andersen modernization coverage for XL since its training
introduction in DFM10. Main-line DFM10 began after step2127489. Cover the
50K evaluation cadence from2150K onward, plus epoch endpoints2482084 and2877261,
and future evaluations. Identity-only branches are outside this main-line inventory.
Existing scheduled Andersen rows were skipped because the119-row validation
JSONL was not transferred to this node; do not propagate this exclusion into
future campaigns once the holdout is restored.

`scripts/inventory_andersen_xl_backfill.py` inventories existing plan rows and
exports without changing the live plan. The initial report at
`logs/andersen-xl-backfill/inventory.json` covers36 past/future boundaries,
with20 existing HF exports. The2482084 sharded source checkpoint is local,
but has no HF export; earlier DFM10 artifacts require retrieval or evaluation
on the original machine. Use EMA and the original fractional epoch metadata.

Superseded on 2026-10-11: `/work/dfm/andersen/pairs_chunked_val.jsonl` was absent. The public
`schneiderkamplab/dfm10-andersen-modernization` package contains training only.
SSH to `ucloud@ssh.cloud.sdu.dk:6768` currently rejects public-key authentication.
Restore the original validation split (119 examples); never substitute training
rows or construct a new holdout. Then validate formats, prepare missing exports,
enable only the active lineage's skipped rows (not superseded DFM13 continuations),
add historical inference/merge/sync rows, and gate them behind a completed training
segment. No live evaluation rows were enabled while this prerequisite is missing.

## Recovery on 2026-10-11

SSH on port 6768 now works. Retrieved all eight canonical DFM10 XL EMA
exports (2150K through 2482084), historical merged metrics, and the original
119-row validation file. All eight historical Andersen results already exist
with 119 samples; do not repeat their inference merely because their artifacts
were previously absent here.

The packaging omission was specific: training preparation excludes validation
from tokenization, the HF exporter packages only training rows, and `/data` is
ignored by Git. The holdout now lives at
`evaluation/data/andersen/pairs_chunked_val.jsonl`, with upstream license and
provenance alongside it. The suite config uses this repository-relative path.
Its SHA256 is
`7d635eb87ecab1fd88be0e290fe029d4af183fbafc0097f516fce0e7c60e91bf`.
The checksum/row-format regression test prevents accidental replacement of the
holdout. No validation rows were added to training or the HF training package.

`scripts/schedule_andersen_xl_backfill.py` prepares missing eval/merge/sync rows
in the existing SQLite plan under an administrative lock, preserving live
runtime state. The 20 missing historical checkpoints and eight future boundaries
use EMA, exact fractional epoch metadata, and the original XL W&B run. Historical
work waits for the current 3450K training segment; subsequent training terminal
barriers include the new merges without making exhausted failures block training.
Receipts and pre-change backup live under `logs/andersen-xl-backfill/schedule/`.
