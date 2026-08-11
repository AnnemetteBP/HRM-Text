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

Prepares the transformation-refinement post-training dataset.

Responsibilities:

- convert CoEdIT and filtered Super-NI rows;
- build synthetic request JSONL files;
- generate synthetic responses against an OpenAI-compatible teacher endpoint;
- convert accepted generated JSONL responses to Parquet;
- support explicit source-target language pairs for synthetic requests:
  `en:en`, `en:da`, `da:da`, `da:en`;
- use separate default English and Danish source roots;
- use special cross-lingual past-tense prompts for `en:da` and `da:en`;
- reject obvious Danish past-tense language leakage as `language_leak`.

Current source-target convention, 2026-06-05:

```text
task_en_en: English source, English answer
task_en_da: English source, Danish answer
task_da_da: Danish source, Danish answer
task_da_en: Danish source, English answer
```
