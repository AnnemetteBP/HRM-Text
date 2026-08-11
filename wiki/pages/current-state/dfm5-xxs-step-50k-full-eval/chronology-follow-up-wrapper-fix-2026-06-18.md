---
type: Operational Record
title: Follow-up wrapper fix (2026-06-18)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Follow-up wrapper
  fix (2026-06-18).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# Follow-up wrapper fix (2026-06-18)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Follow-up wrapper fix, 2026-06-18. Confidence: high for local shell dry-run and
code inspection. `scripts/run_euroeval_on_checkpoint.sh` now honors
`VLLM_PYTHON` for the vLLM server process while keeping `PYTHON_BIN` for the
EuroEval client, health checks, merge/logging, and native-compatible proxy. The
scheduler's `--vllm-python` option therefore controls the server interpreter
for internal HRM vLLM EuroEval jobs.

Verified dry-run:

```bash
cd /work/dfm/HRM-Text
DRY_RUN=1 \
HRM_SERVER_BACKEND=vllm \
HRM_HF_EXPORT_DIR=/work/dfm/HRM-Text/exports/dfm5_L_step550000_ema_hf \
HRM_VLLM_NATIVE_PROXY=1 \
GPU=0 \
PORT=19001 \
CKPT_PATH=checkpoints/dfm5/L \
CKPT_TAG=step_550000 \
MODEL_PREFIX=probe \
VLLM_PYTHON=/home/ucloud/miniforge3/envs/hrm/bin/python \
EUROEVAL_DATASETS=angry-tweets \
EUROEVAL_LOG_ROOT=/tmp/hrm_euroeval_dry_run \
scripts/run_euroeval_on_checkpoint.sh
```

The dry-run printed the vLLM server launch branch, native-compatible proxy
launch, and EuroEval client command without starting long-running processes.
