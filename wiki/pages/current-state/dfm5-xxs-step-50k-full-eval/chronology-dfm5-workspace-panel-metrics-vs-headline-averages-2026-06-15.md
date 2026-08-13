---
type: Operational Record
title: DFM5 workspace panel metrics vs headline averages (2026-06-15)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5 workspace
  panel metrics vs headline averages (2026-06-15).'
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
# DFM5 workspace panel metrics vs headline averages (2026-06-15)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5 workspace panel metrics vs headline averages, 2026-06-15. Confidence:
high for the live W&B workspace spec fetched with `wandb_workspaces`.

The live workspace `https://wandb.ai/peter-sk-sdu/DFM5?nw=yl894iibtp5`
(`DFM5 headline metrics`) was fetched to:

```text
logs/wandb_workspace_specs/dfm5_live_yl894iibtp5_20260615.json
```

The visible panels currently differ from `scripts/log_dfm5_headline_averages.py`
in these substantive places:

- Danish MultiWikiQA panel uses `dfm_eval/multi_wiki_qa/exact_match/mean`,
  while the Danish average still uses `dfm_eval/multi_wiki_qa/f1/mean`.
- Danish NordjyllandNews panel uses
  `dfm_eval/nordjyllandnews/bertscore_f1/mean`, while the Danish average still
  uses `dfm_eval/nordjyllandnews/rouge2/mean`.
- English DROP panel uses `eval/DROP/em`, while the English average still uses
  `eval/DROP/f1`.
- English GovReport panel uses `dfm_eval/govreport/bertscore_f1/mean`, while
  the English average still uses `dfm_eval/govreport/rouge2/mean`.

The workspace also shows EuroEval VaLEU panels for Danish and English
(`euroeval/da/european-values/valeu-da/european_values` and
`euroeval/en/european-values/valeu-en/european_values`), but these remain
excluded from the headline averages by the earlier VaLEU exclusion policy.

The W&B report shared via `https://api.wandb.ai/links/peter-sk-sdu/iboaiazf`
resolves to report `DFM5--VmlldzoxNzIzNTc1Nw`; its spec was fetched to:

```text
logs/wandb_workspace_specs/dfm5_report_VmlldzoxNzIzNTc1Nw_20260615.json
```

The report's panel metrics initially matched the workspace mismatches above:
MultiWikiQA exact-match vs average F1, NordjyllandNews BERTScore vs average
ROUGE-2, DROP exact-match vs average F1, GovReport BERTScore vs average
ROUGE-2, and visible VaLEU panels that remain excluded from averages.
