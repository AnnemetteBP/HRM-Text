---
type: Operational Record
title: 2026-06-10 Expert Dataset Export Package
description: 'Part of Current State: 2026-06-10 Expert Dataset Export Package.'
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
# 2026-06-10 Expert Dataset Export Package

Part of [Current State](/pages/current-state.md).

Confidence: high for local file layout and validation commands.

Created a self-contained export package under:

```text
expert/
```

Superseded: the first export had `13` folders and copied internal Parquet/JSONL
files as hardlinked ordinary files. On 2026-06-10 it was rebuilt into the
standard post-training format below.

It now contains `12` upload-ready dataset subfolders. Each subfolder has:

- actual local data files under `data/*.jsonl.gz`;
- one JSON object per line with a chat-template-ready `messages` field:
  `{"messages":[{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}`;
- a `README.md` dataset card with provenance links and generation summary;
- a standalone `recreate_dataset.py` that does not import repo code or depend
  on another expert subfolder.

The top-level expert folders are:

```text
common-pile-denoising
common-pile-paragraph-reordering
common-pile-prefix-continuation
common-pile-span-filling
danish-dynaword-paragraph-reordering
danish-dynaword-denoising
danish-dynaword-prefix-continuation
danish-dynaword-span-filling
transformations-danish-danish
transformations-danish-english
transformations-english-danish
transformations-english-english
```

`govreport-summarization`, `wikicatsum-summarization`, and
`scientific-summaries-summarization` were removed because they were essentially
repackaged versions of existing HF datasets rather than locally distinctive
expert datasets. `arxiv-paper-summarization` was also removed because HF has
standard arXiv summarization datasets such as `ccdv/arxiv-summarization`, so
the local Common Pile arXiv-derived summarization export was too close to an
existing HF task.

Superseded internal variants were grouped by objective instead of exported as
separate top-level datasets. For example, DynaWord span filling includes all
six generated variants in one folder, and Common Pile span filling includes
all three generated variants in one folder. The DynaWord paragraph-reordering
export uses the later windowed version and does not include the earlier
superseded DynaWord paragraph tree. `common-pile-direct-continuation` was
removed on 2026-06-10 because direct continuation is not a post-training style
expert task.

The synthetic exports include only accepted examples. Rows with
`accepted != true` are dropped. Base generated rows whose `id` appears as a
regenerated `original_id` are also dropped; accepted regeneration rows are used
as replacements when available. The previous combined
`transformation-refinement-synthetic` folder was split into four source/target
language-pair folders:

```text
transformations-danish-danish:   208,117
transformations-danish-english:  211,401
transformations-english-danish:  246,288
transformations-english-english: 248,474
```

Together these contain `914,280` accepted chat rows.

Rows written by the 2026-06-10 rebuild:

```text
danish-dynaword-prefix-continuation:     3,268,392
danish-dynaword-denoising:               1,854,932
danish-dynaword-span-filling:            5,567,226
common-pile-prefix-continuation:        19,043,384
common-pile-denoising:                  19,043,379
common-pile-span-filling:               57,130,149
danish-dynaword-paragraph-reordering:      939,361
common-pile-paragraph-reordering:          277,029
transformations-danish-danish:             208,117
transformations-danish-english:            211,401
transformations-english-danish:            246,288
transformations-english-english:           248,474
```

Export sizes after rebuilding:

```text
common-pile-paragraph-reordering:          151M
transformations-english-english:           180M
transformations-danish-danish:             204M
transformations-english-danish:            217M
transformations-danish-english:            232M
danish-dynaword-paragraph-reordering:      434M
danish-dynaword-denoising:                 1.9G
danish-dynaword-prefix-continuation:       2.5G
danish-dynaword-span-filling:              5.0G
common-pile-prefix-continuation:           13G
common-pile-denoising:                     19G
common-pile-span-filling:                  49G
```

Validation performed:

```bash
find expert -type l | wc -l
find expert -type f \( -name '*.parquet' -o -name '*.jsonl' \) | head
find expert -type f -name '*.jsonl.gz' | wc -l
python -m py_compile scripts/build_expert_exports.py $(find expert -mindepth 2 -maxdepth 2 -name recreate_dataset.py | sort)
```

The symlink count was `0`; no raw `.parquet` or plain `.jsonl` files remained
under `expert/`; the compressed shard count was `4,187`; all recreation scripts
compiled successfully. A first-row smoke test for each dataset showed exactly
the top-level key `messages` with roles `user` and `assistant`.
