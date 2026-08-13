---
type: Operational Record
title: 2026-08-07 DFM8 L Epoch 3 Training Restart
description: 'Part of DFM5 XXS Step-50K Full Eval: 2026-08-07 DFM8 L Epoch 3 Training
  Restart.'
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
# 2026-08-07 DFM8 L Epoch 3 Training Restart

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Confidence: high (verified via plan inspection, checkpoint state, and live training output)

## Context- DFM8 L training completed epoch 2 at step 537300 (checkpoint tag `epoch_2`).
- The epoch 2 campaign plan (`logs/scheduler/dfm8_L_campaign_epoch2_20260803`) already had
  epoch 3 jobs pre-created (steps 550K–806K with `epochs=3` in training command) plus
  epoch 4 jobs (steps 850K–1075K).
- `campaign-train-537714` had FAILED because `epochs=2` training stopped at step 537302
  (end of epoch 2) before reaching the target step 537714. The `epoch_2` checkpoint was
  saved successfully regardless.

## Plan Fix Applied1. Marked `campaign-train-537714` status as `done` (epoch_2 checkpoint exists at step 537300).
2. Updated `campaign-train-550000`:
   - `resume_from_tag`: `step_537714` → `epoch_2`
   - `deps`: `campaign-teardown-537714` → `` (empty; that teardown job never existed in the plan)
3. Reset all stale running jobs (13 wait_checkpoint) and the failed training job.

## Runner Launch- **CRITICAL**: Runner must be launched with `PATH="/home/ucloud/miniforge3/envs/hrm/bin:$PATH"`
  prepended so `torchrun` and `ninja` are on PATH.
- First attempt failed with `FileNotFoundError: 'torchrun'` because PATH wasn't set.
- Second launch (PID 122789) succeeded with correct PATH.
- Log: `logs/scheduler/dfm8_L_campaign_epoch2_20260803/runner_epoch3_v2.log`

## Training Status- Resumed from `epoch_2` (step 537300) at 2026-08-07T16:41:18.
- Training command: `epochs=3`, `global_batch_size=262144`, all 8 GPUs.
- Post-warmup speed: ~1.60 it/s (steps/s).
- First segment: step 537300 → 550000 (~13K steps, ~2.2 hours).
- Full epoch 3: step 537300 → 806571 (~269K steps, ~47 hours training time).
- 50K train → eval → 50K train → eval pattern continues through steps 550K, 600K, 650K,
  700K, 750K, 800K, 806K.
