---
type: Operational Record
title: 'Update 2026-06-13: scripts/schedulemultiplecheckpointevals.sh supports opportunistic
  multi-checkpoint scheduling: one shared jobs.tsv is consumed'
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Update 2026-06-13:
  scripts/schedulemultiplecheckpointevals.sh supports opportunistic multi-checkpoint
  scheduling: one shared jobs.tsv is consumed.'
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
# Update 2026-06-13: scripts/schedulemultiplecheckpointevals.sh supports opportunistic multi-checkpoint scheduling: one shared jobs.tsv is consumed

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-06-13. Confidence: high. `scripts/schedule_multiple_checkpoint_evals.sh`
supports opportunistic multi-checkpoint scheduling: one shared `jobs.tsv` is
consumed by one worker per GPU, and each worker pops the next checkpoint job
whose checkpoint files are ready. This lets checkpoint N+1 start on free GPUs
while long-running shards for checkpoint N are still active. Standard and
DFM-eval tasks already used this pattern.

The script now also supports grouped EuroEval jobs with
`EUROEVAL_DATASET_GROUPS`. When set, each semicolon-separated dataset group is
queued as a separate `euroeval` job instead of one monolithic EuroEval job.
This matches the DFM5 step-50K manual split and prevents one GPU from owning
all EuroEval work.

Dry-run verification:

```bash
cd /work/dfm/HRM-Text
CKPT_TAGS=step_a,step_b \
EVAL_EPOCHS=0.1,0.2 \
CKPT_PATH=checkpoints/dfm5/XXS \
LOG_ROOT_BASE=logs/eval/dryrun_multi_ckpt_opportunistic2 \
DFM_LOG_ROOT_BASE=logs/dfm_evals/dryrun_multi_ckpt_opportunistic2 \
EUROEVAL_LOG_ROOT_BASE=logs/euroeval/dryrun_multi_ckpt_opportunistic2 \
RUN_EUROEVAL=1 \
LITE_EVAL=1 \
WANDB_PROJECT=DFM5 \
WANDB_RUN_ID=2tv9u438 \
WANDB_RUN_NAME=dfm5-XXS \
EUROEVAL_DATASET_GROUPS='angry-tweets,scala-da,dansk;multi-wiki-qa-da,nordjylland-news;danske-talemaader,danish-citizen-tests,hellaswag-da;ifeval-da,valeu-da;sst5,scala-en,conll-en;squad,cnn-dailymail;life-in-the-uk,hellaswag,ifeval;bfcl-v2,valeu-en' \
DRY_RUN=1 \
scripts/schedule_multiple_checkpoint_evals.sh
```

The dry run queued `54` jobs for two lite checkpoints, including eight
EuroEval dataset-group jobs per checkpoint. `bash -n` passed for both
`scripts/schedule_multiple_checkpoint_evals.sh` and
`scripts/schedule_checkpoint_evals.sh`.
