---
type: Software Reference
title: '`scripts/build_tokenized_dfm4_tree.py`'
description: 'Part of Script Entities: `scripts/build_tokenized_dfm4_tree.py`.'
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
# `scripts/build_tokenized_dfm4_tree.py`

Part of [Script Entities](/entities/scripts.md).

Builds the DFM4 tokenized dataset view, `data/tokenized_dfm4`.

Responsibilities:

- symlink all task dirs from `data/tokenized_dfm3`
- symlink DFM4 paragraph-reordering task dirs from
  `data/tokenized_dfm4_paragraph_reorder`
- symlink DFM4 summarization task dirs from
  `data/tokenized_dfm4_summarization`
- write `data/tokenized_dfm4/union_manifest.json`
- traverse source roots with `os.walk(..., followlinks=True)`, because
  `data/tokenized_dfm3` is itself a symlink union. The initial `Path.rglob`
  implementation linked `0` DFM3 tasks from the symlinked root and was
  superseded on 2026-06-01.

Verified 2026-06-01 output:

```json
{
  "output": "data/tokenized_dfm4",
  "roots": [
    {"linked_tasks": 4689, "root": "data/tokenized_dfm3"},
    {"linked_tasks": 25, "root": "data/tokenized_dfm4_paragraph_reorder_dynaword_windows"},
    {"linked_tasks": 425, "root": "data/tokenized_dfm4_paragraph_reorder_common_existing"},
    {"linked_tasks": 4019, "root": "data/tokenized_dfm4_summarization"}
  ],
  "total_tasks": 9158
}
```
