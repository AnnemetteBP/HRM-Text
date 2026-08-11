---
type: Operational Record
title: Superseded on (2026-05-24)
description: 'Chronological record from dfm-evals: Superseded on (2026-05-24).'
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
# Superseded on (2026-05-24)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Superseded on 2026-05-24: the suite-level `--limit 250` was removed from `config/dfm_evals_hrm.yaml` so task defaults are used. The public Danish citizen tests task selected `545` samples after its split/dedup logic. Epoch 1 completed that task and a manual partial W&B sync logged `dfm_eval/danish-citizen-tests/knowledge/accuracy=0.0055` and `dfm_eval/danish-citizen-tests/knowledge/dfm_evals_mcc=-0.01355` to run `origLclean`. Confidence: high.
