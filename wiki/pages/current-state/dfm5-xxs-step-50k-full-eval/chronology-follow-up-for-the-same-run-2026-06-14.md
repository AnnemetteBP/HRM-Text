---
type: Operational Record
title: Follow-up for the same run (2026-06-14)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Follow-up for
  the same run (2026-06-14).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# Follow-up for the same run (2026-06-14)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Follow-up for the same run, 2026-06-14. Confidence: high for W&B history
readback and workspace API output. As with earlier DFM5 average logging, the
remote W&B `run.summary` API did not immediately expose the `headline_avg/*`
keys even though the client sync and local `wandb-summary.json` contained them.
A remote `scan_history` check found the actual history row:

```text
_step                    75711
headline_avg/epoch       0.27608846182186414
headline_avg/train_step  50000
headline_avg/danish      0.28379788656320293
headline_avg/english     0.33401347487407673
headline_avg/math_code   0.06487754537306532
headline_avg/overall     0.22756296893678166
```

The DFM5 workspace was refreshed so the panels plot against explicit history
x-axes (`eval/epoch`, `dfm_eval/epoch`, `euroeval/epoch`,
`headline_avg/epoch`) rather than W&B `_step` or summary values:

```bash
cd /work/dfm/HRM-Text
python scripts/create_dfm5_headline_workspace.py \
  --project DFM5 \
  --name "DFM5 headline metrics"
```

The refreshed workspace URL is:

```text
https://wandb.ai/peter-sk-sdu/DFM5?nw=ein5y6vzl3l
```
