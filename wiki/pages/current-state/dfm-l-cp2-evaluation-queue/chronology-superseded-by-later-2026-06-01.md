---
type: Operational Record
title: Superseded by later (2026-06-01)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Superseded by
  later (2026-06-01).'
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
# Superseded by later (2026-06-01)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Superseded by later 2026-06-01 update: W&B was authenticated and all CP3
merge/sync commands were rerun successfully. Confidence: high.

After `wandb login`, the standard eval, IFEval-DA, and DFM eval merge/sync
commands were rerun manually against:

- `logs/eval/dfm_L_epoch3_heavy_first_20260531T2227`
- `logs/dfm_evals/dfm_L_epoch3_heavy_first_20260531T2227`

The rerun wrote `*.rerun.log` merge logs and printed successful sync completion
for all standard eval tasks, IFEval-DA, and DFM tasks through HumanEval.
W&B API summary verification for project `DFM L`, run id `kgnbdmwf`, found
representative CP3 metrics including:

```text
eval/MATH/acc/epoch_3 = 0.47639826
eval/GSM8k/acc/epoch_3 = 0.793018726307809
dfm_eval/ifeval-da/instruction_following/final_acc/epoch_3 = 0.4760777566757044
dfm_eval/govreport/rougeL/mean/epoch_3 = 0.019145910006355467
dfm_eval/nordjyllandnews/rougeL/mean/epoch_3 = 0.18987313066472783
dfm_eval/humaneval/verify/accuracy/epoch_3 = 0.2195121951219512
```
