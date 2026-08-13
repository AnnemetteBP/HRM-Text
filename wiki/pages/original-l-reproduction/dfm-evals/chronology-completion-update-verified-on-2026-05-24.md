---
type: Operational Record
title: Completion update, verified on (2026-05-24)
description: 'Chronological record from dfm-evals: Completion update, verified on
  (2026-05-24).'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction/dfm-evals.md
---
# Completion update, verified on (2026-05-24)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Completion update, verified on 2026-05-24: dfm-evals finished for all four original Sapient L checkpoints. No dfm-evals wrapper, shim, or sync watcher processes remained; only the unrelated ongoing mixed L training process was still running. Epoch 2 MultiWikiQA completed with `dfm_eval/multi_wiki_qa/exact_match/mean = 0.01074` and `dfm_eval/multi_wiki_qa/f1/mean = 0.04904`, and was manually synced to W&B run `origLclean`. A duplicate zero-sample partial epoch 2 MultiWikiQA `.eval` file remains from the stopped duplicate process and should be ignored. Confidence: high.
