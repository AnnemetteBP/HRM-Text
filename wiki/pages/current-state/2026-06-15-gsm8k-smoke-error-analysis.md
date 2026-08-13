---
type: Operational Record
title: 2026-06-15 GSM8k Smoke Error Analysis
description: 'Part of Current State: 2026-06-15 GSM8k Smoke Error Analysis.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# 2026-06-15 GSM8k Smoke Error Analysis

Part of [Current State](/pages/current-state.md).

Confidence: high for local runs and saved artifacts; medium for manual failure
bucket labels because many wrong completions are bare numeric answers with no
trace.

The same `100` randomly sampled GSM8k test rows were run with seed
`20260615` through DFM5-L `step_200000` and the locally trained original
Sapient L `epoch_4`, both with EMA/default weights, `condition=direct`, and
`temperature=0.0`.

Raw eval-style prompt scores:

```text
DFM5-L step_200000:        22/100
original Sapient L epoch4: 41/100
```

Show-work prompt scores, used for interpretable buckets:

```text
DFM5-L step_200000:        31/100
original Sapient L epoch4: 41/100
```

Manual bucket counts from the show-work run:

```text
bucket                                  DFM5-L  original Sapient L
correct                                    31                  41
bare_wrong_number_no_trace                 62                  58
correct_reasoning_unparseable_format        2                   0
wrong_setup_in_worked_solution              2                   0
incomplete_or_truncated_reasoning           1                   0
invalid_non_numeric_final                   1                   0
dataset_gold_ambiguity                      1                   1
```

Main interpretation: the observed DFM5-L GSM8k lag is mostly not exposed as
long faulty reasoning; even when asked to show work, both models often emit only
bare numbers. Original Sapient L gets more of those bare-number cases right.
DFM5-L also shows a few format/scoring and worked-solution setup failures that
did not appear in this original Sapient L sample.

Artifacts:

```text
scripts/smoke_gsm8k_error_analysis.py
logs/analysis/gsm8k_smoke_dfm5_L_step200000_seed20260615.json
logs/analysis/gsm8k_smoke_dfm5_L_step200000_seed20260615_show_work.json
logs/analysis/gsm8k_smoke_original_sapient_L_epoch4_seed20260615.json
logs/analysis/gsm8k_smoke_original_sapient_L_epoch4_seed20260615_show_work.json
logs/analysis/gsm8k_smoke_dfm5_vs_original_sapient_L_seed20260615.md
logs/analysis/gsm8k_smoke_dfm5_vs_original_sapient_L_seed20260615_counts.json
```
