---
type: Software Reference
title: '`scripts/convert_filtered_sources.py`'
description: 'Part of Script Entities: `scripts/convert_filtered_sources.py`.'
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
# `scripts/convert_filtered_sources.py`

Part of [Script Entities](/entities/scripts.md).

Converts filtered source files to HRM tokenizer schema.

Responsibilities:

- write `data/converted_sources`
- normalize mixed schemas to `condition/instruction/response`
- expand chat `messages` into one row per assistant turn
- convert DynaWord `text` to empty-instruction continuation chunks
- convert `prompt`/`target` backtranslation datasets to direct instruction rows
- convert Danish extractive QA `context`/`question`/`answers` rows to direct instruction rows
- convert Danish translation datasets bidirectionally from `danish` plus `english`, `ukrainian`, or `arabic`
- convert selected local DBC `.jsonl.gz` files:
  - `dbc-abstracts_*` to bibliographic abstract-writing rows
  - `dbc-reviews` to bibliographic review-writing rows
  - `dbc-faktalink` and `dbc-farfatterweb` to section-title/body article rows
- convert local LexDK articles to Danish encyclopedia-writing rows
- convert local OPUS Danish/English direct paired JSONL (`opus_da_en.jsonl.gz` with `da` and `en` fields) to bidirectional translation rows; older split-side `opus-da_*`/`opus-en_*` handling remains as a fallback
- parallelize by source file with `--workers`
- update incrementally by default; existing outputs are skipped when they are current, and new conversions write a `.convert_meta.json` sidecar
- legacy outputs created before `.convert_meta.json` existed are treated as current when the output mtime is newer than or equal to the source mtime

Recommended command:

```bash
python scripts/convert_filtered_sources.py --copy-ready --workers 32
```

Use `--force` only for an intentional full rebuild.
