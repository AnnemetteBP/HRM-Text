---
type: Operational Record
title: Mixed Corpus Next Commands
description: 'Part of Current State: Mixed Corpus Next Commands.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# Mixed Corpus Next Commands

Part of [Current State](/pages/current-state.md).

Convert filtered sources:

```bash
cd /work/dfm/HRM-Text
python scripts/convert_filtered_sources.py --force --copy-ready --workers 32
```

Tokenize converted sources:

```bash
cd /work/dfm/HRM-Text/data_io/tokenizer
cargo run --release --bin tokenizer -- \
  /work/dfm/HRM-Text/data/converted_sources \
  --tokenizer-path /work/dfm/HRM-Text/data_io/trained_tokenizers/bpe/tokenizer.json \
  -o /work/dfm/HRM-Text/data/tokenized_mixed
```

Sample tokenized data:

```bash
cd /work/dfm/HRM-Text/data_io
python sample_tokenized.py \
  tokenized_path=../data/tokenized_mixed \
  output_path=../data/sampled \
  epochs=4 \
  > ../data/show_analytics.md
```
