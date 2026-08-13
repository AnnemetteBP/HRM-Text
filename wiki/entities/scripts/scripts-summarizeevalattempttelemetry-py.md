---
type: Software Reference
title: '`scripts/summarize_eval_attempt_telemetry.py`'
description: 'Part of Script Entities: `scripts/summarize_eval_attempt_telemetry.py`.'
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
# `scripts/summarize_eval_attempt_telemetry.py`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-06. Confidence: high.

Summarizes one or more scheduler telemetry TSVs by task, including successes,
OOMs, highest successful batch size, and memory-free statistics:

```bash
cd /work/dfm/HRM-Text
python scripts/summarize_eval_attempt_telemetry.py logs/eval/*/eval_attempts.tsv
```
