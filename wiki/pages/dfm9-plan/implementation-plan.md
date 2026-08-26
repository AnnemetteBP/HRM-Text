---
type: Plan Record
title: Implementation Plan
description: 'Part of DFM9 Plan: Implementation Plan.'
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
# Implementation Plan

Part of [DFM9 Plan](/pages/dfm9-plan.md).

## 1. Split FLAN prefix for selective cap raising
The current single `flan__` prefix applies one cap to all FLAN files. To apply
100K + repeat 2 only to factual-knowledge files while leaving other FLAN at 5K,
the FLAN files must be split into sub-prefixes in the tokenized tree.

Factual-knowledge FLAN files (100K cap, repeat 2):
- TriviaQA, SQuAD, Natural Questions, HotpotQA, WebQuestions, KILT, RACE,
  DROP, CoQA, QuAC, ROPES, WikiDialog, DREAM, BoolQ

Science/reasoning FLAN files (keep at current 5K cap, repeat 1):
- ARC, OpenBookQA, SciQ, QASC, CommonsenseQA, PIQA, HellaSwag, Winogrande

These already perform well in evals — no need to boost.

Implementation approach: create symlinks in `data/tokenized_dfm9/` that rename
factual FLAN files from `flan__...` to `flan_factual__...`, then use
`flan_factual__` prefix in the sampling config with `max_per_file: 100000` and
`repeat: 2`, while `flan__` stays at `max_per_file: 5000` for the rest.

## 2. Create prefix_config_dfm9.yaml
Copy `prefix_config_dfm8.yaml` and add:
```yaml
- prefix: flan_factual__
  max_per_file: 100000
  repeat: 2
- prefix: flan__
  max_per_file: 5000
```

The `flan_factual__` prefix must come before `flan__` so it matches first.

## 3. Build sampled data
```bash
cd /work/dfm/HRM-Text
python data_io/sample_tokenized.py \
  --tokenized-dir data/tokenized_dfm9 \
  --config data_io/prefix_config_dfm9.yaml \
  --output data/sampled_dfm9
```

## 4. Verify
Check `data/sampled_dfm9/metadata.json` for total tokens/epoch. Expected:
~70.5B + (11.18B - 0.93B) ≈ ~80.8B tokens/epoch (the factual FLAN increase
net of the existing 5K contribution).

## 5. Training
DFM9 training can resume from the DFM8 L epoch 3 checkpoint or start fresh.
Training config needs `data=dfm9` pointing to `data/sampled_dfm9`.
