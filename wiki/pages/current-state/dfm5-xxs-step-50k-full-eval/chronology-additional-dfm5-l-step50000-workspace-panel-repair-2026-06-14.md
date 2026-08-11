---
type: Operational Record
title: Additional DFM5 L step50000 workspace-panel repair (2026-06-14)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Additional DFM5
  L step50000 workspace-panel repair (2026-06-14).'
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
# Additional DFM5 L step50000 workspace-panel repair (2026-06-14)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Additional DFM5 L `step_50000` workspace-panel repair, 2026-06-14.
Confidence: high for local merged artifacts and W&B client sync output. The
workspace manifest already contained panels for `eval/MMLU/acc`,
`eval/BoolQ/acc`, and `dfm_eval/nordjyllandnews/rouge2/mean`, but sparse W&B
history rows can fail to render when the metric and epoch x-axis are not
co-located in the same logged row. Compact rows were therefore re-logged to
run `DFM5/oti1lisg`:

```text
eval/epoch=0.27608846182186414
eval/MMLU/acc=0.29475

eval/epoch=0.27608846182186414
eval/BoolQ/acc=0.5817

dfm_eval/epoch=0.27608846182186414
dfm_eval/nordjyllandnews/rouge2/mean=0.09118908082193376
```

The corresponding local W&B summaries are in:

```text
wandb/run-20260614_170906-oti1lisg/files/wandb-summary.json
wandb/run-20260614_171041-oti1lisg/files/wandb-summary.json
```
