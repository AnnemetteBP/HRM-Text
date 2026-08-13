---
type: Policy Record
title: Expert Export Upload Packaging
description: 'Part of Data Mix Policy: Expert Export Upload Packaging.'
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
# Expert Export Upload Packaging

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Added on 2026-06-17. Confidence: high for local file layout and validation.

The `export/` folders mix original generated data, judge-filtered data, and
historical audit run directories. For HF-style upload, create clean copies
under `export-upload/` rather than uploading `export/` directly.

For audited datasets such as `common-pile-denoising`, the upload payload should
use only the accepted rows from:

```text
export/<dataset>/audited/data/
```

as the top-level:

```text
export-upload/<dataset>/data/
```

The original unfiltered `export/<dataset>/data/` and historical
`audit_*` folders are local provenance/intermediate artifacts and should not be
part of the normal training-data upload. The full audit JSONL is not a clean
per-row annotation for the filtered upload files because its stable row IDs
point to original unfiltered coordinates such as
`common-pile-denoising/train-xxxxx.jsonl.gz:<line>`. A compact
`audit_summary.json` is more appropriate in the upload copy unless we also
publish the unfiltered data or embed provenance IDs in each filtered row.

First clean upload copy created:

```text
export-upload/common-pile-denoising/
  README.md
  recreate_dataset.py
  audit_summary.json
  data/train-*.jsonl.gz
```

Local validation:

- copied with `cp --reflink=never`; no symlinks;
- sampled source/upload files have different inodes and `nlink=1`;
- `477` data shards;
- `254,565` uploaded accepted rows;
- Superseded detail: `audit_full/audit.jsonl` alone has `62,603` audited rows,
  `61,786` keep, and `817` drop. This is only one audit component and should
  not be described as the final filtering audit.

Follow-up on 2026-06-17. Confidence: high for local file inspection and
validation commands. The clean upload copy is:

```text
export-upload/common-pile-denoising/
```

It is named with the Common Pile export family even though its accepted rows
currently come only from Common Pile's arXiv abstract/paper families. The
upload copy contains `254,565` accepted rows across `7` non-empty
`data/train-*.jsonl.gz` shards. Its `recreate_dataset.py` is now denoise-only:
the previous reusable prefix-continuation/span-filling/paragraph-reordering
generation and judge-audit branches were removed, and the CLI no longer exposes
an objective selector. Local validation passed with:

```bash
python -m py_compile export-upload/common-pile-denoising/recreate_dataset.py
python export-upload/common-pile-denoising/recreate_dataset.py --help
python export-upload/common-pile-denoising/recreate_dataset.py audit --help
```

The same packaging strategy was applied to:

```text
export-upload/danish-dynaword-denoising/
```

Confidence: high for local file inspection and validation commands. This
upload copy contains only the accepted judge-audited Danish DynaWord denoising
rows from `export/danish-dynaword-denoising/audited/data/`. The original
generated export had `1,854,932` rows across `90` gzip files. The audit covered
`69,907` rows, accepted `65,518`, and rejected `4,389`; the remaining generated
rows are not included because they had no explicit accepted audit decision. The
clean upload keeps only the four non-empty accepted shards:

```text
data/train-00000.jsonl.gz
data/train-00001.jsonl.gz
data/train-00002.jsonl.gz
data/train-00003.jsonl.gz
```

The `recreate_dataset.py` in this upload copy is Danish denoise-only, defaults
to `--language da`, and uses the prompt style `Gendan den oprindelige tekst.`.
Local validation passed with:

```bash
python -m py_compile export-upload/danish-dynaword-denoising/recreate_dataset.py
python export-upload/danish-dynaword-denoising/recreate_dataset.py --help
python export-upload/danish-dynaword-denoising/recreate_dataset.py audit --help
python -m json.tool export-upload/danish-dynaword-denoising/audit_summary.json
```

Follow-up on 2026-06-17. Confidence: high for local shard/source-order
inspection. The accepted rows in `export-upload/danish-dynaword-denoising` come
only from the first four generated shards, which map to the first four Parquet
files in sorted DynaWord source order:

| Generated shard | Source Parquet | Accepted rows |
|---|---|---:|
| `train-00000.jsonl.gz` | `data/adl/adl.parquet` | `28,730` |
| `train-00001.jsonl.gz` | `data/ai-aktindsigt/ai-aktindsigt.parquet` | `29,011` |
| `train-00002.jsonl.gz` | `data/botxt/botxt.parquet` | `524` |
| `train-00003.jsonl.gz` | `data/cellar/cellar.parquet` | `7,253` |

The original generated shards `train-00004` and later have no accepted rows in
the clean upload package. The generator was capped at about `30,000` generated
rows per source shard; the audit/filter output then kept only accepted row ids.

Follow-up on 2026-06-17. Confidence: high. The
`export-upload/danish-dynaword-denoising/README.md` structure and
`audit_summary.json` core fields were aligned with
`export-upload/common-pile-denoising/`: same Contents/Sources/Example/Filtering/Recreate
section pattern, same `format: "chat messages"` value, same `task:
"denoising"` value, and the same audit count field layout. The only extra JSON
field retained for Danish is `accepted_rows_by_source_file`, because the upload
is materially limited to four effective source Parquet files.

Follow-up on 2026-06-17. Confidence: high for local audit JSONL parsing,
accepted-data row counts, and validation commands. The same clean upload
packaging strategy was applied to the remaining paragraph-reordering,
span-filling, and prefix-continuation exports:

| Upload dataset | Files | Uploaded rows | Audited rows | Rejected rows | Effective source families |
|---|---:|---:|---:|---:|---|
| `export-upload/common-pile-prefix-continuation` | `19` | `619,911` | `740,695` | `120,784` | `common-pile/arxiv_abstracts_filtered`, `common-pile/arxiv_papers_filtered`, `common-pile/library_of_congress` |
| `export-upload/common-pile-span-filling` | `7` | `253,715` | `279,201` | `25,486` | `common-pile/arxiv_abstracts_filtered`, `common-pile/arxiv_papers_filtered` |
| `export-upload/common-pile-paragraph-reordering` | `16` | `86,328` | `182,122` | `95,794` | `common-pile/arxiv_papers_filtered`, `common-pile/project_gutenberg_filtered` |
| `export-upload/danish-dynaword-prefix-continuation` | `2` | `105,317` | `110,396` | `5,079` | `danish-foundation-models/danish-dynaword` |
| `export-upload/danish-dynaword-span-filling` | `2` | `54,968` | `56,315` | `1,347` | `danish-foundation-models/danish-dynaword` |
| `export-upload/danish-dynaword-paragraph-reordering` | `3` | `55,340` | `211,870` | `156,530` | `danish-foundation-models/danish-dynaword` |

For each folder, only non-empty accepted shards from `export/<dataset>/audited/data`
were copied to `export-upload/<dataset>/data`. Each folder has an aligned
`README.md`, `audit_summary.json`, and `recreate_dataset.py`; validation passed
with `python -m json.tool`, `python -m py_compile`, `recreate_dataset.py
--help`, `recreate_dataset.py audit --help`, and accepted-row recounts matching
`audit_summary.json`.

Correction/update on 2026-06-17. Confidence: high. The clean upload README and
`audit_summary.json` for `export-upload/common-pile-denoising` now include the
HF judge model ID and the de-duplicated all-audit rejection breakdown. The
audit model is recorded as `google/gemma-4-31B-it`, served locally under the
OpenAI-compatible vLLM alias `posttrain-gemma-teacher`. The upload filter used
`11` audit JSONL files. After de-duplicating by stable original row id, the
combined audit records:

| Audit outcome | Rows |
|---|---:|
| audited | `267,479` |
| accepted/uploaded | `254,565` |
| rejected by audit | `12,914` |

The original unfiltered export had `19,043,379` rows; `18,788,814` rows are not
included in the upload because the clean upload contains only the audited
`keep=true` set. That excluded count is not equivalent to judged-bad rows; it
also includes rows outside the selected audited keep set.

Rejected rows by primary failure type:

| Failure type | Rows |
|---|---:|
| `low_value_trivial` | `5,873` |
| `incoherent_or_ocr` | `3,158` |
| `response_mismatch` | `2,969` |
| `url_or_reference_dump` | `671` |
| `task_not_meaningful` | `75` |
| `other` | `64` |
| `metadata_boilerplate` | `62` |
| `empty_or_too_short` | `22` |
| `wrong_language` | `20` |

Name/content update on 2026-06-17. Confidence: high. The accepted
`common-pile-denoising` upload subset maps entirely to Common Pile arXiv
abstracts/papers (`79,101` accepted abstract rows and `175,464` accepted paper
rows). The clean upload package is:

```text
export-upload/common-pile-denoising/
```

Its README is intentionally short and upload-focused. The machine-readable
`audit_summary.json` records `dataset: common-pile-denoising`; the README notes
that the accepted rows currently come from Common Pile arXiv abstract/paper
sources.
The filtered folder originally contained one gzip shard per original source
file, including `470` empty gzip shards. Those empty shards were removed from
the clean upload copy, leaving `7` non-empty `data/train-*.jsonl.gz` files with
`254,565` rows.

Upload-card review on 2026-06-17. Confidence: high from local validation. All
12 current `export-upload/*` folders were reviewed for user-facing correctness,
relevance, and concision. README files were regenerated into a consistent
short structure covering contents, actual accepted sources, filtering counts,
one example, and recreation commands. Transformation dataset cards now describe
actual exported source clusters reconstructed from generation metadata rather
than the broader seed inventory. `audit_summary.json` for the four
transformation exports now also records those actual source clusters in
`accepted_rows_by_source_family` and `source_datasets`. Recreate script help
text was checked and missing top-level descriptions were added for the
paragraph-reordering, span-filling, and prefix-continuation scripts. Validation
passed for JSON parsing, Python compilation, `--help`, row/schema recounts,
and no symlinks or `__pycache__` directories remain under `export-upload/`.

HF upload attempt on 2026-06-17. Confidence: high from local API output. Upload
to `schneiderkamplab/*` was attempted with the Hugging Face API, using each
`export-upload/<name>` folder as one dataset repo. The first repo creation
failed before any data transfer:

```text
403 Forbidden: no rights to create a dataset under namespace schneiderkamplab
```

The token identified a user that belongs to the `schneiderkamplab` org, and
the target dataset repos did not already exist. The likely blocker is missing
org role/permission or token write scope for dataset repo creation. No token was
written to disk or the wiki. Local log:

```text
logs/hf_export_upload_20260617.log
```

Reusable uploader added:

```bash
cd /work/dfm/HRM-Text
HF_TOKEN=... python scripts/upload_export_upload_to_hf.py \
  --org schneiderkamplab \
  --root export-upload
```

Retry on 2026-06-17 with the explicitly provided token failed at the same
first `create_repo` call with the same 403. No files were uploaded. The uploader
now also supports `--skip-create` for the case where the 12 dataset repos are
created manually in the org first:

```bash
HF_TOKEN=... python scripts/upload_export_upload_to_hf.py \
  --org schneiderkamplab \
  --root export-upload \
  --skip-create
```

Superseding update on 2026-06-17. Confidence: high from successful local
Hugging Face API upload and `repo_info` visibility checks. The 12 original
`export-upload/*` dataset folders were uploaded to public dataset repos under
`schneiderkamplab`. `repo_info` reported `private=False` for all 12 repos. The
write-capable token was passed through `HF_TOKEN`; no token was written to disk
or the wiki. Upload log:

```text
logs/hf_export_upload_20260617.log
```

Synthetic Sapient-exclusion upload preparation, 2026-06-17. Confidence: high
from local script output and validation. The 70 accepted synthetic replacement
datasets from `export-synth/` were copied into direct `export-upload/` children
for later HF upload:

```text
export-upload/sapient-synth-high40-*
export-upload/sapient-synth-repeat30-*
export-upload/sapient-synth-upload-manifest.json
```

The copy was created with:

```bash
cd /work/dfm/HRM-Text
python scripts/prepare_export_synth_upload.py --force
```

Validation results:

- `70` upload dataset folders: `40` high40 and `30` repeat30.
- `254,247` accepted chat-format rows.
- No symlinks in the copied folders.
- All `70` copied `recreate_dataset.py` scripts compiled and validated their
  local `data/train-*.jsonl.gz` files.
- Six overlong source-derived names were shortened in the upload repo folder
  names to satisfy the Hugging Face 96-character repo-id limit; the manifest
  retains each original `dataset_id` and `original_task_name`.

Export packaging update, 2026-06-17. Confidence: high from local validation.
The synthetic upload folders now join all per-dataset shards into one file:

```text
export-upload/sapient-synth-*/data/train.jsonl.gz
```

There are exactly `70` such files, one per synthetic dataset. The upload repo
folder names no longer include the internal `high40`/`repeat30` campaign names;
that campaign group is retained only in metadata. The README structure now
matches the earlier 12 upload datasets more closely: HF YAML front matter,
Contents, Generation, License, and Recreate. The synthetic README text uses
`anonymous`, not `anonymized`, says `PII absence`, and describes overlap
precautions as creating new synthetic examples that preserve task type/skill,
not rewrites or copies of provenance rows. Each folder also contains
`LICENSE.md`, `metadata/manifest.json`, `metadata/summary.json`, and a
self-contained `recreate_dataset.py` that rebuilds/validates the single-file
layout. The license note states that the datasets that inspired these
recreations may have different licensing conditions, while the included rows
are fully synthetic recreations with no or minimal wording overlap and judged
to be free of PII. Validation after this change: all `70` recreate scripts
passed and recounted `254,247` rows.

The 12 earlier `common-pile-*`, `danish-dynaword-*`, and `transformations-*`
upload datasets were also updated to use Apache-2.0 HF front matter and
`LICENSE.md`. Their README bodies were otherwise left unchanged; no synthetic
provenance caveat was added to those 12.

The uploader now supports `--include-glob`, so these synthetic datasets can be
uploaded without re-uploading the earlier 12 datasets:

```bash
cd /work/dfm/HRM-Text
HF_TOKEN=... python scripts/upload_export_upload_to_hf.py \
  --org schneiderkamplab \
  --root export-upload \
  --include-glob 'sapient-synth-*' \
  --log logs/hf_export_upload_sapient_synth_20260617.log
```
