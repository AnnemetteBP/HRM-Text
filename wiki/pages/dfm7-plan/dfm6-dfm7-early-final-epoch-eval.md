---
type: Plan Record
title: DFM6-DFM7 Early Final Epoch Eval
description: 'Part of DFM7 Plan: DFM6-DFM7 Early Final Epoch Eval.'
tags:
- dfm7
- data
- training
- evaluation
status: stable
last_updated: 2026-07-02
confidence: medium
part_of: /pages/dfm7-plan.md
---
# DFM6-DFM7 Early Final Epoch Eval

Part of [DFM7 Plan](/pages/dfm7-plan.md).

Scheduling note, 2026-07-08. Confidence: high from local checkpoint metadata
and scheduler status.

- Because `data/sampled_dfm7` was extended to six epoch index sets after the
  run was already configured for `epochs=5`, the run finished earlier than the
  pending `step_1250000` eval target.
- The last regular completed checkpoint is `epoch_5` in
  `checkpoints/dfm7/XL-gas2-from-dfm6-epoch3`, with checkpoint metadata
  `step: 1229504`, `epoch: 5`, `data_path: data/sampled_dfm7`.
- An eval subgraph for `ckpt_tag=epoch_5` was appended to the existing
  scheduler plan
  `logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253`
  with `eval_epoch=5.0`, W&B run `DFM5/dfm6-dfm7-xl-gas2`, and the same
  HRM-env/vLLM/FA4 settings as the 850K-1200K campaign:
  vLLM utilization `0.25`, Gemma4 native chat template, EuroEval-first order,
  standard batch `64`, DFM batch `32`, DFM IFEval batch `32`, EuroEval batch
  `32`, judged-task vLLM utilization `0.18`.
- HF export target:
  `exports/dfm6_dfm7_XL_gas2_epoch_5_ema_hf_hrmenv_202253`.
- Scheduler status after append showed `wait-01954` completed,
  `export-01955` completed, and the first `epoch_5` EuroEval shards running on
  all eight GPUs.
- The old `step_1250000` wait row remains in the plan. It is obsolete after
  the early finish and can be marked skipped later; it does not block the
  appended `epoch_5` eval subgraph.
