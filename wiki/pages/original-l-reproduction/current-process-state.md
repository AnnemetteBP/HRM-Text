---
type: Experiment Record
title: Current Process State
description: 'Part of Original L Reproduction: Current Process State.'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction.md
---
# Current Process State

Part of [Original L Reproduction](/pages/original-l-reproduction.md).

As of 2026-05-26 in the MPS checkout, original Sapient tokenization and sampling completed locally:

```text
Tokenized path: data/tokenized_original_sapient
Tokenized metadata files: 5212 / 5212
Tokenized size: 681G

Sampled path: data/sampled_original_sapient
Sampled size: 669G
Analytics: data/show_analytics_original_sapient.md
```

`data/sampled_original_sapient/metadata.json` reports `max_seq_len=4097` and `total_length=14,035,178,678` tokens per epoch. The four generated epoch directories therefore cover about `56,140,714,712` sampled tokens total, matching the previously recorded original Sapient reference total to rounding. The sampler emitted known prefix-overlap warnings for `flan__cot_*` tasks and then completed successfully. Confidence: high.

A full-distribution smoke dataset was derived from `data/sampled_original_sapient` on 2026-05-26:

```text
Path: data/sampled_original_sapient_smoke2
Target tokens across 4 epochs: 56,000,000
Actual tokens across 4 epochs: 56,001,530
metadata.total_length: 14,000,382
On-disk size: 6.5M plus a symlinked tokens.npy
tokens.npy -> ../sampled_original_sapient/tokens.npy
```

It was created by `scripts/create_smoke_from_sampled.py`, taking prefixes from the already shuffled full sampled epoch indices, so it preserves the full sampled dataset distribution in expectation without re-sampling from tokenized shards. `V1Dataset` successfully loaded a batch from this dataset. Confidence: high.

The mixed-corpus tokenizer is a separate process writing to `data/tokenized_mixed`; it should not be used for the L reproduction run.
