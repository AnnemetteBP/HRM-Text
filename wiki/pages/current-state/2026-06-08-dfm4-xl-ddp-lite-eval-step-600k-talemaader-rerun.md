---
type: Operational Record
title: 2026-06-08 DFM4 XL-DDP Lite Eval Step 600K Talemaader Rerun
description: 'Part of Current State: 2026-06-08 DFM4 XL-DDP Lite Eval Step 600K Talemaader
  Rerun.'
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
# 2026-06-08 DFM4 XL-DDP Lite Eval Step 600K Talemaader Rerun

Part of [Current State](/pages/current-state.md).

Confidence: high for local logs/processes.

For `checkpoints/dfm4/XL-ddp` `step_600000` no-EMA lite eval, the original
scheduler failed to produce `generative_talemaader` artifacts. The child job
retried four times and ended with `status_1`, while the parent aggregate status
misleadingly recorded a successful end for that task. Rerunning with the Gemma
judge colocated on GPU0 also failed: the judge used about `15.4 GiB`, leaving
only `22 MiB` free, and `scripts/hrm_openai_server.py` OOMed during model
construction.

The active workaround is to run the Gemma judge CPU-only and the HRM server on
GPU0:

```bash
cd /work/dfm/HRM-Text
CUDA_VISIBLE_DEVICES='' /home/ucloud/miniforge3/envs/hrm/bin/python \
  scripts/transformers_openai_server.py unsloth/gemma-4-E4B-it \
  --served-model-name gemma-4-e4b-judge-cpu \
  --host 127.0.0.1 --port 9799

env CKPT_PATH=checkpoints/dfm4/XL-ddp \
  CKPT_TAG=step_600000 \
  EVAL_EPOCH=1.6337778116635397 \
  LOG_ROOT=logs/dfm_evals/dfm4_XL_ddp_noema_lite_600k_talemaader_cpujudge_rerun_20260608T074615 \
  MODEL_GPU=0 \
  MODEL_PORT=9788 \
  MODEL_NAME=hrm-dfm4-XL-ddp-noema-generative_talemaader-step_600000 \
  JUDGE_SERVED_NAME=gemma-4-e4b-judge-cpu \
  EXISTING_JUDGE_BASE_URL=http://127.0.0.1:9799/v1 \
  SHARD_INDEX=0 \
  NUM_SHARDS=8 \
  NO_EMA=1 \
  PREFIX=lite_dfm_eval_noema \
  WANDB_SYNC=1 \
  WANDB_PROJECT='Original Plus Mixed Danish Instruction Rich L' \
  WANDB_RUN_ID=dfm4xlddpclean \
  WANDB_RUN_NAME='dfm4-XL-ddp clean lite history' \
  WAIT_FOR_MODEL_GPU_FREE_MB=10000 \
  BATCH_SIZE=1 \
  BATCH_TIMEOUT_MS=25 \
  bash scripts/run_talemaader_split_gpu_eval.sh
```

At launch, both servers reached health, the HRM server served completions, and
the CPU judge served judged requests. This workaround is slower than GPU judge
serving but avoids disturbing the active DFM4 XL-DDP training.

Completion/repair update, 2026-06-08. Confidence: high. The `step_600000`
no-EMA lite eval finished, including `MATH`. Standard evals synced correctly.
Several DFM evals had correct incremental syncs, but the later final merge path
rewrote local merged files and W&B rows with zero-sample DFM metrics at the
same epoch. The correct metrics were repaired by re-merging directly from the
`.eval` artifacts and re-syncing to W&B run `dfm4xlddpclean` under
`lite_dfm_eval_noema/*`.

Repair output root:

```text
logs/dfm_evals/dfm4_XL_ddp_noema_lite_600k_repair_sync_20260608T092912
```

All repair logs reported successful W&B sync. Correct repaired sample counts:

```text
dala:                 2048
danish_citizen_tests: 545
gec_dala:             512
generative_talemaader:101
govreport:            61
humaneval:            41
ifeval-da:            17
multi_wiki_qa:        1024
nordjyllandnews:      125
piqa:                 108
wmt24pp_en_da:        120
```

Known risk: because W&B history is append-only, the earlier zero-sample rows
may still exist at the same `lite_dfm_eval_noema/epoch` x-coordinate. The
latest repaired rows are correct, but plots may need filtering or a clean
history clone if duplicate same-x rows are visually confusing.
