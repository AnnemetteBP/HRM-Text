---
type: Plan Record
title: DFM6-DFM7 Late-Epoch Cooldown Option
description: 'Part of DFM7 Plan: DFM6-DFM7 Late-Epoch Cooldown Option.'
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
# DFM6-DFM7 Late-Epoch Cooldown Option

Part of [DFM7 Plan](/pages/dfm7-plan.md).

Planning note, 2026-07-05. Confidence: high for code-path inspection; medium
for optimization judgement until tried.

- The run is already in epoch 5 after resuming from
  `ephemeral_step_1028500`; the checkpoint state records `epoch: 5`,
  `global_batch_size: 262144`, `gradient_accumulation_steps: 2`, and
  `local_batch_size: 16384`.
- If we want a conservative "cooldown" after the fourth epoch, prefer doubling
  effective batch by changing:
  - `global_batch_size=524288`
  - `gradient_accumulation_steps=4`
  This keeps the per-rank microbatch unchanged:
  `524288 / (8 * 4) = 16384`, so GPU memory should stay close to the current
  run.
- Do not double `global_batch_size` while keeping `gradient_accumulation_steps=2`
  unless we explicitly want to test memory pressure; that would double the
  local microbatch to `32768` tokens per rank and may OOM.
- Resume behavior caveat: `pretrain.py` stores checkpoint metadata including
  `local_batch_size`, `batch_in_epoch`, and row cursors. If local batch size is
  unchanged, resume can continue with batch-based skipping. If local batch size
  changes, the code falls back to row-cursor resume. Keeping local batch fixed
  via gradient accumulation is therefore the safer path.
- Optimization caveat: doubling batch halves the number of optimizer updates
  per remaining token. This is a real cooldown in gradient-noise/update-rate
  terms, but it also changes the update budget. If the goal is only gentler
  finishing, lowering LR is the simpler knob; if the goal is smoother late
  training without increasing memory, larger gradient accumulation is a
  reasonable option.

Follow-up, 2026-07-05. Confidence: high for W&B train/eval metric inspection;
medium for optimization judgement.

- Recent W&B train metrics do not show an obvious instability that requires an
  aggressive cooldown. In 25K-step windows through about 1.03M steps, loss is
  noisy but broadly around `1.01-1.03`, and exact accuracy is broadly around
  `0.28`.
- Suite averages through 1.0M show saturation/noise rather than clear
  overtraining:
  - Standard: `0.7068` at 850K, `0.7078` at 900K, `0.7085` at 950K, `0.7076`
    at 1.0M.
  - DFM-evals: `0.5936` at 850K, `0.6241` at 900K, `0.6163` at 950K,
    `0.6101` at 1.0M.
  - EuroEval: `0.5581` at 850K, `0.5583` at 900K, `0.5574` at 950K,
    `0.5812` at 1.0M.
- Therefore, annealing all the way to an effective `3e-8` is probably too
  aggressive if the goal is continued capability gain. It would mostly freeze
  the model near the end. A more reasonable cooldown would be a modest LR drop
  (`1e-4` to `1.5e-4`) or a cosine tail with a nonzero floor (`lr_min_ratio`
  around `0.05-0.1`), optionally combined with the safer doubled effective
  batch path above.
- Code caveat: `pretrain.py` computes LR from current `train_state.step`,
  `total_steps`, `lr`, and `lr_min_ratio`. Switching from the current flat
  `lr_min_ratio=1` to a tiny floor mid-run applies the cosine schedule
  immediately at the current global step, not only at the final few steps.

Preferred late cooldown variant, 2026-07-05. Confidence: high for local
schedule calculation from `pretrain.py`.

- A practical delayed-cosine cooldown can be implemented without code changes
  by setting:
  - `lr=3e-4`
  - `lr_warmup_steps=1050000`
  - `lr_min_ratio=0.05` or `0.1`
- With DFM7 `total_length=66657336296`, `epochs=5`, and
  `global_batch_size=262144`, `pretrain.py` computes `total_steps=1271385`.
  Therefore the cosine tail starts at 1.05M and lasts about 221K steps.
- Approximate LR values:
  - `lr_min_ratio=0.05`: 1.10M `2.66e-4`, 1.15M `1.79e-4`, 1.20M `8.21e-5`,
    1.25M `2.15e-5`, final `1.5e-5`.
  - `lr_min_ratio=0.1`: 1.10M `2.67e-4`, 1.15M `1.85e-4`, 1.20M `9.35e-5`,
    1.25M `3.62e-5`, final `3.0e-5`.
- This is preferable to annealing toward `3e-8`: it meaningfully cools the last
  fifth of training while still allowing learning. `lr_min_ratio=0.1` is the
  more conservative default; `0.05` is a stronger final cooldown.
