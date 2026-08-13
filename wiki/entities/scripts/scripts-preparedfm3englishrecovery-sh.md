---
type: Software Reference
title: '`scripts/prepare_dfm3_english_recovery.sh`'
description: 'Part of Script Entities: `scripts/prepare_dfm3_english_recovery.sh`.'
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
# `scripts/prepare_dfm3_english_recovery.sh`

Part of [Script Entities](/entities/scripts.md).

Stage runner for the DFM3 English-recovery data pipeline.

Responsibilities:

- inventory/download selected Common Pile datasets
- run filtering and incremental conversion
- generate Common Pile self-supervised tasks
- tokenize generated DFM3 tasks with one worker
- build the DFM3 tokenized union
- sample `data/sampled_dfm3`

Validated on 2026-05-31 with `bash -n`.
