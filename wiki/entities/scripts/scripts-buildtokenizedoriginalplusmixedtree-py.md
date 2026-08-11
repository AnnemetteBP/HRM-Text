---
type: Software Reference
title: '`scripts/build_tokenized_original_plus_mixed_tree.py`'
description: 'Part of Script Entities: `scripts/build_tokenized_original_plus_mixed_tree.py`.'
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
# `scripts/build_tokenized_original_plus_mixed_tree.py`

Part of [Script Entities](/entities/scripts.md).

Builds the third tokenized dataset view, `data/tokenized_original_plus_mixed`, from existing tokenized outputs.

Responsibilities:

- symlink all task directories from `data/tokenized_original_sapient`
- symlink non-Sapient task directories from `data/tokenized_mixed`
- skip mixed `sapient_cleaned__*` task directories by default so the full original Sapient tokenization and the filtered mixed Sapient subset are not sampled twice
- write `data/tokenized_original_plus_mixed/union_manifest.json`
- refuse paths outside the repo

Verified command:

```bash
cd /work/dfm/HRM-Text
python scripts/build_tokenized_original_plus_mixed_tree.py --force
```

Verified 2026-05-23 output:

```text
Original tasks linked:       5,212
Mixed tasks linked:          226
Mixed Sapient tasks skipped: 1,139
Name collisions skipped:     0
```
