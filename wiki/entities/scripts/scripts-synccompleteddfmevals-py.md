---
type: Software Reference
title: '`scripts/sync_completed_dfm_evals.py`'
description: 'Part of Script Entities: `scripts/sync_completed_dfm_evals.py`.'
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
# `scripts/sync_completed_dfm_evals.py`

Part of [Script Entities](/entities/scripts.md).

Incremental dfm-evals W&B sync helper.

Responsibilities:

- scan an Inspect log directory for completed `.eval` zip files
- require `header.json`, `summaries.json`, and `reductions.json` before treating a log as complete
- export each completed test to a per-test Every Eval Ever directory
- call `scripts/log_dfm_evals_to_wandb.py` so completed tests are logged to W&B before the full epoch finishes
- write `.synced/*.done` marker files under the chosen sync root to avoid duplicate incremental logging

Verified syntax:

```bash
python -m py_compile scripts/sync_completed_dfm_evals.py
```
