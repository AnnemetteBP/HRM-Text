---
type: Operational Record
title: 2026-06-11 DBC Author/Article Audit Plan
description: 'Part of Current State: 2026-06-11 DBC Author/Article Audit Plan.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# 2026-06-11 DBC Author/Article Audit Plan

Part of [Current State](/pages/current-state.md).

Confidence: high for local schema inspection and script syntax; medium until
judge results are reviewed.

Added a non-mutating audit script for the DBC author/article converted datasets:

```bash
python scripts/audit_dbc_article_datasets.py \
  --base-url http://127.0.0.1:8100/v1 \
  --model posttrain-gemma-teacher \
  --sample-rate 0.1 \
  --concurrency 8 \
  --audit-root logs/dbc_article_audit/sample_10pct \
  --force
```

Default audited files:

```text
data/converted_sources/dbc/dbc-farfatterweb.parquet: 2,831 rows
data/converted_sources/dbc/dbc-faktalink.parquet:    5,991 rows
```

The judge prompt is dataset-aware: Forfatterweb rows must be plausible Danish
author-article sections matching the requested author/heading, while Faktalink
rows must be plausible Danish explanatory article sections matching the
requested topic/heading. The prompt rejects wrong-language, empty,
metadata-only, boilerplate, OCR-corrupted, unrelated, reference/URL-dump, and
too-fragmentary rows, but explicitly does not reject just because the judge
cannot externally verify every factual claim.
