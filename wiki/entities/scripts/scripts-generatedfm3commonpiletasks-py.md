---
type: Software Reference
title: '`scripts/generate_dfm3_common_pile_tasks.py`'
description: 'Part of Script Entities: `scripts/generate_dfm3_common_pile_tasks.py`.'
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
# `scripts/generate_dfm3_common_pile_tasks.py`

Part of [Script Entities](/entities/scripts.md).

Generates DFM3 self-supervised English raw-text task sources from converted
Common Pile continuation rows.

Responsibilities:

- read converted Common Pile rows from `data/converted_sources/common_pile_*`
- rechunk raw text to smaller task chunks, default `3000` chars
- write `condition/instruction/response` Parquet trees under
  `data/converted_sources_dfm3_common_pile_tasks`
- create one direct-continuation category, one prefix-continuation category,
  one denoising category, and three span-fill variants
- use English instructions for generated tasks

Command:

```bash
cd /work/dfm/HRM-Text
python scripts/generate_dfm3_common_pile_tasks.py \
  --output-root data/converted_sources_dfm3_common_pile_tasks
```

Smoke test, 2026-05-31:

```bash
python scripts/generate_dfm3_common_pile_tasks.py \
  --limit-files 0 \
  --output-root /tmp/dfm3_common_pile_smoke \
  --force
```

returned `{}` and exited successfully.
