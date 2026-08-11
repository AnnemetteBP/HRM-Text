---
type: Plan Record
title: DFM6-DFM7 Progress Assessment
description: 'Part of DFM7 Plan: DFM6-DFM7 Progress Assessment.'
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
# DFM6-DFM7 Progress Assessment

Part of [DFM7 Plan](/pages/dfm7-plan.md).

Assessment on 2026-07-03 after fixing the 900K BFCL shard and before the
950K+ queued evaluations. Confidence: high for numbers taken from local
reports and scheduler state; confidence: medium for trend interpretation.
The initial same-day interpretation that "math is mixed" and "HumanEval is
noisy" was too conservative because it over-emphasized one 750K->900K headline
slice and under-emphasized the actual before/after DFM7-switch comparison.

- The active run is `DFM6-DFM7-XL-gas2` in the `DFM5` W&B project. W&B summary
  inspection showed it running around step 907K with `train/loss` about 1.066.
- The eval scheduler has completed the 900K rerun, including BFCL-v2 and all
  v4 averages/reports, and is waiting on future checkpoints 950K, 1000K,
  1050K, 1100K, 1150K, 1200K, and 1250K.
- Overall training progress is strong from early checkpoints to 900K:
  - Danish headline average rose from about 32.0 at 50K to about 51.1 at 900K.
  - English headline average rose from about 33.9 at 50K to about 66.6 at 900K.
  - Math/code headline average rose from about 6.5 at 50K to about 31.2 at
    900K, but this section is noisy because BFCL-v2 has been unstable and
    sparse.
- Since the DFM7 switch, the corrected interpretation is:
  - MATH has improved materially, roughly from the low 30s to about 49 on the
    current evaluated checkpoints.
  - HumanEval has also improved materially, roughly from the mid 40s to the low
    50s on the relevant post-switch comparison.
  - English and Danish headline averages look near-converged, but that hides
    different sub-suite behavior. W&B `suite_avg_v3` rows show continued
    movement across the DFM7-relevant 700K-900K window:
    - Standard: 0.6891 -> 0.6963 -> 0.7011 -> 0.7068 -> 0.7078.
    - DFM-evals: 0.5851 -> 0.6008 -> 0.5914 -> 0.5936 -> 0.6241.
    - EuroEval: 0.5209 -> 0.5365 -> 0.5527 -> 0.5581 -> 0.5583.
    W&B query caveat: 850K and 900K suite rows were logged as separate
    one-suite rows at different internal `_step`s, so querying all suite keys
    in one sparse-history request can miss them. Query each suite key separately
    or group by `suite_avg_v3/train_step`.
  - Tool calling is not solved: the corrected 900K BFCL-v2 rerun scored about
    2.32% tool-calling accuracy. The earlier 750K BFCL spike should not be
    treated as evidence of stable tool-calling competence.
- Interpretation: DFM7 has not caused broad degradation and appears to have
  helped math/code more than the original headline summary suggested. The main
  unresolved targeted gap is still native tool calling. If 950K and 1000K do
  not move BFCL-v2 materially above the low single digits, the remaining
  problem is probably data density/format alignment rather than insufficient
  continuation alone.
