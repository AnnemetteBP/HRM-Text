---
type: Operational Record
title: Clean-run clone (2026-06-04)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Clean-run clone
  (2026-06-04).'
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
# Clean-run clone (2026-06-04)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Clean-run clone, 2026-06-04. Confidence: high. Because the user works in the
saved W&B `manual workspace` view (`nw=boh5wwabbfc7`) and the old append-only
history could still affect plots, a new clean W&B run was created instead of
continuing to mutate workspace panels. Script
`scripts/clone_wandb_run_without_bad_lite_300k.py` parses local
`wandb/run-*-4chqwd3w/run-4chqwd3w.wandb` datastores, skips one interrupted
datastore with invalid padding, deduplicates and coalesces history rows by
`_step`, omits rows where `lite_eval_noema/epoch` or
`lite_dfm_eval_noema/epoch` equals `300000`, and replays the rest into run
`dfm4xlddpclean` in project `Original Plus Mixed Danish Instruction Rich L`.

Dry-run and live replay both reported `38` omitted bad rows, `60,333`
deduplicated rows before coalescing, and `60,331` replayed coalesced rows. W&B
API verification of the new run showed:

- `lite_eval_noema/epoch` unique values:
  `0.1365202623373361`, `0.2730405246746722`, `0.4095607870120083`,
  `0.546081049349`, `0.6826013116866806`
- `lite_dfm_eval_noema/epoch` unique values: same five values above
- `lite_eval_noema_epochfix/epoch` unique values:
  `0.1365198907335385`, `0.273039781467077`, `0.4095596722006155`,
  `0.546079562934154`, `0.6825994536676925`, `0.819119344401231`
- `lite_dfm_eval_noema_epochfix/epoch` unique values: same six corrected
  epoch-fixed values above

The clean run URL is:
`https://wandb.ai/peter-sk-sdu/Original%20Plus%20Mixed%20Danish%20Instruction%20Rich%20L/runs/dfm4xlddpclean`.
The replay log is
`logs/wandb_clone_dfm4_xl_ddp_clean_lite_history_20260604.log`.

Follow-up 300K replacement in the clean run. Confidence: high. After creating
the clean run, the ordinary no-EMA lite prefixes intentionally stopped at 250K
because the original 300K ordinary-prefix rows were omitted. The completed 300K
eval shards were then re-merged and logged to `dfm4xlddpclean` under the
ordinary prefixes `lite_eval_noema/*` and `lite_dfm_eval_noema/*`, using
`EVAL_EPOCH=0.819119344401231`. Command log:
`logs/wandb_backfill_dfm4_clean_300k_usual_prefixes_20260604.log`.

W&B API readback after this backfill showed:

- `lite_eval_noema/epoch` unique values now include `0.819119344401231`, with
  the latest 300K rows at history steps `300061..300068`.
- `lite_dfm_eval_noema/epoch` unique values now include `0.819119344401231`,
  with latest 300K rows at history steps `300072..300079`.
- Example 300K ordinary-prefix values are
  `lite_eval_noema/MMLU/acc=0.3557` at history step `300063` and
  `lite_dfm_eval_noema/piqa/piqa_scorer/accuracy=0.1388888888888889` at
  history step `300075`.
