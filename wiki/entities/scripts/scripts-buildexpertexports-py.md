---
type: Software Reference
title: '`scripts/build_expert_exports.py`'
description: 'Part of Script Entities: `scripts/build_expert_exports.py`.'
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
# `scripts/build_expert_exports.py`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-10; export-root note updated on 2026-06-11. Confidence: high.

Builds the self-contained `export/` dataset export package. It creates one
upload-ready subfolder per non-superseded expert/post-training dataset family,
writes a `README.md` dataset card and standalone `recreate_dataset.py` into
each subfolder, and writes chat-template-ready compressed JSONL shards under
`data/*.jsonl.gz`. It does not create symlinks. The 2026-06-10 rebuild uses
file-level parallel Parquet conversion controlled by `EXPERT_EXPORT_WORKERS`
with default `16`.

Synthetic rows are filtered to accepted examples only. Base generated rows
whose `id` appears as a regenerated `original_id` are excluded, and accepted
regeneration rows are included as replacements. Synthetic transformation data
is exported as four source/target language-pair datasets:
`transformations-danish-danish`, `transformations-danish-english`,
`transformations-english-danish`, and `transformations-english-english`.

Validated output after the root rename:

```text
export/ contains 12 dataset folders
find export -type l | wc -l -> 0
find export -type f -name '*.jsonl.gz' | wc -l -> 4187
no export/*.parquet or plain export/*.jsonl files remain
all export/*/recreate_dataset.py files compile with py_compile
```
