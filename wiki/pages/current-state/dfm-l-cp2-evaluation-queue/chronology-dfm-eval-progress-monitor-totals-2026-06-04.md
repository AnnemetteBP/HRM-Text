---
type: Operational Record
title: DFM eval progress monitor totals (2026-06-04)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM eval progress
  monitor totals (2026-06-04).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm-l-cp2-evaluation-queue.md
---
# DFM eval progress monitor totals (2026-06-04)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM eval progress monitor totals, 2026-06-04. Confidence: high.

`scripts/watch_multi_checkpoint_eval_progress.py` now has known dataset totals
for DALA, GEC-DALA, and MultiWikiQA, so active dfm-evals jobs show
`completion x/y` instead of `completion x/?` for those tasks. Verified dataset
sizes are:

- `dfm_evals/dala`: `2048` samples for `giannor/dala`, split `test`.
- `dfm_evals/gec_dala`: `1024` samples for `giannor/dala_gen_v3`, split
  `test`.
- `dfm_evals/multi_wiki_qa`: `2048` samples for the default public
  MultiWikiQA test mini split; shard `0/2` therefore has `1024` samples.

The 200K EMA lite eval monitor snapshot after the patch showed DALA
`1506/2048`, GEC-DALA `212/512`, and MultiWikiQA `906/1024`.
