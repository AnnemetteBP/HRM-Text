---
type: Operational Record
title: 2026-06-04 DFM4 XL-DDP Step 300K No-EMA Lite Eval
description: 'Part of Current State: 2026-06-04 DFM4 XL-DDP Step 300K No-EMA Lite
  Eval.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# 2026-06-04 DFM4 XL-DDP Step 300K No-EMA Lite Eval

Part of [Current State](/pages/current-state.md).

Confidence: high.

The `checkpoints/dfm4/XL-ddp` `step_300000` checkpoint was present as an
unsharded DDP checkpoint with checkpoint state and carry files:

```text
unsharded_step_300000.pt
checkpoint_state_step_300000.json
carry_step_300000.{0..7}.pt
```

A true no-EMA lite eval was launched on all 8 GPUs and synced directly to the
usual Lite-section W&B run/prefixes:

- W&B project: `Original Plus Mixed Danish Instruction Rich L`
- W&B run id: `4chqwd3w`
- W&B run name: `dfm4-XL-ddp`
- Metric prefixes: `lite_eval_noema/*` and `lite_dfm_eval_noema/*`
- Scheduler tmux window: `hrm:7` (`dfm4-300k-noema`)
- Monitor tmux window: `hrm:8` (`dfm4-300k-mon`)
- Logs: `logs/eval/dfm4_XL_ddp_noema_lite_probe_20260604_300k`
- DFM logs: `logs/dfm_evals/dfm4_XL_ddp_noema_lite_probe_20260604_300k`

The launch used default eval batch sizes from `scripts/schedule_checkpoint_evals.sh`:
`STANDARD_BATCH_SIZE=8`, `DFM_BATCH_SIZE=8`, and `IFEVAL_BATCH_SIZE=16`.
The run completed with `FINAL_MERGE_END step_300000 status_0` and
`DONE status_0`. HumanEval traceback strings in `inspect/logs.json` are normal
wrong-answer scoring explanations, not infrastructure failures.
