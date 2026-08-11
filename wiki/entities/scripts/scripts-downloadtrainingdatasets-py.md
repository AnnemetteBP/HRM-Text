---
type: Software Reference
title: '`scripts/download_training_datasets.py`'
description: 'Part of Script Entities: `scripts/download_training_datasets.py`.'
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
# `scripts/download_training_datasets.py`

Part of [Script Entities](/entities/scripts.md).

Manifest-driven Hugging Face downloader.

Responsibilities:

- download selected groups into `data/downloads/datasets`
- use `HF_TOKEN` from environment for gated datasets
- default dry-run inventory unless `--download` is passed
- groups include `danish`, `synquid`, `nemotron`, `dolci`, `allenai`, `sapient`, `raw`

Current policy:

- Common Pile removed.
- AllenAI WildChat removed.
- `raw` selects only DynaWord.
- Oliver Kinch Danish instruction/backtranslation, QA, summarization, and translation datasets were added on 2026-05-21.
