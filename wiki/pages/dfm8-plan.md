---
type: Knowledge Collection
title: DFM8 Plan
description: DFM8 dataset, synthetic-data, post-training, training, and evaluation
  plan.
tags:
- dfm8
- data
- synthetic-data
- training
- evaluation
status: stable
last_updated: '2026-08-11'
confidence: medium
collection_type: Training Data Plan
---
# DFM8 Plan

Operational update, 2026-07-13. Confidence: high from local tmux/process/log
inspection. Restarting `dfm8_openhermes_repaired/scripts/run_openhermes_repair_8gpu.sh`
with an existing `data/dfm8_openhermes_repaired` work root resumes safely, but
it re-enters the stages in order. Completed shard files are not regenerated
wholesale; however, row-level failures are archived and retried. This can make
the GPUs show short changing bursts of 100% utilization while the runner sweeps
through an already-completed stage such as `source_audit`, retrying only a few
failed rows per shard, before it returns to the unfinished stage. This behavior
is expected and should be monitored through worker logs and output row counts,
not only through `nvidia-smi` utilization.

The detailed sections of this collection are maintained as separate OKF concepts.

## Objectives

[Open the dedicated concept](dfm8-plan/objectives.md).

## Implementation Plan

[Open the dedicated concept](dfm8-plan/implementation-plan.md).

## Danish Education Data

[Open the dedicated concept](dfm8-plan/danish-education-data.md).

## Targeted Synthetic Generation Operations

[Open the dedicated concept](dfm8-plan/targeted-synthetic-generation-operations.md).

## Token Delta Estimate Versus DFM7

[Open the dedicated concept](dfm8-plan/token-delta-estimate-versus-dfm7.md).

## Danish Linguistic Acceptability And GEC Data

[Open the dedicated concept](dfm8-plan/danish-linguistic-acceptability-and-gec-data.md).

## English General SFT And Format-Following Candidates

[Open the dedicated concept](dfm8-plan/english-general-sft-and-format-following-candidates.md).

## Math Answer-Contract Fix

[Open the dedicated concept](dfm8-plan/math-answer-contract-fix.md).

## Danish DAISY Eval Candidate

[Open the dedicated concept](dfm8-plan/danish-daisy-eval-candidate.md).

## Tool-Calling Carryover

[Open the dedicated concept](dfm8-plan/tool-calling-carryover.md).

## Epoch 5 Qualitative Smoke

[Open the dedicated concept](dfm8-plan/epoch-5-qualitative-smoke.md).

## Broad Synthetic Common Pile and DynaWord Scaling

[Open the dedicated concept](dfm8-plan/broad-synthetic-common-pile-and-dynaword-scaling.md).

## Build Requirements

[Open the dedicated concept](dfm8-plan/build-requirements.md).

## Additional Synthetic Data Candidates

[Open the dedicated concept](dfm8-plan/additional-synthetic-data-candidates.md).

## Active Post-Audit Operational Plan

[Open the dedicated concept](dfm8-plan/active-post-audit-operational-plan.md).

## DFM8 Targeted Synthetic Upload

[Open the dedicated concept](dfm8-plan/dfm8-targeted-synthetic-upload.md).

## Danish OpenHermes Synthetic Run

[Open the dedicated concept](dfm8-plan/danish-openhermes-synthetic-run.md).

## DFM8 Post-Training / RL Subset

[Open the dedicated concept](dfm8-plan/dfm8-post-training-rl-subset.md).

## DFM8 Synthetic/OpenHermes Pipeline Status

[Open the dedicated concept](dfm8-plan/dfm8-synthetic-openhermes-pipeline-status.md).

## Hugging Face Availability

[Open the dedicated concept](dfm8-plan/hugging-face-availability.md).

## DFM8 One-Epoch Continuation From DFM6/DFM7 XL

[Open the dedicated concept](dfm8-plan/dfm8-one-epoch-continuation-from-dfm6-dfm7-xl.md).

## DFM8 L Resume On 2026-08-01

[Open the dedicated concept](dfm8-plan/dfm8-l-resume-on-2026-08-01.md).

## DFM8 L Alternating Training/Evaluation Campaign

[Open the dedicated concept](dfm8-plan/dfm8-l-alternating-training-evaluation-campaign.md).

## DFM8 L Second-Epoch Campaign

[Open the dedicated concept](dfm8-plan/dfm8-l-second-epoch-campaign.md).
