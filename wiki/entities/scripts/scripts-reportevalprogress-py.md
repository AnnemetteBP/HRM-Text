---
type: Software Reference
title: '`scripts/report_eval_progress.py`'
description: 'Part of Script Entities: `scripts/report_eval_progress.py`.'
tags:
- scripts
- software
- catalog
- operations
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# `scripts/report_eval_progress.py`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-05-29. Confidence: high for standard eval tqdm parsing; medium
for queued-job ETA because it uses historical runtime weights.

Estimates progress for the active queued checkpoint eval scheduler from:

- `logs/eval/dfm_L_epoch1_queued_all/status.tsv`
- `logs/eval/dfm_L_epoch1_queued_all/jobs.tsv`
- standard shard log tqdm counters such as `generation ... 93/165`

It reports completed/active/queued job counts, active job progress and per-job
ETA, plus a full-evaluation ETA using an 8-lane greedy simulation. DFM/Inspect
active job progress is currently estimated from elapsed time and historical
weights unless the task writes a machine-readable progress counter.

Command:

```bash
cd /work/dfm/HRM-Text
python scripts/report_eval_progress.py
```

Verified immediately after DFM CP1 scheduler launch:

- parsed 8 active GSM8k shards,
- read live tqdm counters such as `93/165`,
- reported `completed=0`, `active=8`, `queued=104`, `total_visible=112`,
- estimated full ETA around `2h57m` from 2026-05-29 15:50 Europe/Berlin.
