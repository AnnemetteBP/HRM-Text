---
type: Plan Record
title: Prep And Tokenization Notes
description: 'Part of DFM7 Plan: Prep And Tokenization Notes.'
tags:
- dfm7
- data
- training
- evaluation
status: stable
last_updated: 2026-07-02
confidence: medium
part_of: /pages/dfm7-plan.md
---
# Prep And Tokenization Notes

Part of [DFM7 Plan](/pages/dfm7-plan.md).

DFM7 prep/tokenization behavior, 2026-06-30. Confidence: high from local script
inspection and successful local run.

- DFM7 uses the Python chat-template tokenizer path
  `scripts/tokenize_chat_template.py`, not the older Rust tokenizer. The script
  is appropriate for Gemma-4-template chat rendering and can run with
  `TOKENIZER_WORKERS=16`.
- `scripts/tokenize_chat_template.py` now prunes Parquet columns before
  tokenization. For chat/message datasets it reads only `messages` plus `tools`
  if present, and for HRM triplets it reads only
  `condition`/`instruction`/`response`. This avoids reading large unused
  provenance columns.
- Partially written tokenized output directories are removed before a file is
  reprocessed; `metadata.json` is still written last. A directory without
  matching metadata is therefore treated as incomplete and restarted.
- `dfm_dyna_instruct/data/apertus-sft-mixture/apertus-sft-mixture.parquet` is a
  pathological single input for this tokenizer: the full file is 9.35 GB with
  98 row groups and 3,942,208 rows. Its `messages` column is only about 110 MB,
  but its source-side `token_count` sums to about 2.30B tokens, so processing it
  as one file would accumulate a very large Python token list before writing.
- `scripts/shard_dfm7_large_parquets.py` shards that Apertus file by row group,
  writing 98 Parquet shards with only the `messages` column under
  `data/dfm7_special_sources/dfm_dyna_instruct_apertus_sft_mixture_shards`.
  The shard set is about 3.0 GB.
- `scripts/build_dfm7_chat_source_tree.py` excludes the monolithic Apertus file
  and links the shards under
  `data/dfm7_chat_sources/dfm_dyna_instruct/data/apertus-sft-mixture-shards`,
  preserving the `dfm_dyna_instruct__` sampling prefix and avoiding duplicate
  tokenization via the `dfm7_special_sources__` wrapper.
- Verified run: after sharding, 98 Apertus shards tokenized with 16 workers in
  688.2 seconds. The two largest shards (`part-0002`, `part-0003`) formed the
  tail and reached roughly 10-15 GB RSS each; this is acceptable on the current
  machine but is the main reason the original monolithic file should not be
  used.
- Superseded by the 2026-07-01 tool-use rebuild: the 2026-06-30 DFM7 sample
  reported `total_length=66,705,562,253`. The fixed canonical sample now
  reports `total_length=66,657,336,296` with 5 epochs, i.e. about 333.29B
  sampled token positions. The physical sampled directory is about 540G on the
  current filesystem.
- Absolute per-epoch token-count comparison from local sampled metadata:

  | Dataset | Sampled path | Tokens per epoch | Vs. original Sapient |
  | --- | --- | ---: | ---: |
  | Original Sapient | `data/sampled_original_sapient` | 14,035,178,678 | 1.00x |
  | DFM5 | `data/sampled_dfm5` | 35,605,979,095 | 2.54x |
  | DFM6 | `data/sampled_dfm6` | 62,819,933,768 | 4.48x |
  | DFM7 | `data/sampled_dfm7` | 66,657,336,296 | 4.75x |

- Per-epoch bucket comparison using mutually exclusive buckets
  `Danish`, `English/general`, and `Math/tool/code`, where
  `Math/tool/code` has precedence over Danish for Danish math/tool/code
  sources. Original Sapient, DFM5, and DFM7 are computed from saved sampling
  analytics. DFM6 is estimated from tokenized task lengths plus
  `data_io/prefix_config_dfm6.yaml` because no saved `show_analytics_dfm6.md`
  exists; the estimator's raw total matches `data/sampled_dfm6/metadata.json`
  after a negligible scale factor (`1.00000006`).

  | Dataset | Danish | English/general | Math/tool/code | Total |
  | --- | ---: | ---: | ---: | ---: |
  | Original Sapient | 0.00B | 9.70B | 4.34B | 14.04B |
  | DFM5 | 7.77B | 19.21B | 8.63B | 35.61B |
  | DFM6 | 19.71B | 21.31B | 21.80B | 62.82B |
  | DFM7 | 23.60B | 21.31B | 21.80B | 66.71B |

  Percentage view:

  | Dataset | Danish | English/general | Math/tool/code |
  | --- | ---: | ---: | ---: |
  | Original Sapient | 0.0% | 69.1% | 30.9% |
  | DFM5 | 21.8% | 53.9% | 24.2% |
  | DFM6 | 31.4% | 33.9% | 34.7% |
  | DFM7 | 35.4% | 31.9% | 32.7% |

- High-level sampled-token rollup across all 5 epochs:
  Danish/Danish-facing additions 118.09B tokens (23.62B/epoch, 35.41%),
  math/reasoning 76.40B (15.28B/epoch, 22.91%), general SFT/instruction
  65.52B (13.10B/epoch, 19.64%), inherited Sapient-style/synthetic 44.05B
  (8.81B/epoch, 13.21%), code/tool/agentic 21.42B (4.28B/epoch, 6.42%), and
  summarization 8.05B (1.61B/epoch, 2.41%).
- Zero-token categories in the 2026-06-30 sample:
  `danish_wildchat4_8m`, `ai_arena_udtraek`, `allenai_rlvr_gsm`,
  `allenai_rlvr_math`, `nemotron_swe`, and
  `synquid_wildchat_100k_qwen_messages`. `synquid_wildchat_100k_qwen_messages`
  is intentionally capped to zero in `prefix_config_dfm7.yaml`; the others
  need adapter/sampling review before relying on them.

Durable prep command from repo root:

```bash
TOKENIZER_WORKERS=16 bash scripts/prepare_dfm7_data.sh
```
| `danish-foundation-models/kaenguruen` | Danish math competition eval | Strong Danish math benchmark | Also included for DFM7 training by current policy decision. Keep eval metrics separate because training/eval overlap makes it non-held-out for DFM7. |
| `oliverkinch/da-bird` | Danish text-to-SQL / table QA | Adds structured reasoning/tool-adjacent SQL coverage | Treat as eval first; could later seed synthetic training data if no overlap with eval split. |
| `schneiderkamplab/danish-tool-calling-benchmark` | Danish/English tool-calling eval | Directly targets the current BFCL/tool-format gap | Existing DFM eval BFCL code can likely be reused/adapted; keep separate Danish and English metrics. |
| `schneiderkamplab/SDU-Daisy` | Danish domain QA | Small Danish cultural/domain QA probe | Because the split is named `train`, use as eval only if we agree it is benchmark-like and not part of training. |

Lower-priority eval/diagnostic candidates:

- `oliverkinch/danish-qa`: primarily a training candidate, but a held-out split
  could become a broad Danish factual QA eval if we create a deterministic
  train/eval split.
- `oliverkinch/synthetic-qa` and `oliverkinch/synthetic-qa-context-qa`: useful
  as QA smoke tests or held-out synthetic diagnostics, but less valuable than
  real Danish benchmarks unless the schemas reveal strong coverage.
- `schneiderkamplab/sapient-synth-platypus-scibench`: possible science
  reasoning diagnostic, but lower priority than GSM-Symbolic and standard
  science/math evals.

Implementation guidance:

- Add these under `dfm-evals/dfm_evals/tasks`, not `evaluation/benchmarks.py`,
  unless we intentionally want card-comparable standard evals.
- Register each task and add shard support up front for anything above a few
  hundred examples.
- Keep benchmark-like datasets in eval-only manifests so DFM7 training cannot
  accidentally sample them.
- Prefer stable metric names under `dfm_eval/<task>/<metric>/mean` and add
  headline-average membership only after a smoke run verifies scoring.
