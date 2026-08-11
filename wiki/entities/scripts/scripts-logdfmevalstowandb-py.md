---
type: Software Reference
title: '`scripts/log_dfm_evals_to_wandb.py`'
description: 'Part of Script Entities: `scripts/log_dfm_evals_to_wandb.py`.'
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
# `scripts/log_dfm_evals_to_wandb.py`

Part of [Script Entities](/entities/scripts.md).

Logs dfm-evals Every Eval Ever JSON exports to W&B under a non-`eval` prefix.

Responsibilities:

- read `.json` records under an EEE export directory
- collect numeric `evaluation_results[].score_details.score` values
- log metrics as `<prefix>/<task>/<scorer>/<metric>`, defaulting to `dfm_eval/...`
- resume W&B run `origLclean` in project `Original Plus Mixed Danish Instruction Rich L` by default

Verified syntax:

```bash
python -m py_compile scripts/log_dfm_evals_to_wandb.py
```
