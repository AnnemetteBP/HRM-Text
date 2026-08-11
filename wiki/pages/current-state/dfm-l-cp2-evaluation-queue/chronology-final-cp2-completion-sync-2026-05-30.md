---
type: Operational Record
title: Final CP2 completion/sync (2026-05-30)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Final CP2 completion/sync
  (2026-05-30).'
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
# Final CP2 completion/sync (2026-05-30)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Final CP2 completion/sync, 2026-05-30. Confidence: high.

CP2 IFEval-DA finished all `32/32` shards and the scheduler reached
`FINAL_MERGE_END` at `2026-05-30T20:05:50+02:00`. All CP2 merge/sync logs under
`logs/eval/dfm_L_epoch2_queued_all` and
`logs/dfm_evals/dfm_L_epoch2_queued_all` were scanned and reported `OK`.

Merged CP2 IFEval-DA metrics:

```text
dfm_eval/ifeval-da/instruction_following/final_acc: 0.41158366361133086
dfm_eval/ifeval-da/instruction_following/final_stderr: 0.017495304869788196
dfm_eval/ifeval-da/instruction_following/inst_loose_acc: 0.5045766590389016
dfm_eval/ifeval-da/instruction_following/inst_strict_acc: 0.4874141876430206
dfm_eval/ifeval-da/instruction_following/prompt_loose_acc: 0.3345656192236599
dfm_eval/ifeval-da/instruction_following/prompt_strict_acc: 0.3197781885397412
```

The final merged file is
`logs/dfm_evals/dfm_L_epoch2_queued_all/merged_ifeval_da_metrics.json`.
The scheduler's merge log is
`logs/dfm_evals/dfm_L_epoch2_queued_all/merge_ifeval_da_wandb.log`.

The CP2 IFEval-DA aggregate was backfilled to both W&B projects:
`DFM L` and `Original Plus Mixed Danish Instruction Rich L`, run id
`kgnbdmwf`. The `Original Plus Mixed Danish Instruction Rich L` project exposed
the values through the normal W&B API immediately. For `DFM L`, the active
training writer again hid/overwrote the summary keys, so the run summary was
patched directly through the W&B API. Verification after the direct summary
patch showed:

```text
DFM L :: dfm_eval/ifeval-da/instruction_following/final_acc = 0.41158366361133086
DFM L :: dfm_eval/ifeval-da/instruction_following/inst_strict_acc = 0.4874141876430206
DFM L :: dfm_eval/ifeval-da/instruction_following/prompt_strict_acc = 0.3197781885397412
```
