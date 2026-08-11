---
type: Policy Record
title: DFM Mix
description: 'Part of Data Mix Policy: DFM Mix.'
tags:
- data
- licensing
- provenance
- privacy
status: stable
last_updated: 2026-06-17
confidence: high
part_of: /pages/data-mix-policy.md
---
# DFM Mix

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Decision on 2026-05-27. Confidence: high for local schema/access checks and
manifest/config edits; medium for the exact caps until sampled analytics are
measured.

The DFM mix is the next mixed-corpus target:

- Name: `dfm`
- Sampling config: `data_io/prefix_config_dfm.yaml`
- Intended output: `data/sampled_dfm`
- Training data config: `config/data/dfm.yaml`
- Target size: about 28B tokens per epoch
- Content: safe filtered Sapient sources plus all approved additional sources,
  including gated Danish instruction sources where access is available.

`synquid/wildchat-100k-qwen` is superseded by
`synquid/wildchat-100k-qwen-messages`. The messages variant was row-accessible
with an explicit HF token on 2026-05-27 and uses a `messages` JSONL schema that
the existing converter supports. It is included only with a tight
`50,000`-row cap per file. `oliverkinch/instruct-bt` was also row-accessible on
2026-05-27 and uses a `messages` Parquet schema supported by the existing
converter.
