---
type: Operational Record
title: DFM5 L step100000 full eval launch (2026-06-14)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5 L step100000
  full eval launch (2026-06-14).'
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
# DFM5 L step100000 full eval launch (2026-06-14)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5 L `step_100000` full eval launch, 2026-06-14. Confidence: high for local
tmux/status logs. `scripts/schedule_checkpoint_evals.sh` now supports
`QUEUE_ORDER=euroeval_first`, which enqueues the 20 one-dataset EuroEval jobs
before DFM IFEval-DA, standard evals, and the remaining DFM evals. This is meant
to avoid EuroEval becoming the long tail. The first attempted launch omitted
`EUROEVAL_BIN=/work/dfm/HRM-Text/scripts/euroeval_api_no_flash_attn_guard.py`;
EuroEval immediately failed with its top-level `flash_attn` import guard. That
bad tmux session/log family was stopped and replaced with a guarded run:

```text
tmux session: dfm5_L_step100000_full_eurofirst_guard
checkpoint:   checkpoints/dfm5/L step_100000
eval epoch:   0.5521769236437283
W&B target:   DFM5 / oti1lisg / dfm5-L
log root:     logs/eval/dfm5_L_step100000_full_20260614_eurofirst_guard
dfm root:     logs/dfm_evals/dfm5_L_step100000_full_20260614_eurofirst_guard
euro root:    logs/euroeval/dfm5_L_step100000_full_20260614_eurofirst_guard
```

The guarded launch queued `188` jobs and started with EuroEval
`angry-tweets`, `scala-da`, `dansk`, and `multi-wiki-qa-da`. At the first
status check there were no recorded failed attempts in
`eval_attempts.tsv`; the started EuroEval jobs were still running.
