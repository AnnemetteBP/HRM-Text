---
type: Software Reference
title: '`scripts/generate_dfm5_l_eval_comparison_report.py`'
description: 'Part of Script Entities: `scripts/generate_dfm5_l_eval_comparison_report.py`.'
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
# `scripts/generate_dfm5_l_eval_comparison_report.py`

Part of [Script Entities](/entities/scripts.md).

Update, 2026-06-16. Confidence: high for local execution. Regenerates
`docs/dfm5.md` from local merged evaluation artifacts. It now writes only
`docs/dfm5.md`; the older duplicate outputs under `logs/reports/` were removed.

Checkpoint inclusion is controlled by the hard-coded `DFM5_CHECKPOINTS` list
near the top of the script. Each entry names the display label, checkpoint tag,
standard-eval root, dfm-evals root, and EuroEval root. To include a newly
completed checkpoint in `docs/dfm5.md`, add its roots to `DFM5_CHECKPOINTS` and
run:

```bash
cd /work/dfm/HRM-Text
python scripts/generate_dfm5_l_eval_comparison_report.py
```
