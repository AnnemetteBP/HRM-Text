---
type: Policy Record
title: Kept Sapient Original Sampling Exposure
description: 'Part of Data Mix Policy: Kept Sapient Original Sampling Exposure.'
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
# Kept Sapient Original Sampling Exposure

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Last updated: 2026-06-12
Confidence: high
Scope: Current filtered Sapient source tree after the DFM5 policy update,
measured against `data/show_analytics_original_sapient.md` at the original
Sapient sampling rate.

The current filtered tree under `data/filtered_sources/sapient_cleaned`
contains `4,892` symlinks, of which one is `README.md`. The remaining `4,891`
data files match original Sapient task names in
`data/show_analytics_original_sapient.md`; `321` original analytics tasks are
not kept by the current source filter.

At the original Sapient sampling rate:

| Subset | Covered tokens over 4 epochs | Tokens/epoch |
|---|---:|---:|
| Full original Sapient | `56,140,714,711` | `14,035,178,678` |
| Current kept Sapient subset | `54,733,299,877` | `13,683,324,969` |
| Currently excluded `321` tasks | `1,407,414,834` | `351,853,709` |

The kept subset preserves about `97.49%` of the original Sapient sampled-token
exposure. The excluded `321` tasks account for about `2.51%` of the original
sampled-token exposure, despite being large in raw bytes, because many broad
FLAN/tasksource files were capped by the original prefix config.

Update, 2026-06-12. Confidence: high. The concrete DFM5 exclusion lists were
materialized locally from `data/show_analytics_original_sapient.md` minus the
current symlink-derived task set in `data/filtered_sources/sapient_cleaned`:

```text
logs/data_audits/dfm5_excluded_original_sapient_tasks.tsv
logs/data_audits/dfm5_excluded_original_sapient_sources.tsv
logs/data_audits/dfm5_excluded_original_sapient_tasks.summary.json
```

The `321` excluded original Sapient tasks break down as `298` FLAN tasks, `21`
Tasksource tasks, and `2` Platypus tasks. By broad policy reason/name pattern:
`46` are translation/news/search, `160` are reviews/opinions/email, `102` are
social/toxicity/PII-risk, `20` are dialogue/chat/user-conversation, and `3`
are eval/book/textbook-risk. These buckets are explanatory groupings; the
source of truth is the TSV list.
