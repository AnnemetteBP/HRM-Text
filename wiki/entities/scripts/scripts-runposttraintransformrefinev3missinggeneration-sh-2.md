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

Added on 2026-06-05. Confidence: high.

Convenience wrapper for generating the remaining source-target-expanded
`posttrain_transform_refine` shards. It uses the fresh local Gemma 4 31B IT
model, the `chat` endpoint, `CLIENT_CONCURRENCY=32`, `JUDGE_QUALITY=1`,
`JUDGE_RETRIES=2`, and writes into:

```text
data/generated_posttrain_transform_refine
```

The queued shard root is:

```text
data/synthetic_request_shards_posttrain_transform_refine_v3_missing
```
