---
type: Operational Record
title: Completion update (2026-06-07)
description: 'Chronological record from DFM L CP2 Evaluation Queue: Completion update
  (2026-06-07).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm-l-cp2-evaluation-queue.md
---
# Completion update (2026-06-07)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

Completion update, 2026-06-07. Confidence: high. The DFM4 XL-DDP no-EMA lite
eval for `step_500000` and `step_550000` completed with final status:

```text
2026-06-07T19:45:45+02:00 FINAL_MERGE_END step_500000 status_0
2026-06-07T19:47:06+02:00 FINAL_MERGE_END step_550000 status_0
2026-06-07T19:47:06+02:00 DONE status_0
```

For both checkpoints, all standard lite tasks and all DFM-lite tasks were
merged locally and synced under `lite_eval_noema/*` and
`lite_dfm_eval_noema/*`. Sample counts matched the lite shard expectations:
MATH `79`, DROP `2384`, GSM8k `165`, MMLU `3511`, HellaSwag `5021`, ARC
`1172`, Winogrande `1267`, BoolQ `3270`, GovReport `61`, WMT24++ en-da `120`,
NordjyllandNews `125`, HumanEval `41`, GEC-DALA `512`, Multi-Wiki-QA `1024`,
Danish citizen tests `545`, DALA `2048`, PIQA `108`, and IFEval-DA `17`.
