---
type: Plan Record
title: DFM8 L Second-Epoch Campaign
description: 'Part of DFM8 Plan: DFM8 L Second-Epoch Campaign.'
tags:
- dfm8
- data
- synthetic-data
- training
- evaluation
status: stable
last_updated: 2026-07-12
confidence: medium
part_of: /pages/dfm8-plan.md
---
# DFM8 L Second-Epoch Campaign

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Update, 2026-08-03. Confidence: high from the completed `epoch_1` checkpoint,
its sidecar, the prior campaign log, and the live second-epoch scheduler.

The earlier predicted first-epoch endpoint of step 268857 is superseded. The
data loader actually exhausted `epoch_0` after step 268650 and wrote the
complete regular checkpoint `fsdp2_epoch_1` at global step **268651**. Its
sidecar records `epoch=1`, exact `batch_in_epoch=0`, global batch 262144, and
all eight carry shards are present. The old campaign's sole failed row,
`campaign-train-268857`, was therefore a checkpoint-name verification failure
after successful completion, not a training failure.

The second epoch is managed by:

```text
logs/scheduler/dfm8_L_campaign_epoch2_20260803
```

It resumes `checkpoints/dfm8/L-gbs131072/fsdp2_epoch_1`, keeps the existing
W&B run `DFM5/g2oaotmc`, and evaluates complete EMA checkpoints at 300K, 350K,
400K, 450K, and 500K. The final scheduler target is the conservative
metadata-derived upper estimate 537714. This does not assert that epoch 2 has
exactly that many steps: the training loop naturally stops and writes
`fsdp2_epoch_2` when sampled `epoch_1` is exhausted. The actual second-epoch
boundary must be taken from that checkpoint sidecar after completion.
Evaluation epochs currently use `global_step / 268651`, anchored to the
observed first-epoch boundary. The full evaluation
configuration remains the one documented above: standard, DFM, 32-shard
IFEval-DA, and EuroEval; EuroEval-first ordering; persistent vLLM; Gemma 4
native chat template; and the established separate judge configuration.

The reproducible plan builder is
`scripts/setup_dfm8_l_epoch2_campaign.sh`. Live tmux windows are
`hrm-0:4` (`training`), `hrm-0:5` (`scheduler`), and `hrm-0:6` (`monitor`).
The training-log follower now searches both the first- and second-epoch log
roots.

Epoch-2→Epoch-3 chain correction, 2026-08-04. Confidence: high from
`plan.tsv` metadata inspection. The continuation row was fixed to begin at the
actual end-of-epoch-2 checkpoint (`step_537714`) instead of restarting from
`step_500000`:

- `campaign-train-537714` ends epoch 2 from `step_500000` to `step_537714`.
- `campaign-train-550000` now depends on `campaign-teardown-537714` and resumes
  from `step_537714` (then stops at 550000).

This keeps the existing 50K cadence schedule for epoch 3 (`600000`, `650000`,
`700000`, `750000`, `800000`, `806365`) and avoids overlapping a stale
`resume_from_tag` at the epoch boundary.
