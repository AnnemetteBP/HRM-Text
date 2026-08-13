---
type: Software Reference
title: '`scripts/prepare_dfm4_paragraph_and_summarization.sh`'
description: 'Part of Script Entities: `scripts/prepare_dfm4_paragraph_and_summarization.sh`.'
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
# `scripts/prepare_dfm4_paragraph_and_summarization.sh`

Part of [Script Entities](/entities/scripts.md).

Stage runner for the DFM4 paragraph-reordering and summarization pipeline.

Responsibilities:

- inventory/download `govreport_summarization`, `wiki_cat_sum`, and
  `laion_scientific_summaries`
- generate DFM4 task sources
- tokenize DFM4 paragraph and summarization roots with one worker by default
- build the DFM4 tokenized union
- sample `data/sampled_dfm4` with `data_io/prefix_config_dfm4.yaml`

Validated on 2026-06-01 with `bash -n`.
