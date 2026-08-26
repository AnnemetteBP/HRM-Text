---
type: Incident
title: DFM8 XXL Step 150.7K Loss Excursion
description: Evidence and operational interpretation of the self-recovering DFM8 XXL loss spike near step 150700.
tags: [training, dfm8, xxl, stability, optimizer]
status: stable
last_updated: 2026-08-26
confidence: high
---
# DFM8 XXL Step 150.7K Loss Excursion

The `DFM5/40j5y877` run (`dfm8-XXL-1epoch`) experienced one severe but
self-recovering loss excursion between steps 150655 and 150875. Loss rose from
approximately `1.1` to a maximum of `7.2855` at step 150685, exact accuracy
fell to zero, and both recovered without changing the learning rate or BP-step
schedule. Loss was back near its earlier range by step 150875 and remained
healthy after the step-151000 resume.

This was not a W&B visualization artifact. It was also not a checkpoint-resume
boundary: the run resumed at step 150000 and the excursion began approximately
655 optimizer steps later. Throughout the event, `train/lr=4e-4` and
`bp_steps=5`.

## Data Attribution

[`scripts/analyze_sampled_step_sources.py`](/scripts/analyze_sampled_step_sources.py)
reproduces Multipack allocation from a checkpoint's saved global row cursor and
maps sampled token offsets back to DFM8 source tasks. The retained report is
`logs/training/dfm8_XXL_1epoch/step_150500_spike_sources.json`.

The baseline, onset, peak/recovery, and recovered windows have effectively the
same sequence-length and source-family distributions:

| Window | Median length | P95 | P99 | DMMath row share |
|---|---:|---:|---:|---:|
| 150500-150650 | 143 | 1121 | 2823 | 23.04% |
| 150651-150685 | 146 | 1148 | 2863 | 22.94% |
| 150686-150760 | 143 | 1095 | 2807 | 23.07% |
| 150900-151000 | 140 | 1112 | 2803 | 23.20% |

The other dominant families are similarly stable. No source or length cohort
is sufficiently overrepresented to explain the excursion. Since DFM8 rows are
globally Philox-shuffled before Multipack allocation, a long contiguous source
run is not expected.

## Interpretation

The strongest current interpretation is a transient model/optimizer
instability at a constant, aggressive `4e-4` learning rate, possibly initiated
by one or a few unusually influential updates. It is not currently attributable
to a sampled-source distribution shift. The training path does not log gradient
or update norms and does not clip gradients, so the precise initiating update
cannot be reconstructed from existing telemetry. AdamATan2 bounds/scales
updates through `atan2`, so conventional global gradient clipping is not by
itself a complete explanation or guaranteed remedy.

The recovered step-151000 checkpoint is suitable for continued training. Do
not roll back solely because of this isolated event. If it recurs, capture
gradient norm, parameter/update norm, and non-finite counts before changing the
optimizer; repeated excursions would justify lowering LR or adding a guarded
rollback policy.

