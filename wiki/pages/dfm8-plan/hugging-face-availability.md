---
type: Plan Record
title: Hugging Face Availability
description: 'Part of DFM8 Plan: Hugging Face Availability.'
tags:
- dfm8
- data
- synthetic-data
- training
- evaluation
status: stable
last_updated: 2026-07-12
confidence: medium
part_of: /pages/dfm8-plan.md
---
# Hugging Face Availability

Part of [DFM8 Plan](/pages/dfm8-plan.md).

Update, 2026-07-13. Confidence: high for DFM8-specific source status from local
config/wiki inspection; medium for inherited DFM7 full-manifest status.

Aside from the still-running OpenHermes repair/translation outputs, the
DFM8-specific additions are available from Hugging Face:

- `giannor/dala_tv2r_it`, `giannor/gec_dala_tv2r_it`, and
  `kobprof/skolegpt-instruct` are upstream HF datasets downloaded by
  `scripts/download_training_datasets.py --groups dfm8 --download`.
- The eight broad transform-expansion datasets are uploaded under
  `schneiderkamplab/{common-pile,danish-dynaword}-*`.
- The four older `transformations-*` datasets are uploaded under
  `schneiderkamplab/transformations-*`.
- The six targeted synthetic DFM8 datasets are uploaded under
  `schneiderkamplab/dfm8-synthetic-*`.

The final DFM8 OpenHermes inputs are intentionally not the raw
`teknium/OpenHermes-2.5` conversion. `data_io/prefix_config_dfm8.yaml` expects
`dfm8-openhermes-en` and `dfm8-openhermes-da`, which will be produced by the
active repaired OpenHermes pipeline and uploaded from
`export-upload-dfm8-openhermes-repaired`.

Caveat: the local DFM8 build currently reuses inherited DFM7 tokenized/source
trees (`data/tokenized_dfm7` and related converted/export artifacts). Many of
those inherited sources are HF upstream datasets or previously uploaded
`schneiderkamplab` exports, but the whole inherited corpus is not yet expressed
as one clean HF-only DFM8 download manifest. If DFM8 must be rebuildable from
scratch on another machine, add a manifest/audit step that maps every inherited
DFM7 prefix in `data_io/prefix_config_dfm8.yaml` to either an upstream HF repo
or a `schneiderkamplab` export repo.

Follow-up, 2026-07-13. Confidence: high from local manifest inspection and
`huggingface_hub` repo checks. For a full DFM8 rebuild from scratch, the answer
was not yet "all sources are available from HF" until we upload or otherwise
publish the locally staged Danish sources:

- `dbc` (`dbc-abstracts_*.jsonl.gz`, `dbc-reviews.jsonl.gz`,
  `dbc-faktalink.jsonl.gz`, `dbc-farfatterweb.jsonl.gz`)
- `lexdk` (`lexdk_articles.jsonl.gz`)
- `opus` (`opus_da_en.jsonl.gz`) - superseded by upload note below

These are present under `data/downloads/datasets/{dbc,lexdk,opus}` and are
sampled via the inherited DFM8 prefixes `dbc__*`, `lexdk__`, and `opus__`.
They are not in `scripts/download_training_datasets.py` as HF datasets, and
obvious public `schneiderkamplab/{dbc,lexdk,opus,dbc-danish,lexdk-articles,opus-da-en}`
repos did not resolve during the check. All obvious large inherited families
otherwise map to upstream HF datasets in the downloader or to previously
uploaded `schneiderkamplab` exports (`sapient-synth-*`, broad transforms, and
DFM8 synthetic outputs). A strict HF-only rebuild therefore needs at least these
three local Danish source groups uploaded or deliberately excluded/replaced.

Upload update, 2026-07-13. Confidence: high from successful uploader exit and
Hub-side repo inspection. The `opus` rebuild gap is closed:

- HF dataset: `schneiderkamplab/opus-da-en-permissive`
- Commit: `67d62cf28a6bbe5e17d208776e49b95d808cc9df`
- Public: yes
- Files: `README.md`, `data/opus_da_en.jsonl.gz`
- Local package: `export-upload-local/opus-da-en-permissive`
- Upload log:
  `logs/hf_upload_opus_da_en_permissive_20260713T062000.log`
- Downloader manifest: `scripts/download_training_datasets.py` now contains
  an HF entry named `opus`, so `python scripts/download_training_datasets.py
  --only opus --download` restores the expected local root
  `data/downloads/datasets/opus`.

After this upload, the remaining known local-only DFM8 rebuild gaps are `dbc`
and `lexdk`, pending separate upload or an explicit replacement/exclusion
decision.

Dataset inventory update, 2026-07-31. Confidence: high from the sampled epoch
indices, `data/show_analytics_dfm8.md`, and the local download manifest. A
human-readable inventory of every nonzero DFM8 source, its HF repository (where
applicable), and its sampled per-epoch token contribution is maintained in
[`docs/dfm8-datasets.md`](../../../docs/dfm8-datasets.md). DBC and LexDK are listed
separately there as non-HF datasets supplied through Danish Foundation Model
agreements. The six-epoch analytics sum to 70.479B tokens per epoch and agree
with direct epoch-index length sums to normal sampling variation.

Inventory refinement, 2026-07-31. Confidence: high from the DFM8 prefix
specification, category/task analytics, tokenized source links, and converter
source code. The inventory is exhaustive at HF-repository granularity: 159
distinct HF dataset IDs have one row each, while DBC and LexDK occupy two
separate agreement-supplied rows. Combined analytics categories for Giannor
TV2R and corrected Dolci tool use are split using task-level coverage rather
than estimated proportions. `acereason` is correctly attributed to
`nvidia/AceReason-1.1-SFT`.

Repair runner scheduling fix, 2026-07-13. Confidence: high from script
inspection and `bash -n`. `dfm8_openhermes_repaired/scripts/run_openhermes_repair_8gpu.sh`
previously used a FIFO wait pattern in `run_shards`: after launching one shard
per GPU, it waited for the oldest PID before launching any later shard. This
caused head-of-line blocking in tail phases: if one shard was slow or wedged,
free GPUs were not assigned later shards. The loop now uses `wait -n` with an
active-worker counter, so each completed child immediately frees one scheduler
slot and the next shard starts without waiting for older still-running shards.
This affects future stages/runs, not already-running child processes from a
script instance that was started before the patch.

DaOH retry shadowing fix, 2026-07-13. Confidence: high from local code
inspection and `py_compile`. The DaOH retry phase should not spend GPU time
retrying old Danish OpenHermes translation failures when the same `source_row_id`
already has an accepted repaired Danish translation from the English
OpenHermes-repair path. `cmd_make_daoh_retry_requests` now loads
`danish_repaired` plus `danish_repair_audits`, computes accepted repaired
source IDs, and skips DaOH retry candidates shadowed by those accepted repairs.
The final `build-upload` path already removed shadowed retry/base rows, but this
change avoids unnecessary retry translation/audit work up front and reports
`skipped_shadowed_by_accepted_repair`.

Importance estimate, 2026-07-13. Confidence: high for counts from
`data/show_analytics_dfm7.md`, `data/show_tokenized_dfm8.md`, and local `du`.
The three local-only source groups are not just bookkeeping noise, but their
importance differs:

| Source group | DFM8 tokenized source tokens | DFM7 sampled tokens, five epochs | Local raw size | Importance |
| --- | ---: | ---: | ---: | --- |
| `opus` | about 5.665B | about 14.518B | 2.4G | Largest of the three; mostly Danish-English translation. Useful, but partly replaceable by other Danish translation sources. |
| `dbc` | about 1.607B | about 1.781B | 2.2G | Medium-sized and more unique Danish cultural/library/book/article instruction material. |
| `lexdk` | about 66M | about 1.567B | 70M | Small source inventory but heavily repeated; high-quality Danish encyclopedic style. |

Together these accounted for about 17.87B sampled tokens over the five-epoch
DFM7 sample, or about 3.57B tokens/epoch. In DFM8 their percentage will likely
be somewhat lower after the OpenHermes and DFM8 synthetic additions, but the
absolute sampling policy still makes them meaningful. For a faithful DFM8
rebuild, upload all three rather than silently dropping them. If one must be
removed, `opus` is the most replaceable by content type; `dbc` and `lexdk` are
more distinctive Danish-domain sources.

Repaired OpenHermes completion, 2026-07-14. Confidence: high from local
pipeline counters and the final tmux build summary. The repaired OpenHermes
pipeline completed all GPU stages and built upload-ready folders under
`export-upload-dfm8-openhermes-repaired`:

- English output: `export-upload-dfm8-openhermes-repaired/dfm8-openhermes-en`
  with `918,095` rows.
- Merged Danish output:
  `export-upload-dfm8-openhermes-repaired/dfm8-openhermes-da` with `967,334`
  rows.
- English audit summary: `1,001,551` source-audit rows, `460,695` accepted
  clean rows, `457,400` accepted repaired rows, and `457,400` clean rows
  shadowed by repair.
- Base Danish OpenHermes summary: `1,001,551` generated rows, `991,114` audit
  rows, `924,816` accepted rows.
- Danish repaired additions: `429,353` accepted repaired rows, `3,220`
  accepted retry rows, `432,573` accepted added rows, and `390,055` regular
  DaOH rows replaced by repaired rows.
- Retry materialization counters: `7,032` DaOH retry translation rows and
  `5,729` DaOH retry audit rows were written.

This supersedes the earlier instruction to wait for the repaired OpenHermes
pipeline before final DFM8 sampling. The remaining step is uploading these two
upload-ready HF dataset folders and then integrating/tokenizing them in the
DFM8 source tree.

Upload update, 2026-07-14. Confidence: high from successful upload command and
Hub API verification. The repaired OpenHermes datasets are now public on
Hugging Face:

- `schneiderkamplab/dfm8-openhermes-en`, commit
  `157a1488d453aef9e827bddabc77d78c0bfd57ef`, 10 `data/*.jsonl.gz` shards plus
  `manifest.json` and `README.md`.
- `schneiderkamplab/dfm8-openhermes-da`, commit
  `a9458057e49c84561b5c75495a3d0400614df1ba`, 10 `data/*.jsonl.gz` shards plus
  `manifest.json` and `README.md`.

The token used for upload was supplied interactively and must not be recorded
in the repo or wiki. Future DFM8 rebuilds can fetch these as normal HF
datasets; the next local step is to ensure the DFM8 download/source-tree config
uses these HF repos instead of relying only on
`export-upload-dfm8-openhermes-repaired`.

Continuation epoch-index rule for DFM8-post / DFM8-preference, 2026-07-14.
Confidence: high from `pretrain.py`, `dataset_new.py`, and
`data_io/sample_tokenized.py` inspection. Checkpoint epoch tags and sampled
dataset directories use different indexing conventions:

- Training/checkpoint epochs are 1-based. A checkpoint named `epoch_5` means
  five training epochs have completed.
- Sampled data directories are 0-based. `data_io/sample_tokenized.py` writes
  `epoch_0`, `epoch_1`, ...
- On resume, `pretrain.py` maps a completed `epoch_N` checkpoint to
  `start_epoch=N+1`, then calls `dataset.set_epoch(start_epoch - 1)`.
  Therefore resuming from `epoch_5` loads sampled directory `epoch_5` for the
  next epoch of data.

For a continuation from the DFM6/DFM7 `epoch_5` checkpoint into DFM8,
DFM8-post, or DFM8-preference SFT with the existing `pretrain.py`, the target
sampled dataset must contain `epoch_5` for the first continuation epoch. There
is no separate epoch-offset config in the current trainer. Safe options:

1. Sample at least six epochs and use the generated `epoch_5` onward. This is
   the most semantically direct path, but wastes time if only one continuation
   epoch is needed.
2. Sample one post-training epoch, then explicitly copy or symlink `epoch_0`
   to `epoch_5` in a continuation-specific sampled directory. This is acceptable
   because the directory number is only the trainer's epoch cursor, not an
   intrinsic data property. Record the mapping in the run config/wiki.
3. Add a small trainer/dataset option such as `data_epoch_offset` if we want to
   keep sampled directories compact while resuming at arbitrary global epochs.
   Until implemented, do not assume such an offset exists.

For W&B/eval continuity, keep the resumed run's global epoch numbering at 6+
when resuming from `epoch_5`; do not reset the training checkpoint epoch to 1
unless intentionally starting a new, separate post-training run.

DFM8 / DFM8-post sampled token distribution snapshot, 2026-07-14.
Confidence: high for local counts from `data/sampled_dfm7/metadata.json`,
`data/sampled_dfm8/metadata.json`, `data/sampled_dfm8_post/metadata.json`, and
their `data/show_analytics_*.md` reports; medium for coarse category grouping.
The analytics `Cov Toks` column is total over sampled epochs, so divide by the
sample count to get per-epoch values. Current per-epoch totals:

| Sample | Sampled epochs | Tokens per epoch |
| --- | ---: | ---: |
| DFM7 | 5 | 66.657B |
| DFM8 | 6 | 67.410B |
| DFM8-post | 9 | 27.048B |

Approximate per-epoch coarse buckets from `Cov Toks / epochs`:

| Bucket | DFM7 | DFM8 | DFM8-post |
| --- | ---: | ---: | ---: |
| Danish | 16.812B | 17.159B | 6.960B |
| English/general instruction | 14.400B | 14.791B | 2.888B |
| Math/code/reasoning | 16.944B | 16.958B | 4.201B |
| Tool/agentic | 9.624B | 9.624B | 11.648B |
| Synthetic/transforms | 3.498B | 3.498B | 0B by the coarse grouping used in the quick report |
| Other/legacy | 5.380B | 5.380B | 1.351B |

Superseded critical DFM8 union issue discovered while inspecting the
distribution, 2026-07-14. Confidence: high from
`scripts/build_tokenized_dfm8_tree.py`, `data/tokenized_dfm8`, and
`data/show_analytics_dfm8.md` inspection. The earlier
`data/tokenized_dfm8` / `data/sampled_dfm8` build should be treated as a
discarded snapshot, not the intended final DFM8 mix:

- `scripts/build_dfm8_chat_source_tree.py` excludes raw
  `data/dfm8_special_sources/openhermes_2_5`, but
  `scripts/build_tokenized_dfm8_tree.py` independently accepts any raw
  tokenized task prefixed by `dfm8_special_sources__`.
- As a result, `data/tokenized_dfm8` contains raw
  `openhermes_2_5__train-*.jsonl` tasks.
- The repaired HF-upload-shaped shards under
  `export-upload-dfm8-openhermes-repaired__dfm8-openhermes-en__data__*.jsonl.gz`
  and `...dfm8-openhermes-da...` were tokenized, but not selected into
  `data/tokenized_dfm8`; the selector only matched the exact directory name
  `dfm8-openhermes-en` / `dfm8-openhermes-da`, not nested shard paths.

Before DFM8 training, fix `scripts/build_tokenized_dfm8_tree.py` so it:

1. rejects `dfm8_special_sources__openhermes_2_5__*`;
2. maps repaired OpenHermes nested shard paths to stable selected task names
   such as `dfm8-openhermes-en__data__train-00000.jsonl.gz`;
3. rebuilds `data/tokenized_dfm8`, `data/sampled_dfm8`, and
   `data/sampled_dfm8_post`; and
4. reruns the distribution report.

Raw OpenHermes removal and repaired-only DFM8 rebuild, 2026-07-14.
Confidence: high from local script inspection, path scans, and successful
resampling. Raw `teknium/OpenHermes-2.5` / `openhermes_2_5` was removed from
the DFM8 pipeline entirely:

- `scripts/download_training_datasets.py` no longer contains a
  `teknium/OpenHermes-2.5` / `openhermes_2_5` dataset entry.
- `scripts/prepare_dfm8_data.sh` no longer calls the raw OpenHermes converter.
- `scripts/convert_dfm8_openhermes.py` was deleted.
- Raw local artifacts under `data/downloads/datasets/openhermes_2_5`,
  `data/dfm8_special_sources/openhermes_2_5`, and raw tokenized
  `dfm8_special_sources__openhermes_2_5__*` paths were removed.
- `scripts/build_dfm8_chat_source_tree.py` and
  `scripts/build_tokenized_dfm8_tree.py` no longer need raw-OpenHermes-specific
  exclusion rules.
- The corrected `data/tokenized_dfm8` contains only repaired OpenHermes shards
  named `dfm8-openhermes-en__data__train-*.jsonl.gz` and
  `dfm8-openhermes-da__data__train-*.jsonl.gz`.

The corrected DFM8 and DFM8-post samples were rebuilt after this cleanup:

```bash
python scripts/build_dfm8_chat_source_tree.py --force --new-only
python scripts/build_tokenized_dfm8_tree.py --force --base-tokenized data/tokenized_dfm7
python scripts/report_dfm8_mix.py
rm -rf data/sampled_dfm8 data/sampled_dfm8_post data/tokenized_dfm8_post
(cd data_io && python sample_tokenized.py \
  tokenized_path=../data/tokenized_dfm8 \
  output_path=../data/sampled_dfm8 \
  epochs=6 \
  concat_workers=4 \
  prefix_config_path=prefix_config_dfm8.yaml \
  > ../data/show_analytics_dfm8.md)
DFM8_POST_EPOCHS=9 bash scripts/prepare_dfm8_post_data.sh
```

Corrected per-epoch totals from `metadata.json` and `show_analytics` reports:

| Sample | Sampled epochs | Tokens per epoch |
| --- | ---: | ---: |
| DFM7 | 5 | 66.657B |
| DFM8 | 6 | 68.613B |
| DFM8-post | 9 | 28.642B |

Approximate coarse per-epoch buckets:

| Bucket | DFM7 | DFM8 | DFM8-post |
| --- | ---: | ---: | ---: |
| Danish | 16.812B | 18.081B | 7.883B |
| English/general instruction | 14.400B | 15.072B | 3.560B |
| Math/code/reasoning | 16.944B | 16.958B | 4.201B |
| Tool/agentic | 9.624B | 9.624B | 11.648B |
| Synthetic/transforms | 3.498B | 3.498B | 0B by this coarse grouping |
| Other/legacy | 5.380B | 5.380B | 1.351B |

DFM8-specific additions and DFM8-post representation:

| Addition | DFM8 tokens/epoch | In DFM8-post? | DFM8-post tokens/epoch |
| --- | ---: | --- | ---: |
| `dfm8-openhermes-en` | 0.672B | yes | 0.672B |
| `dfm8-openhermes-da` | 0.922B | yes | 0.922B |
| `giannor_tv2r_instruction` (`dala_tv2r_it` + `gec_dala_tv2r_it`) | 0.261B | no | 0B |
| `kobprof_skolegpt_instruct` | 0.086B | yes, upweighted | 0.108B |

DFM8-post uses `data/tokenized_dfm8_post`, a filtered tokenized tree with
`4,166` linked tasks: `4,116` focus tasks and `50` broad-anchor tasks. Focus
families include repaired OpenHermes EN/DA, DFM8 behavior synthetic datasets,
native tool-use/agentic datasets, instruction-following datasets, Danish chat
and instruction datasets, and summarization/control datasets. Broad anchors
include math/code/general capability-preservation sources such as
`openmathinstruct2`, `allenai_rlvr_gsm`, `allenai_rlvr_math`, Tulu math/code,
Dolci no-tools/general SFT, Platypus, GSM8K, MATH, and WebInstruct.

DFM8 missed-dataset check, 2026-07-14. Confidence: high from local
`data/tokenized_dfm8`, `data/dfm8_chat_sources`, and
`export-upload-dfm8-synthetic` inspection. The repaired OpenHermes EN/DA,
giannor TV2R DaLA/GEC-DaLA, SkoleGPT, broad Common-Pile/DynaWord transform
expansion, and older `transformations-*` uploads are present in the current
DFM8 tokenized tree. Raw OpenHermes is not present, which is intentional.

The six targeted DFM8 synthetic datasets are still missing from the current
DFM8 tokenized/sample tree even though the plan says they should be included
and the upload-ready folders exist under `export-upload-dfm8-synthetic`:

| Missing planned family | Current `data/tokenized_dfm8` tasks | Current source tokens |
| --- | ---: | ---: |
| `dfm8-synthetic-code-debugging` | 0 | 0 |
| `dfm8-synthetic-constrained-format-following` | 0 | 0 |
| `dfm8-synthetic-danish-summarization-rewrite-controls` | 0 | 0 |
| `dfm8-synthetic-multiturn-danish-english-chat` | 0 | 0 |
| `dfm8-synthetic-native-tool-calling` | 0 | 0 |
| `dfm8-synthetic-strict-math-answer-contract` | 0 | 0 |

Likely cause: `scripts/build_dfm8_chat_source_tree.py` links
`export-upload-dfm8-openhermes-repaired`, `dfm8_transform_expansion_filtered`,
`dfm8_special_sources`, and `export-upload`, but not
`export-upload-dfm8-synthetic`. As a result the six synthetic families are not
tokenized or sampled, and their `data_io/prefix_config_dfm8_post.yaml` focus
prefixes cannot contribute to DFM8-post yet.

Next fix before using DFM8/DFM8-post for training: link
`export-upload-dfm8-synthetic` into `data/dfm8_chat_sources`, ensure
`scripts/build_tokenized_dfm8_tree.py` maps nested synthetic shard paths to
stable task names matching the existing `dfm8-synthetic-*__` sampler prefixes,
then rebuild `data/tokenized_dfm8`, `data/sampled_dfm8`,
`data/tokenized_dfm8_post`, and `data/sampled_dfm8_post`.

Supersedes the missed-dataset check above. DFM8 targeted synthetic integration
completed, 2026-07-14. Confidence: high from local rebuild, manifests,
symlink-aware task scans, and sampled metadata. The six
`dfm8-synthetic-*` upload folders are now fully integrated:

- `scripts/build_dfm8_chat_source_tree.py` links
  `export-upload-dfm8-synthetic`.
- `scripts/build_tokenized_dfm8_tree.py` maps nested
  `export-upload-dfm8-synthetic__dfm8-synthetic-*__data__train-*.jsonl.gz`
  tokenized paths to stable `dfm8-synthetic-*__data__train-*.jsonl.gz`
  task names.
- `scripts/tokenize_chat_template.py` now normalizes legacy synthetic tool-call
  rows of the shape `{"function": "search", "parameters": {...}}` into the
  Gemma4 template-compatible
  `{"function": {"name": "search", "arguments": {...}}}` shape. This was needed
  for one row in
  `dfm8-synthetic-multiturn-danish-english-chat/data/train-00002.jsonl.gz`.

Rebuild commands used from the repo root:

```bash
rm -rf data/dfm8_chat_sources data/tokenized_dfm8_jinja data/tokenized_dfm8 \
  data/sampled_dfm8 data/tokenized_dfm8_post data/sampled_dfm8_post
TOKENIZER_WORKERS=16 DFM8_EPOCHS=6 DFM8_CONCAT_WORKERS=4 \
  bash scripts/prepare_dfm8_data.sh

# After the first tokenization pass exposed the legacy tool-call row shape:
python scripts/tokenize_chat_template.py \
  data/dfm8_chat_sources \
  --tokenizer-path /work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json \
  --chat-template data_io/chat_templates/gemma4_native_chat.jinja \
  --output-dir data/tokenized_dfm8_jinja \
  --workers 16 \
  --skip-bad-json

python scripts/build_tokenized_dfm8_tree.py --force --base-tokenized data/tokenized_dfm7
python scripts/report_dfm8_mix.py
rm -rf data/sampled_dfm8 data/tokenized_dfm8_post data/sampled_dfm8_post
(cd data_io && python sample_tokenized.py \
  tokenized_path=../data/tokenized_dfm8 \
  output_path=../data/sampled_dfm8 \
  epochs=6 \
  concat_workers=4 \
  prefix_config_path=prefix_config_dfm8.yaml \
  > ../data/show_analytics_dfm8.md)
DFM8_POST_EPOCHS=9 DFM8_POST_CONCAT_WORKERS=4 bash scripts/prepare_dfm8_post_data.sh
```

Final manifests:

- `data/tokenized_dfm8/union_manifest.json`: `10,651` inherited DFM7 tasks and
  `69` DFM8-selected task shards. The DFM8-selected count includes the `42`
  targeted synthetic shards.
- `data/tokenized_dfm8_post/union_manifest.json`: `4,208` linked tasks:
  `4,148` focus tasks and `60` broad-anchor tasks.
- Symlink-aware scans confirm all six `dfm8-synthetic-*` shard families are
  present in both `data/tokenized_dfm8` and `data/tokenized_dfm8_post`.
- A symlink-aware scan confirms raw `openhermes_2_5` remains absent from
  `data/tokenized_dfm8`.

Corrected per-epoch totals after targeted synthetic integration:

| Sample | Sampled epochs | Tokens per epoch |
| --- | ---: | ---: |
| DFM7 | 5 | 66.657B |
| DFM8 | 6 | 70.479B |
| DFM8-post | 9 | 34.336B |

Approximate coarse per-epoch buckets, using the same bucket policy as the
previous snapshot and placing the six targeted synthetic datasets under
`Synthetic/transforms`:

| Bucket | DFM7 | DFM8 | DFM8-post |
| --- | ---: | ---: | ---: |
| Danish | 16.812B | 18.081B | 7.883B |
| English/general instruction | 14.400B | 15.072B | 3.560B |
| Math/code/reasoning | 16.944B | 16.958B | 4.201B |
| Tool/agentic | 9.624B | 9.624B | 11.648B |
| Synthetic/transforms | 3.498B | 5.364B | 5.694B |
| Other/legacy | 5.380B | 5.380B | 1.351B |

DFM8-specific additions and DFM8-post representation:

| Addition | DFM8 tokens/epoch | In DFM8-post? | DFM8-post tokens/epoch |
| --- | ---: | --- | ---: |
| `dfm8-openhermes-en` | 0.672B | yes | 0.672B |
| `dfm8-openhermes-da` | 0.922B | yes | 0.922B |
| `giannor_tv2r_instruction` | 0.261B | no | 0B |
| `kobprof_skolegpt_instruct` | 0.086B | yes | 0.108B |
| `dfm8-synthetic-code-debugging` | 0.247B | yes | 0.493B |
| `dfm8-synthetic-constrained-format-following` | 0.171B | yes | 0.513B |
| `dfm8-synthetic-danish-summarization-rewrite-controls` | 0.396B | yes | 1.188B |
| `dfm8-synthetic-multiturn-danish-english-chat` | 0.366B | yes | 1.099B |
| `dfm8-synthetic-native-tool-calling` | 0.513B | yes | 2.052B |
| `dfm8-synthetic-strict-math-answer-contract` | 0.173B | yes | 0.347B |
