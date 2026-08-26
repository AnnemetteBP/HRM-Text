---
type: Plan Record
title: Motivation
description: 'Part of DFM9 Plan: Motivation.'
tags:
- dfm9
- data
- training
- factual-knowledge
- code
status: stable
last_updated: 2026-08-18
confidence: high
part_of: /pages/dfm9-plan.md
---
# Motivation

Part of [DFM9 Plan](/pages/dfm9-plan.md).

FlexOlmo comparison evals on DFM8 XL (step 1,650,000, published as HRM-Mimir-v1)
revealed genuine factual knowledge gaps:

| Task | Mimir | FlexOlmo (full) | Gap | Root cause |
| --- | ---: | ---: | ---: | --- |
| NQ-Open | 12.5% F1 | 19.6% | -7.1pp | Wrong facts |
| TriviaQA | 21.2% F1 | 57.1% | -35.9pp | Wrong facts (severe) |
| MMLU-Pro | 24.8% | 41.3% | -16.5pp | Mixed: ~13pp format (fixed via scoring patch), ~3.5pp genuine |

Weakest knowledge domains (across NQ-Open, TriviaQA, MMLU-Pro):
- Entertainment/Movies/TV/Music: 27-30% of wrong answers
- History: 12.7% MMLU-Pro accuracy (weakest subject)
- Law/Philosophy: 16.0-16.3% MMLU-Pro
- Geography: 9-11% of wrong answers
- Sports: 9% of wrong answers

Scoring fixes already applied (not data issues):
- MMLU-Pro: `\boxed{LETTER}` extraction patch in `flexolmo.py` → ~38% (from 24.8%)
- AGIEval: bare-letter rescoring → 50.7% (from 37.6%, beats FlexOlmo 45.1%)
- BBH: bare-letter rescoring → 45.2% (from 28.9%, near FlexOlmo 46.4%)
- PIQA: bare-letter rescoring → 77.1% (from 0%)
