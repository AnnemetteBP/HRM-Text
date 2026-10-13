---
type: Plan
title: DFM15 Native Reasoning
description: Native thinking and direct-answer supervision inherited from immutable DFM14.
status: draft
confidence: high
last_updated: 2026-10-09
tags: [dfm15, reasoning, data, training]
---
# DFM15

## Evaluation Inheritance

Retain the complete [DFM14 evaluation baseline](dfm14-evaluation-baseline.md),
including all 50 languages and Andersen modernization. Native-reasoning
diagnostics are separately named additions, not replacements for existing
benchmarks or average populations; proposed additions are listed there.

## Version Boundary

User decision on 2026-10-09: native-reasoning repairs belong to **DFM15**.
DFM14 remains unchanged. Do not promote either the old plaintext repair or
the native-reasoning staging output into `data/sampled_dfm14`; do not change
ongoing DFM14 training or its scheduler as part of this data preparation.

The completed CPU build has been designated the first DFM15 staged base:

- Work root: `data/dfm15/native-reasoning-v2`.
- Sample: `data/dfm15/native-reasoning-v2/sampled_dfm15`.
- Three index sets: `epoch_0`, `epoch_1`, `epoch_2`.
- Mean tokens per epoch: **134,359,356,757** (134.359B).
- Native-thinking occurrences from repaired sources: about **2.079M per epoch**.
- Quarantined sampled occurrences removed: **38,828 / 38,976 / 38,996**.
- Status: validated staging, not promoted, not selected by live training.
- Original build log remains `logs/dfm14/native-reasoning-v2/build.log` as
  historical evidence; the build started before the DFM15 naming decision.

## Policy and Implementation

Preserve well-formed reasoning and final answers separately in native Gemma
channels with thinking enabled. Repair only unambiguous malformed boundaries;
retain an intact final answer in non-thinking mode when reasoning cannot safely
be retained or exceeds context. Quarantine examples without a complete usable
answer. Keep ordinary direct-answer supervision. Never truncate a thought
channel or remove its final answer merely to meet context length.

The implementation currently lives in `dfm14/native_reasoning.py` and
`dfm14/build_native_reasoning.py` because DFM14 is its immutable input. Its
default output is now DFM15. See the [repair details and history](dfm14-cpu-release.md)
for source coverage, tests, tool-specific repairs and evidence layout.
The stage carries its own template; shared/live templates remain untouched.

Before eventual training: finalize other DFM15 additions, review mode exposure,
select the required epoch index convention, calculate the packed-step budget,
and perform a checkpoint-safe explicit data switch. None of these are implied
by naming this staged corpus DFM15.
