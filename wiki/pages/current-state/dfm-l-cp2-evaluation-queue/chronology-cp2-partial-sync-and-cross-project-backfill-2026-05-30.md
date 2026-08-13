---
type: Operational Record
title: CP2 partial sync and cross-project backfill (2026-05-30)
description: 'Chronological record from DFM L CP2 Evaluation Queue: CP2 partial sync
  and cross-project backfill (2026-05-30).'
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
# CP2 partial sync and cross-project backfill (2026-05-30)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

CP2 partial sync and cross-project backfill, 2026-05-30. Confidence: high.

While CP2 IFEval-DA was still running, all completed CP2 standard evals and
non-IFEval DFM tasks were merged and synced. The first direct backfill into
`DFM L` wrote local W&B summaries, but the remote `DFM L` run did not expose the
new keys through the API while the active training writer was still online. A
second explicit backfill from the merged JSON files fixed this; W&B API
verification showed representative keys in `DFM L`:

```text
eval/MATH/acc: 0.45380217999999994
dfm_eval/dala/linguistic-acceptability/dfm_evals_macro_f1: 0.3776531672364676
dfm_eval/humaneval/verify/accuracy: 0.14634146341463414
dfm_eval/ifeval-da/instruction_following/final_acc: 0.393870787633715
```

The IFEval-DA value above is the already-completed CP1 value; CP2 IFEval-DA was
not yet complete at the time of this sync. The CP2 backfill log explicitly
reported:

```text
epoch 2 project DFM L dfm ifeval-da skipped: 16/32 eval files available
epoch 2 project Original Plus Mixed Danish Instruction Rich L dfm ifeval-da skipped: 16/32 eval files available
```

CP2 was also backfilled to project
`Original Plus Mixed Danish Instruction Rich L`. W&B API verification showed:

```text
eval/MATH/acc: 0.45380217999999994
dfm_eval/dala/linguistic-acceptability/dfm_evals_macro_f1: 0.3776531672364676
dfm_eval/humaneval/verify/accuracy: 0.14634146341463414
dfm_eval/ifeval-da/instruction_following/final_acc: None
```

Backfill log:

```text
logs/eval/dfm_L_backfill_cp1_cp2_to_projects_20260530T181143.log
```

The second DFM-L visibility repair read merged JSON files and logged CP1/CP2
aggregate rows in one W&B run session. It skipped
`logs/dfm_evals/dfm_L_epoch2_queued_all/merged_ifeval_da_metrics.json` because
that file did not exist yet.
