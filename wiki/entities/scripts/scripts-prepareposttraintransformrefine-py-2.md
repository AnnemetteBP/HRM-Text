---
type: Software Reference
title: '`scripts/prepare_posttrain_transform_refine.py`'
description: 'Part of Script Entities: `scripts/prepare_posttrain_transform_refine.py`.'
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
# `scripts/prepare_posttrain_transform_refine.py`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-04. Confidence: high for local conversion/request-generation
execution; medium for later teacher-model generation until run.

Prepares the `posttrain_transform_refine` dataset family. Subcommands:

- `convert-existing`: converts `grammarly/coedit` and a filtered
  transformation-style subset of `Muennighoff/natural-instructions` into ready
  `condition/instruction/response` Parquet.
- `make-synthetic-requests`: builds teacher-model request JSONL files for five
  transformation tasks in Danish and English.
- `export-seed-texts`: writes the English and Danish source-text pools used for
  synthetic request generation to JSONL plus a manifest.
- `shard-synthetic-requests`: splits request JSONL files into small queue
  shards for multi-GPU teacher generation.
- `generate-synthetic`: calls an OpenAI-compatible teacher model endpoint,
  intended for Gemma 4 31B or 26B-A3.
- `audit-generated`: rejudges accepted generated JSONL rows through an
  OpenAI-compatible judge endpoint and writes non-mutating audit JSONL plus a
  summary.
- `convert-generated`: writes accepted synthetic generations to ready Parquet.

Verified local outputs:

```text
posttrain_coedit rows: 70,783
posttrain_superni_filtered rows: 500,000 across 64 tasks
synthetic request files: 10 x 50,000 requests
synthetic request shards: 500 x 1,000 requests
seed export: 1,119,746 English rows and 99,538 Danish rows
```

The audit/regeneration policy is audit-first: generate the remaining pending
rows with `--judge-quality`, then audit the old accepted rows. Any row with an
unhappy judge must be dropped and regenerated; judge-failed rows should not be
converted into the post-training data.
