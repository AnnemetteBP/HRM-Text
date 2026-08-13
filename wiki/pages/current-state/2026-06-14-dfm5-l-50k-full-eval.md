---
type: Operational Record
title: 2026-06-14 DFM5 L 50K Full Eval
description: 'Part of Current State: 2026-06-14 DFM5 L 50K Full Eval.'
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
# 2026-06-14 DFM5 L 50K Full Eval

Part of [Current State](/pages/current-state.md).

Confidence: high for local checkpoint, scheduler, process, and GPU inspection;
medium until all shards finish and W&B sync is verified.

The DFM5 L step-50K checkpoint was present and launched for full evaluation on
all 8 GPUs while the DFM5 L training run remained active:

```text
checkpoint path: checkpoints/dfm5/L
checkpoint tag:  step_50000
state file:      checkpoints/dfm5/L/checkpoint_state_step_50000.json
wandb project:   DFM5
wandb run id:    oti1lisg
wandb run name:  dfm5-L
tmux session:    dfm5_L_step50000_full_eval
queued jobs:     188
```

The checkpoint state says `epoch=1`, `step=50000`,
`batch_in_epoch=50000`, `global_batch_size=196608`,
`data_path=data/sampled_dfm5`, and `checkpoint_format=sharded`.

Launch command:

```bash
cd /work/dfm/HRM-Text
tmux new-session -d -s dfm5_L_step50000_full_eval \
  'bash /tmp/dfm5_L_step50000_full_eval.sh'
```

The script in `/tmp/dfm5_L_step50000_full_eval.sh` runs:

```bash
cd /work/dfm/HRM-Text
CKPT_PATH=checkpoints/dfm5/L \
CKPT_TAG=step_50000 \
EVAL_EPOCH=0.27608846182186414 \
GPUS=0,1,2,3,4,5,6,7 \
LOG_ROOT=logs/eval/dfm5_L_step50000_full_20260614_dfm5_L_step50000_full \
DFM_LOG_ROOT=logs/dfm_evals/dfm5_L_step50000_full_20260614_dfm5_L_step50000_full \
EUROEVAL_LOG_ROOT=logs/euroeval/dfm5_L_step50000_full_20260614_dfm5_L_step50000_full \
WANDB_SYNC=1 \
WANDB_PROJECT=DFM5 \
WANDB_RUN_ID=oti1lisg \
WANDB_RUN_NAME=dfm5-L \
MODEL_PREFIX=hrm-dfm5-L \
RUN_EUROEVAL=1 \
STANDARD_BATCH_SIZE=8 \
DFM_BATCH_SIZE=8 \
DFM_BATCH_SIZE_GOVREPORT=4 \
DFM_BATCH_SIZE_NORDJYLLANDNEWS=8 \
DFM_BATCH_SIZE_WMT24PP_EN_DA=8 \
DFM_BATCH_SIZE_GENERATIVE_TALEMAADER=8 \
IFEVAL_BATCH_SIZE=16 \
MAX_RETRIES=4 \
EUROEVAL_BIN=/work/dfm/HRM-Text/scripts/euroeval_api_no_flash_attn_guard.py \
scripts/schedule_checkpoint_evals.sh 2>&1 | tee logs/dfm5_L_step50000_full_eval_20260614.log
```

Initial status:

```text
2026-06-14T11:38:54+02:00 QUEUED 188 jobs
2026-06-14T11:38:54+02:00 CHECKPOINT_READY step_50000 path_checkpoints/dfm5/L
2026-06-14T11:38:54+02:00 WORKERS 3046228 3046229 3046230 3046231 3046232 3046233 3046234 3046235
```

At about `2026-06-14T11:42+02:00`, all eight GPUs showed 100% utilization.
The first eight GSM8k shards finished quickly, and the scheduler had moved the
workers onto DROP and MMLU shards. This confirms that the queue can start
later tasks as soon as individual GPUs free up.

Update at `2026-06-14T13:19+02:00`: the initial launch used batch sizes that
were too conservative for the available B200 headroom. A restart with higher
configured batch sizes initially still selected `batch_8` for MATH because
`scripts/schedule_checkpoint_evals.sh` treated the highest previously
successful low-batch telemetry row as a ceiling. The selector was patched so a
prior low-batch success no longer prevents trying a higher configured batch
size; only recorded OOM telemetry lowers the candidate batch size. The eval
queue was restarted with:

```text
STANDARD_BATCH_SIZE=128
STANDARD_BATCH_SIZE_GSM8K=64
STANDARD_BATCH_SIZE_MATH=64
STANDARD_BATCH_SIZE_DROP=32
DFM_BATCH_SIZE=32
DFM_BATCH_SIZE_GOVREPORT=32
DFM_BATCH_SIZE_NORDJYLLANDNEWS=32
DFM_BATCH_SIZE_WMT24PP_EN_DA=32
DFM_BATCH_SIZE_HUMANEVAL=16
DFM_BATCH_SIZE_GENERATIVE_TALEMAADER=16
IFEVAL_BATCH_SIZE=32
EUROEVAL_BATCH_SIZE=16
MAX_RETRIES=5
```

The live process command lines after the second restart showed MATH shards
running with `generation_config.batch_size=64`. Confidence: high.
