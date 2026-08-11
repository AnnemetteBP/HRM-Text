---
type: Operational Record
title: DFM5 L step150000 full eval launch (2026-06-15)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5 L step150000
  full eval launch (2026-06-15).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# DFM5 L step150000 full eval launch (2026-06-15)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5 L `step_150000` full eval launch, 2026-06-15. Confidence: high for local
checkpoint state and scheduler status logs. The `checkpoints/dfm5/L`
`step_150000` checkpoint exists as an FSDP2 sharded regular checkpoint with
`batch_in_epoch=150000`, `global_batch_size=196608`, and data path
`data/sampled_dfm5`. Its eval epoch x-value is `0.8282653854655924`.

The full eval was launched with EuroEval-first ordering and the EuroEval
FlashAttention guard:

```text
tmux session/window: hrm-0:7 eval150k-scheduler
monitor window:      hrm-0:8 eval150k-monitor
checkpoint:          checkpoints/dfm5/L step_150000
W&B target:          DFM5 / oti1lisg / dfm5-L
log root:            logs/eval/dfm5_L_step150000_full_20260615_eurofirst_guard
dfm root:            logs/dfm_evals/dfm5_L_step150000_full_20260615_eurofirst_guard
euro root:           logs/euroeval/dfm5_L_step150000_full_20260615_eurofirst_guard
```

Initial scheduler status:

```text
2026-06-15T05:23:39+02:00 QUEUED 188 jobs
2026-06-15T05:23:39+02:00 CHECKPOINT_READY step_150000 path_checkpoints/dfm5/L
2026-06-15T05:23:39+02:00 START euroeval angry-tweets shard_0_of_20 gpu_0 attempt_1_of_6 batch_16
```

At the first health check, EuroEval tasks had started first on GPUs 0-5 and
`eval_attempts.tsv` still contained only the header, so no failures had been
recorded.
