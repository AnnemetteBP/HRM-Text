---
type: Operational Record
title: 2026-06-10 DFM4 XL-DDP Step 700K EMA Lite Eval Grooming
description: 'Part of Current State: 2026-06-10 DFM4 XL-DDP Step 700K EMA Lite Eval
  Grooming.'
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
# 2026-06-10 DFM4 XL-DDP Step 700K EMA Lite Eval Grooming

Part of [Current State](/pages/current-state.md).

Confidence: high for local artifacts and process state; high for W&B API checks.

The `step_700000` EMA lite eval for `checkpoints/dfm4/XL-ddp` completed
locally under:

```text
logs/eval/dfm4_XL_ddp_ema_lite_700k_20260609_lowbs/step_700000
logs/dfm_evals/dfm4_XL_ddp_ema_lite_700k_20260609_lowbs/step_700000
```

Strict local audit passed for all standard lite tasks:

```text
GSM8k, DROP, MMLU, HellaSwag, ARC, Winogrande, BoolQ, MATH
```

Strict local audit passed for all DFM lite tasks:

```text
danish_citizen_tests, dala, gec_dala, wmt24pp_en_da, multi_wiki_qa,
piqa, generative_talemaader, govreport, nordjyllandnews, humaneval,
ifeval_da
```

The last missing tasks were rerun on GPU3 in the foreground queue
`manual_gpu3_gec_multi_fg_20260610T005636`. `gec_dala` completed `512/512`
samples at `2026-06-10T01:40:08+02:00`; `multi_wiki_qa` completed `1024`
samples at `2026-06-10T01:57:06+02:00`. `gec_dala` was slow at batch size 1
under concurrent training, taking about 44 minutes. The earlier detached GPU2
rerun failed because it was launched as a plain background child from a
short-lived shell; use foreground, tmux, or `nohup`/`setsid` for detached
manual queues.

Final local merge command:

```bash
cd /work/dfm/HRM-Text
FINAL_MERGE_ONLY=1 \
CKPT_TAG=step_700000 \
EVAL_EPOCH=1.9112836727227056 \
CKPT_PATH=checkpoints/dfm4/XL-ddp \
LOG_ROOT=logs/eval/dfm4_XL_ddp_ema_lite_700k_20260609_lowbs/step_700000 \
DFM_LOG_ROOT=logs/dfm_evals/dfm4_XL_ddp_ema_lite_700k_20260609_lowbs/step_700000 \
WANDB_SYNC=1 \
WANDB_PROJECT='Original Plus Mixed Danish Instruction Rich L' \
WANDB_RUN_ID=dfm4xlddpclean \
WANDB_RUN_NAME='dfm4-XL-ddp clean lite history' \
EVAL_PREFIX=lite_eval_ema \
DFM_EVAL_PREFIX=lite_dfm_eval_ema \
LITE_EVAL=1 \
LITE_SHARD_INDEX=0 \
NO_EMA=0 \
bash scripts/schedule_checkpoint_evals.sh
```

The final local merge ended with `FINAL_MERGE_END` at
`2026-06-10T02:00:01+02:00`. Per-task merged JSON files were written under each
task directory, for example:

```text
standard_shards/BoolQ/merged_metrics.json
gec_dala/merged_metrics.json
multi_wiki_qa/merged_metrics.json
merged_ifeval_da_metrics.json
```

Important W&B caveat, 2026-06-10. The target run
`peter-sk-sdu/Original Plus Mixed Danish Instruction Rich L/dfm4xlddpclean` was
actively training while the eval backfill was attempted. Separate W&B SDK and
CLI append attempts created correct local `.wandb` history rows, but the rows
did not become visible through the W&B API while the active training process
owned the run. Verified examples:

```text
local backfill .wandb row 1: _step=717690, lite_eval_ema/epoch=1.9112836727227056,
  lite_eval_ema/BoolQ/acc=0.4443, lite_eval_ema/MATH/acc=0.1646
local backfill .wandb row 2: _step=717691, lite_dfm_eval_ema/epoch=1.9112836727227056,
  lite_dfm_eval_ema/multi_wiki_qa/f1/mean=0.823548559665865,
  lite_dfm_eval_ema/gec_dala/exact_match/mean=0.3515625
```

The remote API still showed the previous EMA lite point at
`lite_eval_ema/epoch = 1.638238688802462` and
`lite_dfm_eval_ema/epoch = 1.638238688802462`. Conclusion: the evals are fully
run and merged locally, but remote W&B history sync for the live
`dfm4xlddpclean` run remains pending until the training run is paused/stopped or
the metrics are logged by the active training process itself. Do not treat the
absence of `epoch_1p9112836727227056` keys in W&B as missing local evals.
