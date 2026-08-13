---
type: Operational Record
title: 'Update 2026-06-13: The DFM5 XXS step-50K full evaluation campaign is synced
  to'
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Update 2026-06-13:
  The DFM5 XXS step-50K full evaluation campaign is synced to.'
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
# Update 2026-06-13: The DFM5 XXS step-50K full evaluation campaign is synced to

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-06-13. Confidence: high. The DFM5 XXS step-50K full evaluation
campaign is synced to W&B run `2tv9u438` in project `DFM5`. Local status for
the eight EuroEval groups:

```text
GPU0 done json_objects=3 metrics=yes
GPU1 done json_objects=2 metrics=yes
GPU2 done json_objects=3 metrics=yes
GPU3 done json_objects=2 metrics=yes
GPU4 done json_objects=3 metrics=yes
GPU5 done json_objects=2 metrics=yes
GPU6 done json_objects=3 metrics=yes
GPU7 done json_objects=2 metrics=yes
```

The W&B summary API did not list eval keys, but a full remote history scan of
`peter-sk-sdu/DFM5/2tv9u438` found `382` keys starting with `eval/`,
`dfm_eval/`, or `euroeval/`, confirming that the sidecar eval logs reached the
remote run history. This matches previous W&B behavior where summary keys can
lag or omit sidecar-logged eval rows on an active training run.

A saved DFM5 workspace view was created for the 19 headline eval metrics plus
training/parameter panels:

```text
name: DFM5 headline metrics
url:  https://wandb.ai/peter-sk-sdu/DFM5?nw=2q3uq7mqioe
```

The view has four sections:

```text
Danish Headline Metrics:
  dfm_eval/dala/linguistic-acceptability/dfm_evals_macro_f1
  dfm_eval/danish-citizen-tests/knowledge/accuracy
  dfm_eval/gec_dala/exact_match/mean
  dfm_eval/generative-talemaader/model_graded_fact/accuracy
  dfm_eval/ifeval-da/instruction_following/final_acc
  dfm_eval/multi_wiki_qa/f1/mean
  dfm_eval/nordjyllandnews/rouge2/mean
  dfm_eval/piqa/piqa_scorer/accuracy
  dfm_eval/wmt24pp-en-da/chrf3pp/mean

English Headline Metrics:
  eval/ARC/acc
  eval/BoolQ/acc
  eval/DROP/f1
  eval/HellaSwag/acc
  eval/MMLU/acc
  eval/Winogrande/acc
  dfm_eval/govreport/rouge2/mean

Math & Code Headline Metrics:
  eval/GSM8k/acc
  eval/MATH/acc
  dfm_eval/humaneval/verify_sanitized/accuracy

Training Metrics & Params:
  train/loss
  train/accuracy
  train/exact_accuracy
  train/lr
  bp_steps
  scalar cards for config lr/global batch/epochs/layers
```

Standard eval panels use `eval/epoch`; DFM-eval panels use
`dfm_eval/epoch`; training panels use `_step`. Script and manifest:

```text
scripts/create_dfm5_headline_workspace.py
logs/wandb_workspace_specs/dfm5_headline_metrics.json
logs/wandb_create_dfm5_headline_workspace_20260613.log
```
