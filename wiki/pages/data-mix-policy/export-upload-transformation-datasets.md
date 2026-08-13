---
type: Policy Record
title: Export-Upload Transformation Datasets
description: 'Part of Data Mix Policy: Export-Upload Transformation Datasets.'
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
# Export-Upload Transformation Datasets

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Added on 2026-06-17. Confidence: high from local file inspection, JSONL row
counts, and exact matching against generation metadata.

The four synthetic transformation datasets have been prepared as standalone
HF-uploadable folders under `export-upload/`:

```text
export-upload/transformations-danish-danish
export-upload/transformations-danish-english
export-upload/transformations-english-danish
export-upload/transformations-english-english
```

Each folder contains copied gzip JSONL data, `README.md`,
`audit_summary.json`, `accepted_selection_summary.json`,
`generation_config.json`, local seed files, and a self-contained
`recreate_dataset.py`. There are no symlinks in these four upload folders.

The exported rows use the standard post-training chat schema:

```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

The rows themselves contain only `messages`. Actual task/source provenance is
therefore tracked in aggregate in `audit_summary.json["actual_contents"]`,
reconstructed by exact matching of exported chat messages against accepted
generation metadata after whitespace normalization. All exported rows matched
generation metadata and no unmatched rows were found.

Row counts:

| Dataset | Rows | Files | Accepted regeneration rows |
|---|---:|---:|---:|
| `transformations-danish-danish` | 208,117 | 250 | 0 |
| `transformations-danish-english` | 211,401 | 250 | 0 |
| `transformations-english-danish` | 246,288 | 409 | 1,260 |
| `transformations-english-english` | 248,474 | 388 | 997 |

The actual source clusters are:

| Dataset | Main actual source clusters |
|---|---|
| `transformations-danish-danish` | Danish DynaWord 146,043; Laerebogen 33,837; Danish Wiki Instruct 8,740; smaller Oliver Kinch, LexDK, and DOAB/Statistics sources |
| `transformations-danish-english` | Danish DynaWord 147,925; Laerebogen 34,378; Danish Wiki Instruct 9,132; smaller Oliver Kinch, LexDK, and DOAB/Statistics sources |
| `transformations-english-danish` | DFM4 scientific/arXiv summarization seeds 237,965; DBC 7,671; `facebook/asset` 369; LexDK 283 |
| `transformations-english-english` | DFM4 scientific/arXiv summarization seeds 238,221; DBC 9,535; `facebook/asset` 366; LexDK 352 |

The task families are the same across the four packages: exact sentence
summary, past-tense rewrite, child-friendly simplification, numbered fact
extraction, and non-copy rewrite. Per-task row counts are recorded in each
folder's `README.md` and `audit_summary.json`.
