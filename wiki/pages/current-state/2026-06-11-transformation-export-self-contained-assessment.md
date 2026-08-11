---
type: Operational Record
title: 2026-06-11 Transformation Export Self-Contained Assessment
description: 'Part of Current State: 2026-06-11 Transformation Export Self-Contained
  Assessment.'
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
# 2026-06-11 Transformation Export Self-Contained Assessment

Part of [Current State](/pages/current-state.md).

Confidence: high for local file inspection.

Superseded by the update immediately below: the transformation folders now
include local seed files, generation configs, and accepted-selection summaries.

The four transformation export folders are:

```text
transformations-danish-danish
transformations-danish-english
transformations-english-danish
transformations-english-english
```

Each contains `README.md`, `data/*.jsonl.gz`, and a standalone
`recreate_dataset.py`, but the recreation script is only partially
self-contained in the reproducibility sense:

- It has no repo-code dependency and uses only Python standard-library modules.
- It requires an external seed-text JSONL passed via `--seed-texts`.
- It requires an OpenAI-compatible teacher endpoint via `--base-url` and
  `--model`.
- It currently generates fresh rows from seed texts; it does not reproduce the
  exact accepted-only split/export because the original accepted/regenerated
  audit provenance files are not embedded in each transformation folder.

Therefore the transformation folders are uploadable and self-contained as data
artifacts, but not exact-reproducible without external seed text, teacher model,
and judge/audit provenance. To make them fully reproducible before upload, add
the seed manifest and generation/audit configuration to each folder, or include
the accepted-audit provenance JSONL used to select the rows.
