---
type: Software Reference
title: '`scripts/prepare_posttrain_transform_refine.sh`'
description: 'Part of Script Entities: `scripts/prepare_posttrain_transform_refine.sh`.'
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
# `scripts/prepare_posttrain_transform_refine.sh`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-04. Confidence: high.

Stage runner for the post-training transformation-refine pipeline. Key stages:

```bash
scripts/prepare_posttrain_transform_refine.sh inventory
scripts/prepare_posttrain_transform_refine.sh download-existing
scripts/prepare_posttrain_transform_refine.sh convert-existing
scripts/prepare_posttrain_transform_refine.sh make-synthetic-requests
scripts/prepare_posttrain_transform_refine.sh shard-synthetic-requests
scripts/prepare_posttrain_transform_refine.sh generate-synthetic
scripts/prepare_posttrain_transform_refine.sh convert-synthetic
scripts/prepare_posttrain_transform_refine.sh tokenize-existing
scripts/prepare_posttrain_transform_refine.sh tokenize-synthetic
scripts/prepare_posttrain_transform_refine.sh build-tokenized-tree
scripts/prepare_posttrain_transform_refine.sh sample
```
