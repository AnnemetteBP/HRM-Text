---
type: Software Reference
title: '`scripts/run_posttrain_transform_refine_v3_missing_generation.sh`'
description: 'Part of Script Entities: `scripts/run_posttrain_transform_refine_v3_missing_generation.sh`.'
tags:
- scripts
- software
- catalog
- operations
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# `scripts/run_posttrain_transform_refine_v3_missing_generation.sh`

Part of [Script Entities](/entities/scripts.md).

Launch helper for the next post-training synthetic generation run. It should be
started only when GPUs are free.

Responsibilities:

- use fresh Gemma 4 31B IT at
  `data/models/google/gemma-4-31B-it-fresh-20260604`;
- use `SHARD_ROOT=data/synthetic_request_shards_posttrain_transform_refine_v3_missing`;
- use `GENERATED_ROOT=data/generated_posttrain_transform_refine`;
- generate only the 550k missing/regenerated rows:
  `*_da_da`, `*_da_en`, and `past_tense_rewrite_en_da`.

Command:

```bash
cd /work/dfm/HRM-Text
scripts/run_posttrain_transform_refine_v3_missing_generation.sh
```
