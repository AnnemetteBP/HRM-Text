---
type: Operational Record
title: DFM5 comparison table Qwen baselines (2026-06-16)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5 comparison
  table Qwen baselines (2026-06-16).'
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
# DFM5 comparison table Qwen baselines (2026-06-16)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5 comparison table Qwen baselines, 2026-06-16. Confidence: high for the
local `docs/dfm5.md` and
`scripts/generate_dfm5_l_eval_comparison_report.py` edits, HRM-Text arXiv v1
Table 4 inspection, and Qwen3.5-9B model-card inspection. The generator now
preserves `Qwen3.5 2B` and `Qwen3.5 9B` columns whenever `docs/dfm5.md` is
regenerated. HRM-Text arXiv v1 Table 4 reports same-suite standard English
values for `Qwen3.5 2B` only:

```text
MMLU=64.5, ARC-C=81.0, HellaSwag=64.6, Winogrande=56.7,
BoolQ=80.5, DROP=30.8, GSM8K=53.0, MATH=34.2
```

The same arXiv table does not report `Qwen3.5 9B`, so that column is present
but left unavailable (`—`) until a same-suite authoritative source is found.
The official Qwen3.5-9B model card does report adjacent newer language
benchmarks: `MMLU-Pro=82.5`, `MMLU-Redux=91.1`, `C-Eval=88.2`,
`SuperGPQA=58.2`, `GPQA Diamond=81.7`, `IFEval=91.5`, `IFBench=64.5`,
`Global PIQA=83.2`, and `WMT24++=72.6`. These are noted in `docs/dfm5.md`
but not inserted into the main benchmark rows because they are not the same
benchmark/configuration as the HRM-Text standard table. The Slack table exports
under `docs/dfm5_slack_tables/` were regenerated from the updated Markdown and
now have 15 columns.
