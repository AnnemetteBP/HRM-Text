---
type: Operational Record
title: 2026-06-15 Original Sapient L Backfill Into DFM5
description: 'Part of Current State: 2026-06-15 Original Sapient L Backfill Into DFM5.'
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
# 2026-06-15 Original Sapient L Backfill Into DFM5

Part of [Current State](/pages/current-state.md).

Confidence: high for local source artifacts, successful W&B sync, and remote
run metadata/summary verification.

The original Sapient L reproduction run was backfilled into a new W&B run in
project `DFM5`:

```text
project: DFM5
run id:  original-sapient-L-dfm5-backfill-20260615
name:    original Sapient L backfilled
url:     https://wandb.ai/peter-sk-sdu/DFM5/runs/original-sapient-L-dfm5-backfill-20260615
```

The backfill script is:

```text
scripts/backfill_original_sapient_l_to_dfm5.py
```

It replays scalar training rows from:

```text
wandb/merged-20260524-76sygh18-clean/history.jsonl
```

and rebuilds evaluation rows from local artifacts:

```text
logs/eval/original_sapient_L/epoch_{1,2,3,4}.log
logs/dfm_evals/original_sapient_L_lite_all_checkpoints_20260603T213010/epoch_{1,2,3,4}
logs/euroeval/original_sapient_L/epoch_{1,2,3,4}/euroeval_benchmark_results.jsonl
```

The true original Sapient L epoch-step mapping used for eval rows is:

```text
epoch 1 -> step 81478
epoch 2 -> step 162961
epoch 3 -> step 244443
epoch 4 -> step 325928
```

Command used:

```bash
cd /work/dfm/HRM-Text
python scripts/backfill_original_sapient_l_to_dfm5.py \
  2>&1 | tee logs/wandb_backfill_original_sapient_l_to_dfm5_20260615.log
```

The dry run and final manifest are in:

```text
logs/wandb_backfill_original_sapient_l_to_dfm5_dryrun_20260615.log
logs/wandb_backfill_original_sapient_l_to_dfm5_20260615.log
logs/wandb_backfill_original_sapient_l_to_dfm5_manifest.json
```

Final manifest:

```text
training_rows: 65186
total_rows:    65190
eval_steps:    [81478, 162961, 244443, 325928]
metric counts: epoch 1=460, epoch 2=455, epoch 3=460, epoch 4=460
```

Representative verified summary keys include `train/loss`, `eval/MMLU/acc`,
`eval/BoolQ/acc`, `eval/GSM8k/acc`,
`dfm_eval/nordjyllandnews/rouge2/mean`,
`dfm_eval/humaneval/verify_sanitized/accuracy`,
`euroeval/da/summarization/nordjylland-news/chr_f3pp`, and
`headline_avg/{danish,english,math_code,overall}`.
