---
type: Operational Record
title: Later correction on (2026-06-01)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Later correction
  on (2026-06-01).'
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
# Later correction on (2026-06-01)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Later correction on 2026-06-01. Confidence: high.

The initial verification above was for project `DFM L`. The same CP3 merged
metrics were then explicitly backfilled to project
`Original Plus Mixed Danish Instruction Rich L`, run id `kgnbdmwf`, because
that project initially showed only CP1 and CP2. Backfill log:

```text
logs/eval/dfm_L_epoch3_heavy_first_20260531T2227/backfill_cp3_to_original_plus_mixed_20260601T134813.log
```

W&B API summary verification against
`peter-sk-sdu/Original Plus Mixed Danish Instruction Rich L/kgnbdmwf` found:

```text
eval/MATH/acc/epoch_3 = 0.47639826
eval/GSM8k/acc/epoch_3 = 0.793018726307809
dfm_eval/ifeval-da/instruction_following/final_acc/epoch_3 = 0.4760777566757044
dfm_eval/govreport/rougeL/mean/epoch_3 = 0.019145910006355467
dfm_eval/nordjyllandnews/rougeL/mean/epoch_3 = 0.18987313066472783
dfm_eval/humaneval/verify/accuracy/epoch_3 = 0.2195121951219512
```
