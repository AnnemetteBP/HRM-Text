---
type: Operational Record
title: Manual dfm-evals sync, verified on (2026-05-24)
description: 'Chronological record from dfm-evals: Manual dfm-evals sync, verified
  on (2026-05-24).'
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
# Manual dfm-evals sync, verified on (2026-05-24)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Manual dfm-evals sync, verified on 2026-05-24: completed Inspect logs were exported to Every Eval Ever JSON and logged to the clean W&B run `origLclean` in project `Original Plus Mixed Danish Instruction Rich L`. A `.eval` file is treated as complete only when the Inspect zip contains `header.json`, `summaries.json`, and `reductions.json`; partial files were not synced. Synced metrics currently include epoch 1 Danish citizen tests, DaLA, and GEC-DaLA, plus Danish citizen tests for epochs 2-4. WMT24++ epoch 1 and DaLA/GEC-DaLA for epochs 2-4 were still partial at the time of this sync. Confidence: high.
