---
type: Operational Record
title: Clarification added (2026-06-04)
description: 'Chronological record from dfm-evals: Clarification added (2026-06-04).'
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
# Clarification added (2026-06-04)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Clarification added 2026-06-04: the `lite_eval_noema/*` and
`lite_dfm_eval_noema/*` relog above is not evidence of a true non-EMA original
Sapient L evaluation, because it reused the existing generic lite eval outputs
without rerunning inference. The original launch command did not set `NO_EMA=1`,
and `scripts/schedule_multiple_checkpoint_evals.sh` defaults `NO_EMA=0`, so
the underlying generic `lite_eval/*` outputs should be treated as default EMA
evals. A local search found no separate `original_sapient*noema*` eval root or
recorded `NO_EMA=1` original Sapient L run. Confidence: high for the local
search and relog fact; Confidence: medium for the default-EMA interpretation.
