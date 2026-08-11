---
type: Operational Record
title: 'Update 2026-06-13: For future multi-checkpoint scheduler runs, EuroEval defaults
  to one dataset'
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Update 2026-06-13:
  For future multi-checkpoint scheduler runs, EuroEval defaults to one dataset.'
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
# Update 2026-06-13: For future multi-checkpoint scheduler runs, EuroEval defaults to one dataset

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-06-13. Confidence: high. For future multi-checkpoint scheduler
runs, EuroEval defaults to one dataset per queue job when all of the following
are true: `RUN_EUROEVAL=1`, `EUROEVAL_LANGUAGES=da,en`,
`EUROEVAL_DATASET_GROUPS` is unset, `EUROEVAL_DATASETS` is unset, and
`EUROEVAL_TASKS` is unset. Explicit dataset groups, dataset lists, or task
lists still override this default. A dry run verified 20 EuroEval jobs for one
checkpoint:

```text
angry-tweets
scala-da
dansk
multi-wiki-qa-da
nordjylland-news
danske-talemaader
danish-citizen-tests
hellaswag-da
ifeval-da
valeu-da
sst5
scala-en
conll-en
squad
cnn-dailymail
life-in-the-uk
hellaswag
ifeval
bfcl-v2
valeu-en
```
