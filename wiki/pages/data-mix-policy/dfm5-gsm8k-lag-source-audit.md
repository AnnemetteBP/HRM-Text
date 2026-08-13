---
type: Policy Record
title: DFM5 GSM8k Lag Source Audit
description: 'Part of Data Mix Policy: DFM5 GSM8k Lag Source Audit.'
tags:
- data
- licensing
- provenance
- privacy
status: stable
last_updated: 2026-06-17
confidence: high
part_of: /pages/data-mix-policy.md
---
# DFM5 GSM8k Lag Source Audit

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Last updated: 2026-06-15
Confidence: high for local audit files and analytics rows; medium for causal
interpretation.
Scope: Original Sapient sources omitted from DFM5 and their likely relevance
to GSM8k-style performance.

The local omitted-task audit shows `321` original Sapient tasks excluded from
DFM5, with `1,407,414,834` original covered tokens over four epochs
(`351,853,709` tokens/epoch). A keyword scan for explicit math/science/logic
terms among omitted tasks found only `91,628,200` original covered tokens over
four epochs (`22,907,050` tokens/epoch), dominated by ReClor, SciBench, and
TweetQA-like tasks rather than GSM8k-style arithmetic:

```text
Platypus__reclor.jsonl                         47,467,200 covered tokens
tasksource__reclor.parquet                      4,693,360 covered tokens
Platypus__scibench.jsonl                        5,165,960 covered tokens
TweetQA/QReCC/MS MARCO-style QA residuals       remaining matched tokens
```

The obvious original Sapient GSM8k/math/science families are not omitted:
`gsm8k`, `mathqa`, `aqua`, `openbookqa`, `qasc`, `sciq`, `strategyqa`, and
`quartz` are allow-overridden and present in `data/show_analytics_dfm5.md`.
A keyword comparison of those included families gives about the same exposure
per epoch in original Sapient and DFM5:

```text
original Sapient keyword set: 736,505,857 covered tokens / 4 epochs
DFM5 keyword set:             920,611,503 covered tokens / 5 epochs
both are about 184M tokens/epoch
```

Therefore, the current best explanation for DFM5-L's early GSM8k lag is not a
missing direct GSM8k/math source from the original mix. More plausible causes
are dilution by the much larger DFM5 epoch, loss of high-leverage non-math
instruction/formatting effects, differences in EMA/checkpoint dynamics, or the
need for more GSM8k-like elementary arithmetic post-training.
