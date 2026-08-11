---
type: Software Reference
title: '`scripts/build_filtered_source_tree.py`'
description: 'Part of Script Entities: `scripts/build_filtered_source_tree.py`.'
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
# `scripts/build_filtered_source_tree.py`

Part of [Script Entities](/entities/scripts.md).

Builds `data/filtered_sources` from `data/downloads/datasets`.

Responsibilities:

- apply `config/data/source_filter.yaml`
- create symlinks by default
- apply `allow_overrides` before `deny`
- update incrementally by default; `--force` still removes and rebuilds the output tree
