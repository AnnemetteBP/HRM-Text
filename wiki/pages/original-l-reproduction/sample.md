---
type: Experiment Record
title: Sample
description: 'Part of Original L Reproduction: Sample.'
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
# Sample

Part of [Original L Reproduction](/pages/original-l-reproduction.md).

After tokenization completes, sample with the original `data_io/prefix_config.yaml`:

```bash
cd /work/dfm/HRM-Text/data_io
python sample_tokenized.py \
  tokenized_path=../data/tokenized_original_sapient \
  output_path=../data/sampled_original_sapient \
  epochs=4 \
  > ../data/show_analytics_original_sapient.md
```
