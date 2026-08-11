---
type: Operational Record
title: DFM8 XL Latest Resume Point
description: 'Part of DFM5 XXS Step-50K Full Eval: DFM8 XL Latest Resume Point.'
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
# DFM8 XL Latest Resume Point

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-07-20. Confidence: high from local checkpoint inspection.

After the interrupted DFM8 seventh-epoch run, the newest complete ephemeral
checkpoint under `checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5` is:

```text
ephemeral_step_1569000
```

Validation found `fsdp2_ephemeral_step_1569000/.metadata`, all 8 FSDP
`*.distcp` shard files, all 8 `carry_ephemeral_step_1569000.<rank>.pt` files,
and `checkpoint_state_ephemeral_step_1569000.json`.

The checkpoint sidecar records:

```json
{
  "step": 1569000,
  "epoch": 7,
  "batch_in_epoch": 140428,
  "batch_in_epoch_exact": true,
  "data_path": "data/sampled_dfm8",
  "global_batch_size": 262144,
  "gradient_accumulation_steps": 2
}
```

Resume this run with `epochs=7`, `resume_checkpoint_tag=ephemeral_step_1569000`,
`resume_step=1569000`, and `resume_epoch=7`.

Rechecked later on 2026-07-20. Confidence: high. No newer checkpoint was present:
the latest regular checkpoint was `step_1560000`, and the latest complete
checkpoint overall remained `ephemeral_step_1569000`.
