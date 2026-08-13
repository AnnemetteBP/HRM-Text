---
type: Software Reference
title: '`scripts/build_tokenized_dfm2_tree.py`'
description: 'Part of Script Entities: `scripts/build_tokenized_dfm2_tree.py`.'
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
# `scripts/build_tokenized_dfm2_tree.py`

Part of [Script Entities](/entities/scripts.md).

Builds the DFM2 tokenized dataset view, `data/tokenized_dfm2`.

Responsibilities:

- symlink all task directories from `data/tokenized_mixed`
- symlink generated DFM2 task directories from `data/tokenized_dfm2_dynaword_tasks`
- write `data/tokenized_dfm2/union_manifest.json`

Command:

```bash
cd /work/dfm/HRM-Text
python scripts/build_tokenized_dfm2_tree.py --force
```
