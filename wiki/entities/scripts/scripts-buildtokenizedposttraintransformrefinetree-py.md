---
type: Software Reference
title: '`scripts/build_tokenized_posttrain_transform_refine_tree.py`'
description: 'Part of Script Entities: `scripts/build_tokenized_posttrain_transform_refine_tree.py`.'
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
# `scripts/build_tokenized_posttrain_transform_refine_tree.py`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-04. Confidence: high.

Builds a filtered tokenized union for post-training. It links only allowlisted
task prefixes from:

```text
data/tokenized_dfm4
data/tokenized_posttrain_transform_refine_existing
data/tokenized_posttrain_transform_refine_synthetic
```

This is necessary because `data_io/sample_tokenized.py` samples unmatched tasks
fully by default; the post-training mix must therefore avoid pointing directly
at the full DFM4 tokenized tree. Verified local manifest linked `4,117` tasks:
`4,115` selected existing DFM4/relevant tasks plus `2` new post-training tasks.
