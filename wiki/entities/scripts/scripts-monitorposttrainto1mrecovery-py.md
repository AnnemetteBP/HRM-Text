---
type: Software Reference
title: '`scripts/monitor_posttrain_to_1m_recovery.py`'
description: 'Part of Script Entities: `scripts/monitor_posttrain_to_1m_recovery.py`.'
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
# `scripts/monitor_posttrain_to_1m_recovery.py`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-09. Confidence: high for local tmux output.

Live monitor for the posttrain transform/refine 1M recovery audit. It prints
one line per GPU with audited rows, current file progress, aggregate rate, audit
ETA, and GPU memory/utilization.

Active tmux window:

```bash
tmux attach -t hrm-1
# switch to window 7: posttrain-monitor
```
