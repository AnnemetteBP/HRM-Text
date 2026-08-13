---
type: Policy Record
title: Mixed English/Danish Filtered 2x-Original Cap
description: 'Part of Data Mix Policy: Mixed English/Danish Filtered 2x-Original Cap.'
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
# Mixed English/Danish Filtered 2x-Original Cap

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Verified/created locally on 2026-05-24.

The first mixed-only filtered sample used `data_io/prefix_config.yaml` against `data/tokenized_mixed` and produced a very large corpus:

- Output: `data/sampled_mixed_english_danish_filtered`
- Analytics: `data/show_analytics_mixed_english_danish_filtered.md`
- Per-epoch `metadata.total_length`: `70,644,435,216` tokens
- 4-epoch covered tokens: `282,577,740,862`

Cause: `data/tokenized_mixed` task names include source prefixes such as `sapient_cleaned__data_clustered__SYNTH__...`, but the shared `data_io/prefix_config.yaml` uses unprefixed Sapient rules such as `SYNTH__`, `flan__`, and `dmmath__`. Those rules therefore did not match the filtered Sapient tasks in the mixed-only tokenized tree, causing most filtered Sapient files to be sampled uncapped.

A dedicated capped config was added:

```text
data_io/prefix_config_mixed_2x_original.yaml
```

Target ceiling:

- Original Sapient sample: `56,140,714,711` covered tokens over 4 epochs.
- Original per-epoch size: `14,035,178,677.75` tokens.
- 2x ceiling: `28,070,357,355.5` tokens per epoch.

Dry-run estimate after applying the new config with PrefixLM truncation/filtering:

- Estimated per-epoch sampled tokens: `24,630,898,966`
- Ratio to original per-epoch size: `1.755x`
- This is below the `2x` ceiling.

Final completed sample:

- Output: `data/sampled_mixed_english_danish_filtered_2x_original`
- Analytics: `data/show_analytics_mixed_english_danish_filtered_2x_original.md`
- Hydra config: `config/data/mixed_english_danish_filtered_2x_original.yaml`
- `metadata.total_length`: `24,630,436,020` tokens per epoch
- 4-epoch covered tokens: `98,521,744,082`
- Ratio to original per-epoch size: `1.755x`
- Unique sampled tokens: `55,258,504,135 / 78,082,414,846` (`70.77%`)
- Directory size: about `625G`

Note: `sample_tokenized.py` copies the full token bank into output `tokens.npy` before writing capped epoch indices, so the disk footprint remains large even though the epoch index budget is capped.

Estimated largest per-epoch category shares:

| Category | Estimated tokens/epoch | Share |
|---|---:|---:|
| `sapient_cleaned` | `8,129,060,084` | `33.0%` |
| `danish_dynaword` | `3,093,170,660` | `12.6%` |
| `nemotron_multilingual` | `3,001,252,991` | `12.2%` |
| `allenai_big_reasoning_traces` | `1,624,580,477` | `6.6%` |
| `dolci_instruct_sft` | `1,380,220,345` | `5.6%` |
| `dolci_instruct_sft_no_tools` | `962,106,919` | `3.9%` |
| `allenai_tulu_v2_sft_mixture` | `902,702,844` | `3.7%` |
| `allenai_tulu_3_sft_mixture` | `831,587,284` | `3.4%` |

Sampling was launched in tmux:

```bash
cd /work/dfm/HRM-Text/data_io
/home/ucloud/miniforge3/envs/hrm/bin/python sample_tokenized.py \
  tokenized_path=../data/tokenized_mixed \
  output_path=../data/sampled_mixed_english_danish_filtered_2x_original \
  prefix_config_path=prefix_config_mixed_2x_original.yaml \
  epochs=4 \
  concat_workers=4 \
  > ../data/show_analytics_mixed_english_danish_filtered_2x_original.md \
  2> ../logs/sample_mixed_english_danish_filtered_2x_original.err
```

Session:

```bash
tmux attach -t hrm_sample_mixed_2x_original
```

Confidence: high.
