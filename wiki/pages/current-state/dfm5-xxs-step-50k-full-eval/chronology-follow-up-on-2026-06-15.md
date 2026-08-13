---
type: Operational Record
title: Follow-up on (2026-06-15)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Follow-up on
  (2026-06-15).'
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
# Follow-up on (2026-06-15)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Follow-up on 2026-06-15: the DFM5 headline-average definitions were updated in
code to match the live workspace/report panel choices. Confidence: high for
local script validation and dry-run output.

Changed files:

```text
scripts/log_dfm5_headline_averages.py
scripts/create_dfm5_headline_workspace.py
scripts/generate_dfm5_l_eval_comparison_report.py
```

Superseded in the same session for DROP: the headline averages now use:

- `dfm_eval/multi_wiki_qa/exact_match/mean` instead of
  `dfm_eval/multi_wiki_qa/f1/mean`.
- `dfm_eval/nordjyllandnews/bertscore_f1/mean` instead of
  `dfm_eval/nordjyllandnews/rouge2/mean`.
- `eval/DROP/f1`; DROP was intentionally kept on F1 so the Markdown comparison
  table remains comparable to the model-card DROP F1 values.
- `dfm_eval/govreport/bertscore_f1/mean` instead of
  `dfm_eval/govreport/rouge2/mean`.

VaLEU remains visible in the workspace/report but excluded from all headline
averages. The regenerated local Markdown report is:

```text
logs/reports/dfm5_l_eval_comparison_50k_100k_150k_vs_original_ema_and_card.md
```

Dry-run corrected DFM5-L headline averages with DROP kept on F1:

```text
50K:  Danish=0.3204938053  English=0.3394398505  MathCode=0.0648775454  Overall=0.2416037337
100K: Danish=0.3856718136  English=0.4337499937  MathCode=0.1409537807  Overall=0.3201251960
150K: Danish=0.4332904762  English=0.5028531674  MathCode=0.1945934388  Overall=0.3769123608
200K: Danish=0.4480947019  English=0.5191093860  MathCode=0.2233228181  Overall=0.3968423020
```

W&B run `DFM5/oti1lisg` currently has four old `headline_avg/*` history rows.
W&B history rows are append-only, so replacing those points cleanly requires
either a corrected/new run or new metric keys plus panel updates; appending the
corrected rows under the same keys would create duplicate points at the same
`headline_avg/epoch` x-values.

The average logger now defaults to `avg/*` and supports `--metric-prefix` for
overrides. The workspace builder now defaults to `avg/*` and supports
`--headline-avg-prefix` for overrides. This means the running 250K post-eval
watcher, which calls the average logger without an explicit prefix, will log
250K averages under `avg/*`.

The live workspace `https://wandb.ai/peter-sk-sdu/DFM5?nw=yl894iibtp5` and the
shared report `DFM5--VmlldzoxNzIzNTc1Nw` were patched in place on 2026-06-15:

- Headline average panels now use `avg/overall`, `avg/danish`, `avg/english`,
  and `avg/math_code` with x-axis `avg/epoch`.
- No `headline_avg/` panel references remain in the live workspace.
- DROP was restored to `DROP F1` using `eval/DROP/f1`.

Patch snapshots:

```text
logs/wandb_workspace_specs/dfm5_live_yl894iibtp5_after_avg_dropf1_patch_20260615.json
logs/wandb_workspace_specs/dfm5_report_VmlldzoxNzIzNTc1Nw_after_avg_dropf1_patch_20260615.json
```

Follow-up: because `avg/*` did not yet have logged history rows, W&B initially
hid the new average-only section and the average panels when
`showEmptySections=false`. The live workspace was patched in place to set panel
bank `showEmptySections=true`. Verification from the live spec showed:

```text
Headline Averages: 4 panels
Danish Headline Metrics: 20 panels
English Headline Metrics: 17 panels
Math & Code Headline Metrics: 5 panels
Training Metrics & Params: 9 panels
```

Snapshot:

```text
logs/wandb_workspace_specs/dfm5_live_yl894iibtp5_show_empty_sections_20260615.json
```
