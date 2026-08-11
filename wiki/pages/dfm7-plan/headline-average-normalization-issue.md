---
type: Plan Record
title: Headline Average Normalization Issue
description: 'Part of DFM7 Plan: Headline Average Normalization Issue.'
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
# Headline Average Normalization Issue

Part of [DFM7 Plan](/pages/dfm7-plan.md).

Update, 2026-07-01. Confidence: high from local code changes, dry-run audit,
and completed W&B relog job.

- `scripts/log_dfm5_headline_averages.py` now uses metric-specific
  normalization for headline averages: all `euroeval/*` source metrics are
  divided by 100, while standard `eval/*` and the included `dfm_eval/*`
  headline metrics remain ratio-scale.
- GovReport is handled correctly in the headline average because the included
  key is `dfm_eval/govreport/bertscore_f1/mean`, which is ratio-scale. The
  local GovReport CHRF metrics are mixed/percent-like but are not members of
  the headline average key list.
- Future scheduler-generated average rows now write `headline_avg_v3/*` and
  `suite_avg_v3/*`. Existing v2 keys are intentionally left untouched.
- The active DFM6-to-DFM7 eval plan was edited under `PlanLock`: a
  project-wide `relog_project_averages` CPU row was prepended, and 28 pending
  average rows were changed from v2 prefixes to v3 prefixes.
- `scripts/relog_project_averages_v3.py` relogged corrected v3 averages from
  local W&B history for DFM5 project runs. Audit file:
  `logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253/relog_project_averages_v3_audit.jsonl`
  with 80 rows.
- The DFM5 workspace builder defaults now point average panels at
  `headline_avg_v3` and `suite_avg_v3`. A v3 SDK-created workspace was saved at
  `https://wandb.ai/peter-sk-sdu/DFM5?nw=k06l5ll2wq5`. The manual workspace
  id `nw=760qd0evtsa` could not be safely resolved through the available
  W&B workspace API surface during this session.
- Follow-up correction, 2026-07-01. Confidence: high from local audit rows and
  successful W&B sync. The first project-wide v3 relog only found two
  `dfm5-l-clean-20260619-v3` average points because that clean run's complete
  history lived mainly in audit JSONL files, not local `.wandb` files for the
  clean run id. The missing v3 average rows were recomputed from
  `logs/backfill_dfm5_l_clean_rows_v3_history650_20260619.jsonl`,
  `logs/append_dfm5_l_clean_from_oti1lisg_after820565_20260620.jsonl`, and
  `logs/relog_dfm5_l_clean_850k_900k_explicit_train_step_20260620.jsonl`, then
  logged to `dfm5-l-clean-20260619-v3` for 18 epochs from 0.276 through 4.970.
  The corrected workspace preserving the previous panel order, including Suite
  Averages, and placing per-section averages first is:
  `https://wandb.ai/peter-sk-sdu/DFM5?nw=3fvncok3gjh`.

DFM6-DFM7 math/code average anomaly, 2026-07-01. Confidence: high from local
inspection of `scripts/log_dfm5_headline_averages.py`,
`eval_scheduler/eval_scheduler/plan.py`, and local EuroEval BFCL merged metric
files.

Observed issue:

- The Math & Code headline average uses four metrics:
  `eval/GSM8k/acc`, `eval/MATH/acc`,
  `dfm_eval/humaneval/verify_sanitized/accuracy`, and
  `euroeval/en/tool-calling/bfcl-v2/tool_calling_accuracy`.
- The average normalizer in `scripts/log_dfm5_headline_averages.py` is generic:
  values in `[0, 1]` are used directly, values in `(1, 100]` are divided by
  100, and larger values are ignored.
- Local DFM6-DFM7 BFCL merged metrics show a scale break between checkpoints:
  step 750000 has `tool_calling_accuracy=0.48`, while step 800000 has
  `tool_calling_accuracy=2.44`. The current normalizer therefore treats these
  as `0.48` and `0.0244`, respectively.
- This can make the Math & Code average go down even when all visible raw
  component panels go up. It is an averaging/normalization artifact, not by
  itself evidence that the model got worse.

Recommended fix:

- Make average normalization metric-specific rather than relying on the generic
  `>1 means percent` heuristic.
- For BFCL/tool-calling, first determine the intended EuroEval scale and then
  either normalize at ingestion/merge time to a stable `[0, 1]` metric or use a
  corrected metric-specific average key. Do not silently mix `0.48` as a ratio
  with `2.44` as a percent in the same headline average.
- Until fixed and backfilled, interpret `avg/math_code` and
  `headline_avg_v2/math_code` cautiously for checkpoints whose BFCL metric
  crosses above 1.
