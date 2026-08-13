---
type: Operational Record
title: 'Update 2026-06-13: Full standard, DFM, and EuroEval evals were launched for
  DFM5'
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Update 2026-06-13:
  Full standard, DFM, and EuroEval evals were launched for DFM5.'
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
# Update 2026-06-13: Full standard, DFM, and EuroEval evals were launched for DFM5

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-06-13. Confidence: high. Full standard, DFM, and EuroEval evals
were launched for DFM5 XXS checkpoints `step_100000` and `step_150000` in tmux
session `dfm5_xxs_eval_100k_150k`. Both checkpoints had
`fsdp2_step_*` metadata and all eight carry files before launch. Epoch-axis
values were computed from `total_length=35,605,979,095` and
`global_batch_size=196,608`:

```text
step_100000 -> 0.5521769236437283
step_150000 -> 0.8282653854655924
```

Launch command:

```bash
cd /work/dfm/HRM-Text
ROOT_TS=20260613_100k_150k
tmux new-session -d -s dfm5_xxs_eval_100k_150k \
  "cd /work/dfm/HRM-Text && \
   CKPT_TAGS=step_100000,step_150000 \
   EVAL_EPOCHS=0.5521769236437283,0.8282653854655924 \
   CKPT_PATH=checkpoints/dfm5/XXS \
   GPUS=0,1,2,3,4,5,6,7 \
   LOG_ROOT_BASE=logs/eval/dfm5_XXS_100k_150k_full_${ROOT_TS} \
   DFM_LOG_ROOT_BASE=logs/dfm_evals/dfm5_XXS_100k_150k_full_${ROOT_TS} \
   EUROEVAL_LOG_ROOT_BASE=logs/euroeval/dfm5_XXS_100k_150k_full_${ROOT_TS} \
   RUN_EUROEVAL=1 \
   LITE_EVAL=0 \
   QUEUE_ORDER=heavy_first \
   MAX_RETRIES=3 \
   WANDB_SYNC=1 \
   WANDB_PROJECT=DFM5 \
   WANDB_RUN_ID=2tv9u438 \
   WANDB_RUN_NAME=dfm5-XXS \
   MODEL_PREFIX=hrm-dfm5-XXS \
   STANDARD_BATCH_SIZE=16 \
   DFM_BATCH_SIZE=16 \
   IFEVAL_BATCH_SIZE=16 \
   EUROEVAL_BATCH_SIZE=8 \
   EUROEVAL_BATCH_TIMEOUT_MS=25 \
   EUROEVAL_BIN=/work/dfm/HRM-Text/scripts/euroeval_api_no_flash_attn_guard.py \
   EUROEVAL_DATASET_GROUPS='angry-tweets,scala-da,dansk;multi-wiki-qa-da,nordjylland-news;danske-talemaader,danish-citizen-tests,hellaswag-da;ifeval-da,valeu-da;sst5,scala-en,conll-en;squad,cnn-dailymail;life-in-the-uk,hellaswag,ifeval;bfcl-v2,valeu-en' \
   scripts/schedule_multiple_checkpoint_evals.sh 2>&1 | \
   tee logs/dfm5_xxs_eval_100k_150k_${ROOT_TS}.log"
```

Initial status:

```text
QUEUED 352 jobs for 2 checkpoints
WORKERS 2473337 2473338 2473339 2473340 2473341 2473342 2473343 2473344
```

The first eight jobs were IFEval-DA shards for `step_100000`, one per GPU.
Server logs under
`logs/dfm_evals/dfm5_XXS_100k_150k_full_20260613_100k_150k/step_100000/ifeval_shard_*/step_100000/server.log`
showed live generation progress, and `nvidia-smi` showed 100% GPU utilization
on all eight devices shortly after launch.
