---
type: Software Reference
title: '`scripts/build_tokenized_dfm3_tree.py`'
description: 'Part of Script Entities: `scripts/build_tokenized_dfm3_tree.py`.'
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
# `scripts/build_tokenized_dfm3_tree.py`

Part of [Script Entities](/entities/scripts.md).

Builds the DFM3 tokenized dataset view, `data/tokenized_dfm3`.

Responsibilities:

- symlink task dirs from `data/tokenized_mixed`
- symlink DFM2 generated DynaWord task dirs from
  `data/tokenized_dfm2_dynaword_tasks`
- symlink DFM3 generated Common Pile task dirs from
  `data/tokenized_dfm3_common_pile_tasks`
- write `data/tokenized_dfm3/union_manifest.json`

Command:

```bash
cd /work/dfm/HRM-Text
python scripts/build_tokenized_dfm3_tree.py --force
```
