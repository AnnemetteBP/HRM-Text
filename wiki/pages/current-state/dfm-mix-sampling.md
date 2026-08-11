---
type: Operational Record
title: DFM Mix Sampling
description: 'Part of Current State: DFM Mix Sampling.'
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
# DFM Mix Sampling

Part of [Current State](/pages/current-state.md).

Updated on 2026-05-28. Confidence: high.

The DFM mix was sampled successfully from `data/tokenized_mixed` into `data/sampled_dfm` using `data_io/sample_tokenized.py`. The manual sampler process finished after writing tokens, generating four epoch index directories, and generating the analytics report.

Command used from the repo root:

```bash
setsid bash -c 'cd /work/dfm/HRM-Text/data_io && ionice -c2 -n7 nice -n 10 python sample_tokenized.py tokenized_path=../data/tokenized_mixed output_path=../data/sampled_dfm epochs=4 concat_workers=4 prefix_config_path=prefix_config_dfm.yaml > ../data/show_analytics_dfm.md 2> ../logs/tokenize/dfm_sample_stderr.log' > logs/tokenize/dfm_sample_stdout.log 2>&1 &
```

Verified outputs:

- `data/sampled_dfm/tokens.npy`: about `630G`.
- `data/sampled_dfm/epoch_0` through `data/sampled_dfm/epoch_3`.
- `data/sampled_dfm/metadata.json`.
- `data/show_analytics_dfm.md`: analytics report.
- Metadata reports `total_length=28254014835`, `max_seq_len=4097`, and tokenizer path `/work/dfm/HRM-Text/data_io/trained_tokenizers/bpe/tokenizer.json`.
