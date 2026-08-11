---
type: Policy Record
title: DFM5 Danish Token Accounting
description: 'Part of Data Mix Policy: DFM5 Danish Token Accounting.'
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
# DFM5 Danish Token Accounting

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Added on 2026-06-17. Confidence: high for local analytics parsing and token
counts from `data/show_analytics_dfm5.md`.

For the current DFM5 sample, `data/show_analytics_dfm5.md` reports
`128,605,312,816` total unique candidate tokens and `178,029,895,476` covered
tokens across 5 epochs, i.e. about `35.606B` tokens per epoch.

Strictly Danish monolingual/reference-style sources have about
`5,232,200,438` unique candidate tokens:

- Danish DynaWord export objectives: `300,492,627`
- Danish instruction/reference sources (`dbc`, `laerebogen`, `lexdk`,
  `oliverkinch_*` Danish BT/reference/instruction, `synquid_*` Danish
  instruction tasks): `4,727,840,172`
- `transformations-danish-danish`: `203,867,639`

Danish-involved sources, including cross-lingual Danish translation and
transformation tasks but excluding the maybe-multilingual
`synquid_wildchat_100k_qwen_messages`, have about `15,282,372,741` unique
candidate tokens. Including that maybe-multilingual WildChat slice gives about
`15,502,966,407` unique candidate tokens.

Current DFM5 per-epoch sampled exposure is lower because of caps/repeats:

- strict Danish monolingual/reference-style: about `4,368,304,924`
  tokens/epoch;
- Danish-involved including cross-lingual, excluding maybe-multilingual
  WildChat: about `6,448,926,031` tokens/epoch;
- Danish-involved including maybe-multilingual WildChat: about
  `6,534,845,485` tokens/epoch.

Clarification added on 2026-06-17. Confidence: high. The DFM5-linked Danish
available-token pool should be read from `data/show_analytics_dfm5.md`, not by
blindly scanning every Danish-looking directory under `data/tokenized_mixed`,
because that root still contains legacy `danish_dynaword__...` files that are
not linked into DFM5. The DFM5-linked source clusters are:

| Cluster | Files | Available tokens |
|---|---:|---:|
| OPUS Danish-English translation | `1` | `6,037,616,160` |
| Oliver Kinch Danish translation | `4` | `3,541,450,520` |
| Laerebogen with follow-ups | `7` | `2,563,212,663` |
| DBC articles/reviews | `24` | `1,800,302,760` |
| Synthetic transformations Danish-English / English-Danish | `659` | `355,640,602` |
| Danish DynaWord synthetic objectives | `475` | `300,492,627` |
| Synquid WildChat Qwen messages (maybe multilingual) | `1` | `220,593,666` |
| Synthetic transformations Danish-Danish | `250` | `203,867,639` |
| Synquid Danish instruction/reasoning | `4` | `202,263,632` |
| Synquid Danish translation/MT | `2` | `115,465,021` |
| Oliver Kinch Danish BT/reference/instruction | `10` | `88,741,738` |
| LexDK encyclopedic articles | `1` | `73,319,379` |
