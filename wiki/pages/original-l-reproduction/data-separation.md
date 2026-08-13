---
type: Experiment Record
title: Data Separation
description: 'Part of Original L Reproduction: Data Separation.'
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
# Data Separation

Part of [Original L Reproduction](/pages/original-l-reproduction.md).

Keep this run separate from the filtered mixed corpus:

```text
Mixed corpus downloads:          data/downloads/datasets/*
Mixed corpus filter tree:        data/filtered_sources
Mixed corpus converted path:     data/converted_sources
Mixed corpus tokenized path:     data/tokenized_mixed
Mixed corpus sampled path:       data/sampled
Mixed corpus data config:        config/data/hlm.yaml

Original Sapient source roots:   data/downloads/datasets/sapient_cleaned/data_clustered
                                 data/downloads/datasets/sapient_cleaned/data
Original Sapient tokenized path: data/tokenized_original_sapient
Original Sapient sampled path:   data/sampled_original_sapient
Original Sapient data config:    config/data/original_sapient.yaml

Original plus mixed tokenized:   data/tokenized_original_plus_mixed
Original plus mixed sampled:     data/sampled_original_plus_mixed
Original plus mixed data config: config/data/original_plus_mixed.yaml
```

The original reproduction should not use `data/filtered_sources` or `data/converted_sources`, because those reflect our safer mixed-corpus policy and rewritten path prefixes. It should tokenize the original Sapient roots directly so `data_io/prefix_config.yaml` matches names like `openmathinstruct2__...`, `flan__...`, `tasksource__...`, and `Platypus__...`.

Do not overwrite `config/data/hlm.yaml` for the reproduction run. Keep `hlm.yaml` pointed at the mixed-corpus default `data/sampled`, and use `data=original_sapient` or `data.path=data/sampled_original_sapient` for the reproduction run.

The dedicated original data config is:

```yaml
path: data/sampled_original_sapient
target_only: true
```

The third `original ∪ mixed` dataset is intentionally separate from both. It uses a symlinked tokenized view of all original Sapient tasks plus non-Sapient mixed tasks. Mixed `sapient_cleaned__*` tokenized tasks are skipped because they are already represented in the full original Sapient tokenization under original-compatible task names.

Status, 2026-05-23: the `original ∪ mixed` tokenized view was rebuilt after mixed tokenization added more outputs. It now links `5,212` original Sapient task directories plus `226` non-Sapient mixed task directories and skips `1,139` mixed `sapient_cleaned__*` task directories. Sampling with `epochs=4` and `concat_workers=4` completed into `data/sampled_original_plus_mixed`; `metadata.json` reports `max_seq_len=4097`, `total_length=46,825,293,021`, and each epoch index has `111,058,569` rows. `data/show_analytics_original_plus_mixed.md` reports `73,008,641,849` unique sampled tokens out of `216,160,760,173` total tokenized tokens. Confidence: high.
