---
type: Operational Record
title: DFM4 XL-DDP 300K no-EMA lite W&B x-axis repair (2026-06-04)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM4 XL-DDP 300K
  no-EMA lite W&B x-axis repair (2026-06-04).'
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
# DFM4 XL-DDP 300K no-EMA lite W&B x-axis repair (2026-06-04)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM4 XL-DDP 300K no-EMA lite W&B x-axis repair, 2026-06-04. Confidence: high.

The `step_300000` no-EMA lite eval for W&B run `4chqwd3w` in project
`Original Plus Mixed Danish Instruction Rich L` was initially logged with
`lite_eval_noema/epoch=300000` and `lite_dfm_eval_noema/epoch=300000`, which
made the Lite section plots autoscale to an unusable x-axis. W&B rewind was
tested through GraphQL but is not enabled for this account, and history rows are
append-only through the available API, so the bad original rows remain in the
run history.

The non-destructive repair is a clean parallel metric namespace:
`lite_eval_noema_epochfix/*` and `lite_dfm_eval_noema_epochfix/*`. Script
`scripts/backfill_dfm4_lite_noema_epochfix_wandb.py` reads the completed local
merged JSONs for DFM4 XL-DDP no-EMA lite checkpoints `step_50000`,
`step_100000`, `step_150000`, `step_200000`, `step_250000`, and `step_300000`,
rewrites the prefixes, and computes fractional epochs as
`step * 196608 / 72007089569`. Verified logged epoch values are:

- `step_50000`: `0.1365198907335385`
- `step_100000`: `0.273039781467077`
- `step_150000`: `0.4095596722006155`
- `step_200000`: `0.546079562934154`
- `step_250000`: `0.6825994536676925`
- `step_300000`: `0.819119344401231`

W&B API readback showed `lite_eval_noema_epochfix/epoch` at history steps
`300049..300054` and `lite_dfm_eval_noema_epochfix/epoch` at history steps
`300055..300060`, with the correct six fractional epoch values above. The
default workspace view `nw-nwuserpetersk-w` (`Peter-sk's workspace`) was updated
so its two auto Lite sections are named `lite_eval_noema_epochfix` and
`lite_dfm_eval_noema_epochfix`. Backup specs were written to
`logs/wandb_workspace_specs/20260604T201124Z_before_lite_epochfix_nw-nwuserpetersk-w.json`
and
`logs/wandb_workspace_specs/20260604T201124Z_after_lite_epochfix_nw-nwuserpetersk-w.json`.

Follow-up repair in the same turn. Confidence: high. The W&B UI still surfaced
the old `300000` x-axis through auto-generated Lite plots. The same default
workspace view was therefore changed from auto Lite sections to explicit
non-auto Lite sections: `Lite standard no-EMA epochfixed` with `9` standard
panels and `Lite DFM no-EMA epochfixed` with `14` DFM panels. Each panel uses
only `lite_eval_noema_epochfix/*` or `lite_dfm_eval_noema_epochfix/*` metrics,
with x-axis `lite_eval_noema_epochfix/epoch` or
`lite_dfm_eval_noema_epochfix/epoch`. API readback showed zero occurrences of
`lite_eval_noema/` and `lite_dfm_eval_noema/` in the live view spec. Backup
specs were written to
`logs/wandb_workspace_specs/20260604T201558Z_before_lite_explicit_epochfix_nw-nwuserpetersk-w.json`
and
`logs/wandb_workspace_specs/20260604T201558Z_after_lite_explicit_epochfix_nw-nwuserpetersk-w.json`.
