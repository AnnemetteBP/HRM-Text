---
type: Software Reference
title: '`data_io/sample_tokenized.py`'
description: 'Part of Script Entities: `data_io/sample_tokenized.py`.'
tags:
- scripts
- software
- catalog
- operations
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# `data_io/sample_tokenized.py`

Part of [Script Entities](/entities/scripts.md).

Samples tokenized task directories into HRM training data.

Local note, 2026-05-23: `concat_workers` is now a CLI config field. Use it to throttle the initial `tokens.npy` concatenation copy phase on shared storage, for example:

```bash
cd /work/dfm/HRM-Text/data_io
ionice -c2 -n7 nice -n 10 python sample_tokenized.py \
  tokenized_path=../data/tokenized_original_plus_mixed \
  output_path=../data/sampled_original_plus_mixed \
  epochs=4 \
  concat_workers=4 \
  > ../data/show_analytics_original_plus_mixed.md
```
