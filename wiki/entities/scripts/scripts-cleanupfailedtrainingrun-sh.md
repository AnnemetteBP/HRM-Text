---
type: Software Reference
title: '`scripts/cleanup_failed_training_run.sh`'
description: 'Part of Script Entities: `scripts/cleanup_failed_training_run.sh`.'
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
# `scripts/cleanup_failed_training_run.sh`

Part of [Script Entities](/entities/scripts.md).

Dry-run-by-default helper for removing local artifacts from failed training runs.

Responsibilities:

- remove a selected local W&B run directory
- remove W&B convenience symlinks only when they point at the selected run
- remove a selected checkpoint directory
- refuse paths outside `REPO_ROOT`
- refuse `data/` and `data_io/` paths

Current known failed original-L target:

```bash
scripts/cleanup_failed_training_run.sh --original-l-latest
scripts/cleanup_failed_training_run.sh --original-l-latest --execute
```
