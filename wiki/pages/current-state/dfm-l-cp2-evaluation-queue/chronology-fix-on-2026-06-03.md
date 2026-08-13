---
type: Operational Record
title: Fix on (2026-06-03)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Fix on (2026-06-03).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm-l-cp2-evaluation-queue.md
---
# Fix on (2026-06-03)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Fix on 2026-06-03. Confidence: high. `scripts/schedule_checkpoint_evals.sh`
now defaults `PYTHON_BIN` to `/home/ucloud/miniforge3/envs/hrm/bin/python` and
uses it for standard evals, HRM OpenAI server launches, judge server launches,
merge scripts, and health checks. DFM server and judge health checks now use
`wait_for_server ... || return 1`, so a failed server cannot fall through into
`dfm-evals`. The broken eval processes were stopped, and the tmux run was
relaunched with explicit `PYTHON_BIN=/home/ucloud/miniforge3/envs/hrm/bin/python`.
After relaunch, `pgrep` showed real `hrm_openai_server.py` and
`evaluation.main` processes, and per-GPU memory rose to roughly `102-104GB`,
confirming eval models were loaded alongside the active XL training job.
