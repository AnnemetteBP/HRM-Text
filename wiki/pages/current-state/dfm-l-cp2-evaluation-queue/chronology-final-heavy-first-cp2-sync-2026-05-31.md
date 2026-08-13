---
type: Operational Record
title: Final heavy-first CP2 sync (2026-05-31)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Final heavy-first
  CP2 sync (2026-05-31).'
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
# Final heavy-first CP2 sync (2026-05-31)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Final heavy-first CP2 sync, 2026-05-31. Confidence: high.

The heavy-first CP2 scheduler completed all `168/168` jobs and reached
`FINAL_MERGE_END` at `2026-05-31T15:52:04+02:00`. The built-in final merge
synced the aggregates to project `DFM L`, run id `kgnbdmwf`.

The same merged aggregates were then backfilled to project
`Original Plus Mixed Danish Instruction Rich L`, run id `kgnbdmwf`, run name
`dfm-L`. The successful backfill log is:

```text
logs/eval/dfm_L_epoch2_heavy_first_backfill_to_original_plus_mixed_20260531T174752.log
```

It logged `195` standard `eval/*` metrics from `8` merged standard files and
`74` `dfm_eval/*` metrics from `11` merged DFM files. W&B API verification
against
`https://wandb.ai/peter-sk-sdu/Original%20Plus%20Mixed%20Danish%20Instruction%20Rich%20L/runs/kgnbdmwf`
returned representative values:

```text
eval/MATH/acc = 0.45380217999999994
eval/GSM8k/acc = 0.7665051554207735
eval/MMLU/acc = 0.33975000000000005
dfm_eval/ifeval-da/instruction_following/final_acc = 0.41204577082020327
dfm_eval/generative-talemaader/model_graded_fact/accuracy = 0.13923267326732677
dfm_eval/humaneval/verify/accuracy = 0.14634146341463414
dfm_eval/nordjyllandnews/rougeL/mean = 0.20810562203119595
```
