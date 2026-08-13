---
type: Operational Record
title: '`dfm-evals` Location'
description: 'Part of Current State: `dfm-evals` Location.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# `dfm-evals` Location

Part of [Current State](/pages/current-state.md).

Verified on 2026-05-24. Confidence: high.

`dfm-evals` is an untracked nested git checkout at `/work/dfm/HRM-Text/dfm-evals`. It was moved from `/work/dfm/HRM-Text/external/dfm-evals` with its local `.venv` intact. The nested checkout's git status remained unchanged by the move; it still has local task patches in `dfm_evals/tasks/danish_citizen_tests.py` and `dfm_evals/tasks/talemaader/task.py`.

The main runnable reference is `scripts/run_dfm_evals_on_checkpoints.sh`, whose default is:

```bash
DFM_EVALS_DIR="${DFM_EVALS_DIR:-${REPO_ROOT}/dfm-evals}"
```

No model training configs depend on the path directly. Existing logs under `logs/dfm_evals/...` remain where they are.
