---
type: Software Reference
title: '`scripts/filter_all_export_audits.py`'
description: 'Part of Script Entities: `scripts/filter_all_export_audits.py`.'
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
# `scripts/filter_all_export_audits.py`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-11. Confidence: high for syntax.

Filters the eight export datasets using every `audit*/audit.jsonl` file inside
each dataset folder. This replaces the earlier `export_audit_filter_watch`
tmux watcher, which only knew about `audit_full` and would miss rebalance shard
audit roots.

Run after the desired audit target is reached:

```bash
python scripts/filter_all_export_audits.py
```
