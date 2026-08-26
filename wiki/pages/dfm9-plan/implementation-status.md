---
type: Plan Record
title: Implementation Status
description: 'Part of DFM9 Plan: Implementation Status.'
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
# Implementation Status

Part of [DFM9 Plan](/pages/dfm9-plan.md).

Update, 2026-08-07. Confidence: high from local file creation and process
inspection.

## Completed
1. **`data/tokenized_dfm9/`**: created with 10,722 symlinked entries from
   `tokenized_dfm8/` (later expanded to 11,413 with new sources, SWE windowed,
   and extension sources). 266 factual-knowledge FLAN files renamed from `flan__`
   to `flan_factual__` (includes main FLAN variants and niv2 task variants
   for TriviaQA, SQuAD, NQ, HotpotQA/KILT, WebQuestions, RACE, DROP, CoQA,
   QuAC, ROPES, WikiDialog, DREAM, BoolQ). Remaining 3,608 non-factual FLAN
   files kept as `flan__`. 6,848 non-FLAN entries symlinked as-is.

   Per-dataset factual file counts: bool=8, coqa=8, dream=28, drop=10,
   hotpot/kilt=28, natural_questions=4, quac=4, race=72, ropes=54,
   squad=16, trivia=8, web_questions=22, wiki_dialog=4. Total=266.

2. **`data_io/prefix_config_dfm9.yaml`**: created with 109 prefix entries
   (DFM8 had 108 + 1 new `flan_factual__` entry). Key change:
   ```yaml
   - prefix: flan_factual__
     max_per_file: 100000
     repeat: 2
   - prefix: flan__cot_        # unchanged, no cap
   - prefix: flan__             # unchanged, 5K cap
     max_per_file: 5000
   ```
   The `flan_factual__` prefix is placed before `flan__cot_` and `flan__`
   so it matches first.

3. **Sampling launched** in background (PID 1091371):
   ```bash
   cd data_io && ionice -c2 -n7 nice -n 10 python sample_tokenized.py \
     tokenized_path=../data/tokenized_dfm9 \
     output_path=../data/sampled_dfm9 \
     epochs=5 concat_workers=4 \
     prefix_config_path=prefix_config_dfm9.yaml \
     > ../data/show_analytics_dfm9.md 2> ../logs/tokenize/dfm9_sample_stderr.log
   ```
   Note: `reuse_tokens=true` is NOT safe because renaming `flan__` to
   `flan_factual__` changes the sorted task order, which changes per-task
   `mmap_base_offset` values in the combined `tokens.npy`.

## Sampling Complete
Update, 2026-08-07. Confidence: high from `metadata.json` and analytics report
output.

```text
metadata.json total_length: 79,938,703,078  (~79.94B tokens/epoch)
DFM8 was:                  70,479,433,697  (~70.48B tokens/epoch)
Increase:                   9,459,269,381  (~9.46B, +13.4%)
```

Factual FLAN category (`flan_factual`) in the analytics report:
- Total rows: 16,495,724 (3.5% of all rows)
- Total tokens: 9,603,096,705 (7.5% of all tokens)
- Covered rows over 5 epochs: 82,911,760 (7.1%)
- Covered tokens over 5 epochs: 50,997,831,112 (12.8%) = ~10.2B/epoch

Non-factual FLAN category (`flan`) remains at 5K cap:
- Covered tokens over 5 epochs: 21,639,449,658 (5.4%) = ~4.3B/epoch

The ~9.46B increase is slightly less than the projected ~10.25B because the
tokenized tree has 266 factual FLAN files (vs 514 in the source parquet
analysis). The actual token increase is proportional to the available
tokenized files.

Verified output:
```text
data/sampled_dfm9/
├── epoch_0/
├── epoch_1/
├── epoch_2/
├── epoch_3/
├── epoch_4/
├── metadata.json
└── tokens.npy
```
