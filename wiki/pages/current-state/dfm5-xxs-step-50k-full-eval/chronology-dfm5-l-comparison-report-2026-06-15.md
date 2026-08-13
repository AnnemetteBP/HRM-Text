---
type: Operational Record
title: DFM5 L comparison report (2026-06-15)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5 L comparison
  report (2026-06-15).'
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
# DFM5 L comparison report (2026-06-15)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5 L comparison report, 2026-06-15. Confidence: high for local artifact
extraction. A Markdown table comparing DFM5-L `step_50000`, `step_100000`,
and `step_150000` against the earlier original Sapient L run and README
model-card L/XL values was written to:

```text
logs/reports/dfm5_l_eval_comparison_50k_100k_150k_vs_original_ema_and_card.md
```

Source policy for that report:

- DFM5-L columns use the local full eval merged artifacts under
  `logs/eval`, `logs/dfm_evals`, and `logs/euroeval` for the corresponding
  `dfm5_L_step{50000,100000,150000}_full_*` roots.
- Original Sapient L uses EMA/default sources only: the full epoch-4 standard
  eval log `logs/eval/original_sapient_L/epoch_4.log`, the original epoch-4
  EuroEval JSONL `logs/euroeval/original_sapient_L/epoch_4/euroeval_benchmark_results.jsonl`,
  and the default/EMA local DFM-evals artifacts under
  `logs/dfm_evals/original_sapient_L_lite_all_checkpoints_20260603T213010/epoch_4`.
- Explicit `*_noema_*` roots are intentionally excluded from this comparison.
- README model-card L/XL columns are populated only for the standard benchmark
  metrics shown in `README.md`.
- On 2026-06-15, section average rows were added to the Markdown report for
  Danish, English, and Math & Code. The averages are percent-style values for
  the DFM5-L and original Sapient L columns only; the model-card average cells
  remain blank because the card provides only a subset of standard benchmarks.
  Danish and English averages follow the headline-dashboard convention and
  exclude VaLEU rows.
- Later on 2026-06-15, the report was expanded from only original Sapient L
  epoch 4 to original Sapient L epochs 1, 2, 3, and 4, all using EMA/default
  sources. The original Sapient L epoch-2 EuroEval source file does not contain
  the `valeu-da` row, so that cell is reported as `—`; this does not affect the
  Danish average because VaLEU rows are excluded from section averages.
