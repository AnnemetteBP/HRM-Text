---
type: Software Reference
title: '`scripts/audit_dbc_article_datasets.py`'
description: 'Part of Script Entities: `scripts/audit_dbc_article_datasets.py`.'
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
# `scripts/audit_dbc_article_datasets.py`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-11. Confidence: high for local syntax, schema inspection, and
row counts; medium until a judge run has been executed.

Non-mutating audit for DBC article/author instruction datasets. Defaults:

```text
data/converted_sources/dbc/dbc-farfatterweb.parquet: 2,831 rows
data/converted_sources/dbc/dbc-faktalink.parquet:    5,991 rows
```

The script reads converted Parquet rows with `instruction` and `response`,
then asks an OpenAI-compatible judge whether the row is useful Danish
article-section training data. The prompt is dataset-aware:

- Forfatterweb: response should be a plausible Danish section for the requested
  author/article heading.
- Faktalink: response should be a plausible Danish explanatory article section
  for the requested topic/heading.

It rejects wrong-language, empty, metadata-only, boilerplate, OCR-corrupted,
mostly-reference/URL, unrelated, too-fragmentary, or low-quality article prose.
It does not reject merely because the judge cannot externally verify every
factual claim.

Suggested first pass:

```bash
python scripts/audit_dbc_article_datasets.py \
  --base-url http://127.0.0.1:8100/v1 \
  --model posttrain-gemma-teacher \
  --sample-rate 0.1 \
  --concurrency 8 \
  --audit-root logs/dbc_article_audit/sample_10pct \
  --force
```
