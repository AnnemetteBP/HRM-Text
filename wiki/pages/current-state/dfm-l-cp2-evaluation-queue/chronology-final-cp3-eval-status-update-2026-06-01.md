---
type: Operational Record
title: Final CP3 eval status update (2026-06-01)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Final CP3 eval
  status update (2026-06-01).'
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
# Final CP3 eval status update (2026-06-01)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Final CP3 eval status update, 2026-06-01. Confidence: high.

The resumed CP3 scheduler consumed the full queue: `jobs.tsv` reached `0`
lines, all eval workers/server processes exited, and the last eval job
(`dfm humaneval shard_3_of_4`) ended with status `0` at
`2026-06-01T13:35:39+02:00`. The scheduler then entered `FINAL_MERGE_START`
and reached `FINAL_MERGE_END` at `2026-06-01T13:35:56+02:00`.

However, every final merge-and-W&B-sync command logged `FAILED` because W&B was
not authenticated in the detached scheduler environment:

```text
wandb.errors.errors.UsageError: No API key configured. Use `wandb login` to log in.
```

The eval artifacts are present locally, including HumanEval shard inspect and
EEE outputs. The next operational step is to rerun merge/sync with a valid W&B
login or `WANDB_API_KEY` in the environment; the eval computations themselves
do not need to be rerun for this failure.
