---
type: Operational Record
title: Data State
description: 'Part of Current State: Data State.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-27
confidence: high
part_of: /pages/current-state.md
---
# Data State

Part of [Current State](/pages/current-state.md).

Update on 2026-05-31:

- DFM3 data-prep scaffolding was added for English evaluation recovery. DFM3
  is DFM2 plus selected Common Pile raw-text objectives and raised caps for
  approved English/multilingual instruction data.
- New files:
  - `scripts/generate_dfm3_common_pile_tasks.py`
  - `scripts/build_tokenized_dfm3_tree.py`
  - `scripts/prepare_dfm3_english_recovery.sh`
  - `data_io/prefix_config_dfm3.yaml`
  - `config/data/dfm3.yaml`
- `scripts/download_training_datasets.py` now has an explicit `common_pile`
  group with selected filtered/public/open Common Pile components. A dry-run
  inventory resolved `480` selected files and `275.1 GB` compressed/download
  size.
- `scripts/convert_filtered_sources.py` now converts selected Common Pile
  `.json.gz`, `.jsonl.gz`, and Parquet rows with a `text` field into raw
  continuation rows.
- Validation passed:
  - `python -m py_compile` for modified/new Python scripts.
  - `bash -n scripts/prepare_dfm3_english_recovery.sh`.
  - `data_io/prefix_config_dfm3.yaml` parses as YAML with `84` rules.
- Later on 2026-05-31, the selected Common Pile download/filter/convert
  stages completed and DFM3 task generation finished. The generator wrote
  `2,862` Parquet task files under
  `data/converted_sources_dfm3_common_pile_tasks`, with approximately
  `19,043,38x` rows in each of the six DFM3 objective families:
  direct continuation, prefix continuation, denoising, and three span-fill
  variants. Confidence: high.
- DFM3 Common Pile tokenization was launched with one worker:

```bash
ionice -c2 -n7 nice -n 10 ./data_io/tokenizer/target/release/tokenizer \
  data/converted_sources_dfm3_common_pile_tasks \
  --tokenizer-path /work/dfm/HRM-Text/data_io/trained_tokenizers/bpe/tokenizer.json \
  --workers 1 \
  -o data/tokenized_dfm3_common_pile_tasks
```

  At `2026-05-31 12:07 CEST`, the reliable progress signal was `484 / 2862`
  completed tokenized task directories, measured by top-level output dirs or
  `metadata.json` files, and about `100G` written. Do not estimate tokenizer
  completion from raw file count under the output tree, because each completed
  tokenized task directory contains multiple array files. Confidence: high.

Update on 2026-06-01:

- DFM3 Common Pile tokenization completed: `2862 / 2862` generated task dirs
  have `metadata.json`, matching the `2862` generated Parquet inputs.
  `data/tokenized_dfm3_common_pile_tasks` is `448G`. Confidence: high.
- The DFM3 tokenized union was built at `data/tokenized_dfm3` with `4690`
  top-level symlinks. Confidence: high.
- DFM3 sampling completed at `data/sampled_dfm3`; it contains `metadata.json`
  and `tokens.npy` and is `1.2T`. `data/sampled_dfm3/metadata.json` reports
  `max_seq_len=4097` and `total_length=174,204,067,350`. The analytics file
  `data/show_analytics_dfm3.md` reports `192,508,795,135` unique sampled tokens
  out of `214,239,617,633` available unique tokens (`89.86%`). Confidence: high.
- DFM4 source downloads completed. No DFM4 downloader process remains. Local
  sizes are `436M` for `govreport_summarization`, `5.5G` for `wiki_cat_sum`,
  and `143G` for `laion_scientific_summaries`. The selected LAION arXiv slice
  has `4006` Parquet files plus selected repository docs, matching the `4008`
  selected-file inventory. GovReport has `2` train Parquet shards plus README;
  WikiCatSum has `3` train JSONL files plus README. Confidence: high.
- Superseded: the first DFM4 sample used four epochs and the original
  paragraph-reorder tokenization.
- Current DFM4 generation, tokenization, union build, and five-epoch sampling
  completed. The current union keeps the full DFM3 tree, regenerated DynaWord
  paragraph-window tasks, the previously complete Common Pile paragraph tasks,
  and DFM4 summarization tasks. `data/tokenized_dfm4/union_manifest.json`
  reports roots of `4689` DFM3 tasks, `25` regenerated DynaWord paragraph
  tasks, `425` Common Pile paragraph tasks, `4019` summarization tasks, and
  `9158` total tasks. Confidence: high.
- Current DFM4 sampling completed at `data/sampled_dfm4` with `epochs=5`.
  `metadata.json` reports `max_seq_len=4097` and
  `total_length=72,007,089,569` tokens per epoch. `tokens.npy` is
  `1,225,441,020,536` bytes. Per-epoch arrays exist under `epoch_0` through
  `epoch_4`; all epoch array files were rewritten at `20:32-20:33 CEST` on
  2026-06-01. `data/show_analytics_dfm4.md` reports
  `360,035,447,845` covered tokens across five epochs. Confidence: high.
- Superseded: before pulling `origin/main` on 2026-06-02, the local
  `global_batch_size` path had no gradient accumulation.
- Pull/merge update on 2026-06-02. Confidence: high. `main` was
  fast-forwarded to `origin/main` after a dry run in
  `/work/dfm/HRM-Text-pull-sim`. Local tracked changes were stashed,
  reapplied, and conflicts were resolved using the same resolutions as the temp
  worktree. Conflicted files were `config/cfg_pretrain.yaml`, `pretrain.py`,
  `wiki/pages/download-convert-tokenize.md`, and `wiki/pages/open-issues.md`.
  Validation passed with `python scripts/check_goldfish_loss.py`,
  `python -m py_compile pretrain.py models/lm_head.py models/goldfish_loss.py
  scripts/check_goldfish_loss.py`, and `git diff --check`.
- Current batch-size implementation after the pull, verified from
  `pretrain.py`, `dataset_new.py`, and `multipack_sampler.py` on 2026-06-02.
  Confidence: high. `global_batch_size` is now the effective optimizer token
  batch and `gradient_accumulation_steps` controls the physical microbatch:
  `local_batch_size = global_batch_size / (world_size *
  gradient_accumulation_steps)`. Each optimizer step accumulates that many
  microbatches before `optim.step()`, with loss scaled by supervised-token
  counts across the accumulated microbatches.

Update on 2026-05-30:

- DFM2 data preparation completed. `scripts/generate_dfm2_dynaword_tasks.py`
  produced DynaWord-derived self-supervised tasks, tokenized with one tokenizer
  worker into `data/tokenized_dfm2_dynaword_tasks`.
- `scripts/build_tokenized_dfm2_tree.py --force` built `data/tokenized_dfm2`
  as a symlink union with `1377` base mixed tasks plus `450` generated DFM2
  tasks, for `1827` total task dirs.
- DFM2 sampling completed at `data/sampled_dfm2`; `config/data/dfm2.yaml`
  points training at this sample.
- `data/sampled_dfm2/metadata.json` reports `total_length=42,317,252,803`
  tokens per epoch and `max_seq_len=4097`.
- `data/show_analytics_dfm2.md` reports generated DynaWord self-supervised
  additions of `56,253,792,196` covered tokens across four epochs, or
  `14,063,448,049` per epoch. The retained direct DynaWord slice is
  `2,813,942,923` covered tokens per epoch, so the generated additions are
  `4.998X`.
- DFM2 generated tasks do not use sampler `repeat: 2`; the generator creates
  unique variants instead.

Update on 2026-05-27:

- New DFM gated additions downloaded and converted:
  `laerebogen_with_followups`, `synquid_wiki_instruct_da`,
  `oliverkinch_instruct_bt`, `synquid_mt_da_deepseek`, and
  `synquid_wildchat_100k_qwen_messages`.
- `data_io/prefix_config_dfm.yaml` defines the DFM sampling policy and
  `config/data/dfm.yaml` points training at `data/sampled_dfm`.
- A subset tokenizer run against `data/converted_sources_dfm_new` pruned
  existing `data/tokenized_mixed` outputs because the Rust tokenizer removes
  output directories not present in its current input root. Recovery was started
  by running the tokenizer against the full `data/converted_sources` tree with
  one low-priority worker. A watcher will sample `data/sampled_dfm` only after
  the tokenizer log reports `Done.`.

Superseded context from earlier sessions:

- `data_io` is cloned under `/work/dfm/HRM-Text/data_io`.
- Downloads were run with:

```bash
python scripts/download_training_datasets.py --groups all --exclude-gated --download
```

- Because `--exclude-gated` was used, gated sources such as Laerebogen, Wiki Instruct DA, Instruct BT, and gated Synquid WildChat variants are not part of that run.
- `data/filtered_sources` was built with:

```bash
python scripts/build_filtered_source_tree.py --force
```

- The user reported the final filtered tree build:

```text
Allowed files:      1,525
Denied files:       4,073
Allowed bytes:      248,502,793,134
```

## 2026-08-27 Storage duplication audit

`data/` occupies approximately `32,741 GiB`. No large duplicate payloads found
by the audit are hard-linked, so each copy consumes storage. Conservative
sampled-region signatures (five 8 MiB regions spanning each file) identified
the following same-size, same-content candidates; run a complete `cmp` or hash
before replacing either copy:

- `sampled_original_plus_mixed/tokens.npy` and
  `sampled_original_plus_mixed_danish_instruction_rich/tokens.npy`: one
  duplicated `1,136.3 GiB` token pool. Their metadata and epoch selections are
  different, so only `tokens.npy` is shareable.
- `sampled_mixed_english_danish_filtered/tokens.npy` and its
  `2x_original` counterpart: one duplicated `618.1 GiB` token pool; indices and
  metadata differ.
- The Nemotron SWE tokenized directory under both
  `tokenized_dfm6_swe_shards` and `tokenized_dfm6_direct_jinja`: seven files
  with identical relative names/sizes and matching sampled token signatures,
  approximately `315 GiB` per copy.
- `1,132` flattened Sapient task directories occur in both `tokenized_mixed`
  and `tokenized_original_sapient`, with identical relative file shapes/sizes;
  the mixed-side copies total about `151 GiB`.
- `1,394` files under `downloads/datasets` and `converted_sources` have the
  same relative path and size, totaling about `66 GiB`; sampled checks of the
  largest Parquet file matched.
- `converted_sources/nemotron_swe/data/swe.parquet.unsplit` duplicates the
  retained `swe.parquet` payload, approximately `2.3 GiB`.

These candidates provide about `2.3 TiB` of literal-copy savings after full
verification. Separately,
`sampled_dfm6_before_superset_fix_20260620_133752` is a superseded `784 GiB`
snapshot; removing or archiving it would raise the clear avoidable total to
about `3.1 TiB`. Older sampled DFM generations and separate 8K/16K/32K
materializations account for many additional TiB but are historical or
context-specific artifacts, not byte-identical duplicates. The current sampler
materializes a monolithic `tokens.npy` in every output, so overlapping corpus
versions cannot generally share storage without symlinking/reflinking verified
immutable token pools or redesigning the format around content-addressed token
stores.
