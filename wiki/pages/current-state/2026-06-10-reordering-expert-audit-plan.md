---
type: Operational Record
title: 2026-06-10 Reordering Expert Audit Plan
description: 'Part of Current State: 2026-06-10 Reordering Expert Audit Plan.'
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
# 2026-06-10 Reordering Expert Audit Plan

Part of [Current State](/pages/current-state.md).

Confidence: high for local row counts and script syntax; medium for judge
quality until the first audit sample is reviewed. Prompt audit updated on
2026-06-11.

The transformation synthetic exports look comparatively strong, but the
paragraph-reordering exports need a judge quality pass because sampled rows can
include list/index/catalog-like fragments where "restore the original paragraph
order" is not a meaningful learnable task. A non-mutating judge audit script was
added:

```bash
python scripts/audit_reordering_datasets.py \
  --base-url http://127.0.0.1:8100/v1 \
  --model posttrain-gemma-teacher \
  --sample-rate 0.01 \
  --concurrency 8 \
  --audit-root logs/expert_reordering_audit/sample_1pct \
  --force
```

The script writes one audit JSONL row per judged example and a summary with
keep/drop counts. It asks the judge to keep only rows with coherent
paragraph-like passages, a meaningful/inferable order, non-catalog content, and
a response that restores the source content. Local row counts:

```text
expert/danish-dynaword-paragraph-reordering: 939,361 rows
expert/common-pile-paragraph-reordering:     277,029 rows
```

Prompt audit, 2026-06-11: the reordering judge prompt was tightened to reject
arbitrary order, alphabetical/name lists, catalog/index/table-of-contents
fragments, bibliography-like rows, metadata boilerplate, OCR corruption,
response omissions/additions, and rows that are not natural discourse ordering
examples. It now requests `primary_failure_type` for diagnostics.
