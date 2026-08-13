---
type: Software Reference
title: '`scripts/generate_dfm2_dynaword_tasks.py`'
description: 'Part of Script Entities: `scripts/generate_dfm2_dynaword_tasks.py`.'
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
# `scripts/generate_dfm2_dynaword_tasks.py`

Part of [Script Entities](/entities/scripts.md).

Generates DFM2 self-supervised DynaWord task sources.

Responsibilities:

- read converted DynaWord continuation rows from `data/converted_sources/danish_dynaword`
- rechunk raw text to smaller task chunks, default `3000` chars
- write separate `condition/instruction/response` Parquet trees under `data/converted_sources_dfm2_dynaword_tasks`
- create two prefix-continuation variants, two denoising variants, and six span-fill variants
- cap rows per source file to the DFM2 sampling budget: `60k` for each prefix-continuation variant, `30k` for each denoising variant, and `30k` for each span-fill variant
- avoid sampler-level `repeat: 2` for generated task families; unique generated variants are used instead of duplicated sampled rows

Command:

```bash
cd /work/dfm/HRM-Text
python scripts/generate_dfm2_dynaword_tasks.py \
  --output-root data/converted_sources_dfm2_dynaword_tasks \
  --force
```

Verified 2026-05-30 full generation output: `450` Parquet files and `13G`.
