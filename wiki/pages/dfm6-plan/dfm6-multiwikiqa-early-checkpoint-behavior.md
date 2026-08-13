---
type: Plan Record
title: DFM6 MultiWikiQA Early-Checkpoint Behavior
description: 'Part of DFM6 Plan: DFM6 MultiWikiQA Early-Checkpoint Behavior.'
tags:
- dfm6
- data
- training
- evaluation
status: stable
last_updated: 2026-06-28
confidence: high
part_of: /pages/dfm6-plan.md
---
# DFM6 MultiWikiQA Early-Checkpoint Behavior

Part of [DFM6 Plan](/pages/dfm6-plan.md).

Last updated: 2026-06-22
Confidence: high
Scope: Local diagnosis of DFM6 XL-GAS2 `step_50k`, `step_100k`, and
`step_150k` MultiWikiQA eval outputs.

The poor-looking MultiWikiQA exact-match scores at `step_150000` are not best
explained by missing training data. The DFM6 tokenized union contains
`oliverkinch_multi_wiki_qa_high_quality__da__train-00000-of-00001.parquet`, and
`data_io/prefix_config_dfm6.yaml` repeats the
`oliverkinch_multi_wiki_qa_high_quality__` prefix `10` times.

Observed local metrics:

| Checkpoint | DFM F1 | DFM EM | EuroEval F1 | EuroEval EM |
|---|---:|---:|---:|---:|
| `step_50000` | `0.2964` | `0.0005` | `28.62` | `0.00` |
| `step_100000` | `0.3453` | `0.0029` | `33.14` | `0.21` |
| `step_150000` | `0.3823` | `0.0049` | `35.45` | `0.00` |

The F1 trend is improving, while exact match remains near zero. An
instance-level scan of the DFM eval outputs found that at `step_150000` about
`65%` of outputs contain a reference answer somewhere and about `62%` contain a
reference answer on the first output line, but `100%` of outputs stop by hitting
`max_tokens=32`. Typical bad outputs start with the right answer and then emit
bullets, alternatives, or repetition, so the exact-match scorer evaluates the
whole over-generated string rather than the first answer span.

Current interpretation: early DFM6 checkpoints often know how to extract the
answer span but have not yet learned the strict "answer with max 3 words and
stop" behavior. For future diagnosis, compare F1 and first-line/reference
containment alongside exact match, and consider a controlled rerun with tighter
stop/max-token settings or first-line answer extraction before treating this as
a data-coverage failure.
