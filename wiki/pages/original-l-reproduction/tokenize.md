---
type: Experiment Record
title: Tokenize
description: 'Part of Original L Reproduction: Tokenize.'
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
# Tokenize

Part of [Original L Reproduction](/pages/original-l-reproduction.md).

Command launched on 2026-05-21:

```bash
cd /work/dfm/HRM-Text/data_io/tokenizer
cargo run --release --bin tokenizer -- \
  /work/dfm/HRM-Text/data/downloads/datasets/sapient_cleaned/data_clustered \
  /work/dfm/HRM-Text/data/downloads/datasets/sapient_cleaned/data \
  --tokenizer-path /work/dfm/HRM-Text/data_io/trained_tokenizers/bpe/tokenizer.json \
  -o /work/dfm/HRM-Text/data/tokenized_original_sapient
```

Expected input files in the current download:

```text
5212 parquet/jsonl files
```

Verify completion:

```bash
find /work/dfm/HRM-Text/data/tokenized_original_sapient -name metadata.json | wc -l
du -sh /work/dfm/HRM-Text/data/tokenized_original_sapient
```

Expected metadata count is `5212`.
