---
type: Operational Record
title: DFM L CP3 eval resume/GovReport recovery (2026-06-01)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM L CP3 eval
  resume/GovReport recovery (2026-06-01).'
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
# DFM L CP3 eval resume/GovReport recovery (2026-06-01)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM L CP3 eval resume/GovReport recovery, 2026-06-01. Confidence: high.

The CP3 scheduler was later stopped and resumed from
`logs/eval/dfm_L_epoch3_heavy_first_20260531T2227` with
`RESUME_EXISTING_QUEUE=1`. The resumed queue reached the GovReport shards after
finishing the standard eval shards. GovReport initially left all GPUs idle
because `scripts/hrm_openai_server.py` model-server processes were crashing
before serving `/health`, while dfm-evals clients waited on localhost ports.
Two import issues were fixed:

- `scripts/hrm_openai_server.py` now inserts the repo root into `sys.path`
  before importing repo modules.
- `utils/__init__.py` was added so `from utils.functions import ...` resolves
  to the repo-local utility package instead of colliding with other `utils`
  namespace/package paths.

A scheduler cleanup bug was also fixed in `scripts/schedule_checkpoint_evals.sh`:
the DFM and IFEval `RETURN` cleanup traps now read `${server_pid:-}` and
`${judge_pid:-}` into local temporaries before testing/killing them. Without
this, `set -u` could terminate a worker later with an unbound local variable
after a DFM task returned.

When launching a long resume from Codex/tool-managed shells, use `setsid -f`
rather than plain background `nohup`; plain background launches were observed
to be torn down after the launcher command returned. The working detached
resume pattern was:

```bash
setsid -f bash -c 'exec env \
  EPOCH=3 EVAL_EPOCH=3 CKPT_TAG=epoch_3 CKPT_PATH=checkpoints/dfm/L \
  GPUS=0,1,2,3,4,5,6,7 QUEUE_ORDER=heavy_first RESUME_EXISTING_QUEUE=1 \
  LOG_ROOT="logs/eval/dfm_L_epoch3_heavy_first_20260531T2227" \
  DFM_LOG_ROOT="logs/dfm_evals/dfm_L_epoch3_heavy_first_20260531T2227" \
  WANDB_PROJECT="DFM L" WANDB_RUN_ID=kgnbdmwf WANDB_RUN_NAME=dfm-L \
  MODEL_PREFIX=hrm-dfm-L MAX_RETRIES=3 STARTUP_STAGGER_SECONDS=10 \
  scripts/schedule_checkpoint_evals.sh \
  >> "logs/eval/dfm_L_epoch3_heavy_first_20260531T2227.resume6.setsid.log" 2>&1' \
  </dev/null
```

After the `setsid` relaunch, GovReport shards resumed successfully: status
showed shards `0..7` starting, several ending with status `0`, later shards
starting, `11` GovReport shard eval files written, and the remaining queue
down to `38` jobs. Confidence: high.
