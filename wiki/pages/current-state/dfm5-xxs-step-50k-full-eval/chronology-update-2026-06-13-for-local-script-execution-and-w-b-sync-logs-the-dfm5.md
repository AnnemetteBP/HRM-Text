---
type: Operational Record
title: 'Update 2026-06-13: for local script execution and W&B sync logs. The DFM5'
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Update 2026-06-13:
  for local script execution and W&B sync logs. The DFM5.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# Update 2026-06-13: for local script execution and W&B sync logs. The DFM5

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-06-13. Confidence: high for local script execution and W&B sync
logs. The DFM5 headline workspace now includes derived section-average panels
at the top of Danish, English, and Math & Code. The averages are logged as
real W&B metrics rather than workspace-only expressions, because the source
metrics are split across `eval/*`, `dfm_eval/*`, and `euroeval/*` rows. Script:

```text
scripts/log_dfm5_headline_averages.py
```

Metric keys:

```text
headline_avg/epoch
headline_avg/train_step
headline_avg/danish
headline_avg/danish/count
headline_avg/english
headline_avg/english/count
headline_avg/math_code
headline_avg/math_code/count
headline_avg/overall
```

Values are unweighted arithmetic means of the section's headline metrics,
including EuroEval panels, after normalizing each metric to 0-1. Values already
in `[0, 1]` are kept; values in `(1, 100]` are divided by 100; negative values
are clamped to 0; non-finite or larger-than-100 values are skipped. The `count`
metrics record how many source metrics were present.

Superseded: the first backfill excluded EuroEval and produced:

```text
step_50000  epoch=0.276088            danish=0.076141 english=0.255659 math_code=0.016349 overall=0.116050
step_100000 epoch=0.5521769236437283  danish=0.082365 english=0.244336 math_code=0.022722 overall=0.116475
```

Superseded: the second backfill included EuroEval including VaLEU where
available. That made counts differ across checkpoints because VaLEU can abort
without writing a result record:

```text
step_50000  epoch=0.276088            danish=0.147101 count=19 english=0.191901 count=16 math_code=0.012262 count=4 overall=0.117088
step_100000 epoch=0.5521769236437283  danish=0.156194 count=18 english=0.230057 count=15 math_code=0.017042 count=4 overall=0.134431
```

The `step_100000` counts are lower than `step_50000` because the local
EuroEval merged files present at backfill time were missing one Danish and one
English primary EuroEval metric. Follow-up inspection showed the missing
metrics are `euroeval/da/european-values/valeu-da/european_values` and
`euroeval/en/european-values/valeu-en/european_values`. EuroEval did start
both VaLEU tasks, but aborted them because the model produced labels outside
the allowed candidate set and the task does not allow invalid outputs:

```text
ValEU-da: No candidate labels found ... 8/53 samples ... abort the evaluation.
VaLEU-en: No candidate labels found ... 3/53 samples ... abort the evaluation.
```

Because no VaLEU result records were written to
`euroeval_benchmark_results.jsonl`, the merged EuroEval metric files contain
only the other dataset from each group (`ifeval-da` for group 3 and `bfcl-v2`
for group 7). The headline-average script currently skips missing metrics
rather than treating aborted tasks as zero.

Current policy as of `2026-06-13`: VaLEU metrics are kept as workspace panels
but excluded from the section averages. This keeps average counts stable across
checkpoints while preserving the raw VaLEU panel for inspection.

The no-VaLEU average rows were synced to W&B project `DFM5`, run id
`2tv9u438`, by:

```bash
cd /work/dfm/HRM-Text
python scripts/log_dfm5_headline_averages.py \
  --item '50000:0.276088:logs/eval/dfm5_XXS_step50000_full_20260613:logs/dfm_evals/dfm5_XXS_step50000_full_20260613:logs/euroeval/dfm5_XXS_step50000_parallel_20260613' \
  --item '100000:0.5521769236437283:logs/eval/dfm5_XXS_100k_150k_full_20260613_100k_150k/step_100000:logs/dfm_evals/dfm5_XXS_100k_150k_full_20260613_100k_150k/step_100000:logs/euroeval/dfm5_XXS_100k_150k_full_20260613_100k_150k/step_100000' \
  --item '150000:0.8282653854655924:logs/eval/dfm5_XXS_step150000_full_highbs_20260613_step150_highbs/step_150000:logs/dfm_evals/dfm5_XXS_step150000_full_highbs_20260613_step150_highbs/step_150000:logs/euroeval/dfm5_XXS_step150000_full_highbs_20260613_step150_highbs/step_150000'
```

The synced no-VaLEU values are:

```text
step_50000  epoch=0.276088            danish=0.153509 count=18 english=0.203071 count=15 math_code=0.012262 count=4 overall=0.122947
step_100000 epoch=0.5521769236437283  danish=0.156194 count=18 english=0.230057 count=15 math_code=0.017042 count=4 overall=0.134431
step_150000 epoch=0.8282653854655924  danish=0.179091 count=18 english=0.220028 count=15 math_code=0.012290 count=4 overall=0.137136
```

W&B client output confirmed upload and summary update for
`headline_avg/{danish,english,math_code,overall}`. A W&B API `scan_history`
probe was too slow and was terminated; the sync log is
`logs/wandb_log_dfm5_headline_averages_no_valeu_50k_100k_150k_20260613.log`.
```

The saved workspace URL after adding the average panels is:

```text
https://wandb.ai/peter-sk-sdu/DFM5?nw=ggywzrf0fxl
```
