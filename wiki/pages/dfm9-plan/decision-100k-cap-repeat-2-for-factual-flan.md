---
type: Plan Record
title: 'Decision: 100K cap + repeat 2 for factual FLAN'
description: 'Part of DFM9 Plan: Decision: 100K cap + repeat 2 for factual FLAN.'
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
# Decision: 100K cap + repeat 2 for factual FLAN

Part of [DFM9 Plan](/pages/dfm9-plan.md).

Decided 2026-08-07. Confidence: high.

**Cap**: `max_per_file: 100000` for factual-knowledge FLAN files (up from 5,000).
**Repeat**: `repeat: 2` for factual-knowledge FLAN files (up from implicit 1).

This gives each unique factual row 2 × 3 = 6 exposures over 3 training epochs
(was 3), with ~10M unique rows (was ~2M).

Projected impact (all 22 factual FLAN datasets):
- Tokens/epoch: 5.59B × 2 = 11.18B (15.9% of epoch, was 1.3%)
- Over 3 epochs: 33.6B tokens (was 2.8B)
- Unique rows: 10.0M (was 2.0M)
- Exposures per row: 6x (was 3x)

Key factual datasets only (TriviaQA + SQuAD + NQ + HotpotQA):
- Tokens/epoch: 0.81B × 2 = 1.62B (2.3% of epoch, was 0.17%)
- Over 3 epochs: 4.9B tokens (was 0.36B)
- Unique rows: 3.3M (was 281K)
- Exposures per row: 6x (was 3x)
