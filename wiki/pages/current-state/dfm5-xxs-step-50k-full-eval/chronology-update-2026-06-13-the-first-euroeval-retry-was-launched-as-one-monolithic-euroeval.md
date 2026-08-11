---
type: Operational Record
title: 'Update 2026-06-13: The first EuroEval retry was launched as one monolithic
  EuroEval'
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Update 2026-06-13:
  The first EuroEval retry was launched as one monolithic EuroEval.'
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
# Update 2026-06-13: The first EuroEval retry was launched as one monolithic EuroEval

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-06-13. Confidence: high. The first EuroEval retry was launched as
one monolithic EuroEval job on GPU0 because `scripts/schedule_checkpoint_evals.sh`
enqueues only a single `euroeval` job and `scripts/run_euroeval_on_checkpoint.sh`
runs one EuroEval client/server pair. That underused the available GPU
headroom. The single-GPU run was stopped and replaced with eight explicit
dataset groups, one per GPU, using `EUROEVAL_DATASETS`.

Default EuroEval `--language da --language en` resolves to these 20 datasets:

```text
angry-tweets, scala-da, dansk, multi-wiki-qa-da, nordjylland-news,
danske-talemaader, danish-citizen-tests, hellaswag-da, ifeval-da, valeu-da,
sst5, scala-en, conll-en, squad, cnn-dailymail, life-in-the-uk, hellaswag,
ifeval, bfcl-v2, valeu-en
```

Parallel groups launched under:

```text
logs/euroeval/dfm5_XXS_step50000_parallel_20260613/
```

Group map:

```text
GPU0: angry-tweets, scala-da, dansk
GPU1: multi-wiki-qa-da, nordjylland-news
GPU2: danske-talemaader, danish-citizen-tests, hellaswag-da
GPU3: ifeval-da, valeu-da
GPU4: sst5, scala-en, conll-en
GPU5: squad, cnn-dailymail
GPU6: life-in-the-uk, hellaswag, ifeval
GPU7: bfcl-v2, valeu-en
```

Each group uses a separate local HRM OpenAI server and syncs metrics directly
to W&B project `DFM5`, run id `2tv9u438`, at `EVAL_EPOCH=0.276088`. This
works, but the scheduler should be generalized later so EuroEval dataset
groups are first-class queued jobs rather than one monolithic job.
