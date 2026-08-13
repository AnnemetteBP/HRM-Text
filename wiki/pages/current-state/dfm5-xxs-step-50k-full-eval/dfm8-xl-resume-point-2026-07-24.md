---
type: Operational Record
title: DFM8 XL Resume Point, 2026-07-24
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM8 XL Resume Point, 2026-07-24.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# DFM8 XL Resume Point, 2026-07-24

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Confidence: high from local checkpoint sidecar and shard inspection.

The DFM8 XL epoch-7 process stopped on 2026-07-24 after rank 1 received
`SIGKILL` and the remaining ranks were terminated. The newest fully written
checkpoint is:

```text
checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5/fsdp2_ephemeral_step_1766500
```

It has its DCP `.metadata`, all 8 `*.distcp` shards, all 8
`carry_ephemeral_step_1766500.<rank>.pt` files, and
`checkpoint_state_ephemeral_step_1766500.json`. The sidecar records
`step=1766500`, `epoch=7`, `batch_in_epoch=535428`, and
`batch_in_epoch_exact=true`.

This supersedes the earlier recorded `ephemeral_step_1569000` resume point.
Resume with the original DFM8 XL settings and:

```text
resume_checkpoint_tag=ephemeral_step_1766500
resume_step=1766500
resume_epoch=7
```
