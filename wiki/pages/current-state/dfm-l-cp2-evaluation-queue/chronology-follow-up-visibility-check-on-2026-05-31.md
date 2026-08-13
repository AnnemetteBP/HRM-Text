---
type: Operational Record
title: Follow-up visibility check on (2026-05-31)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Follow-up visibility
  check on (2026-05-31).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm-l-cp2-evaluation-queue.md
---
# Follow-up visibility check on (2026-05-31)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Follow-up visibility check on 2026-05-31. Confidence: high.

The CP2 heavy-first metrics are present in W&B history, not only in summary.
API checks with one metric family at a time returned history rows for run
`kgnbdmwf` in project `Original Plus Mixed Danish Instruction Rich L`,
including:

```text
eval/MATH/acc at _step 900103 with eval/epoch = 2
dfm_eval/ifeval-da/instruction_following/final_acc at _step 900104 with dfm_eval/epoch = 2
```

If the W&B UI does not show them, likely causes are workspace/run filters that
exclude the `dfm-L` run, stale panel state, or plots using `_step` as x-axis.
For standard eval panels use `eval/epoch` as x-axis; for DFM eval panels use
`dfm_eval/epoch`.
