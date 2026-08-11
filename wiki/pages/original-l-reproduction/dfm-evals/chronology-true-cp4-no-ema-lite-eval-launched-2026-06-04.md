---
type: Operational Record
title: True CP4 no-EMA lite eval, launched (2026-06-04)
description: 'Chronological record from dfm-evals: True CP4 no-EMA lite eval, launched
  (2026-06-04).'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction/dfm-evals.md
---
# True CP4 no-EMA lite eval, launched (2026-06-04)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

True CP4 no-EMA lite eval, launched 2026-06-04. Confidence: high for the
command and local paths.

The real original Sapient L CP4 no-EMA lite eval was launched immediately in
tmux window `hrm:7` (`origL-cp4-noema-now`) after first staging, then removing,
a free-GPU preflight wait loop. It is local only (`WANDB_SYNC=0`) and uses
distinct prefixes so it cannot be confused with the earlier relogged metrics.
It queued `19` jobs and started workers `349165` through `349172`; the first
wave started `dfm_ifeval`, `MATH`, `GSM8k`, `DROP`, `MMLU`, `HellaSwag`, `ARC`,
and `Winogrande`.
