---
type: Software Reference
title: '`scripts/generate_dfm4_tasks.py`'
description: 'Part of Script Entities: `scripts/generate_dfm4_tasks.py`.'
tags:
- scripts
- software
- catalog
- operations
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# `scripts/generate_dfm4_tasks.py`

Part of [Script Entities](/entities/scripts.md).

Generates additive DFM4 task sources.

Responsibilities:

- generate paragraph-reordering tasks from converted DynaWord and selected
  converted Common Pile rows
- generate arXiv paper-to-abstract summarization tasks from locally downloaded
  Common Pile arXiv paper JSON shards
- generate GovReport, WikiCatSum, and LAION Scientific-Summaries summarization
  tasks when those HF datasets are downloaded under `data/downloads/datasets`
- write PrefixLM-compatible `condition/instruction/response` Parquet trees
  under `data/converted_sources_dfm4_paragraph_reorder` and
  `data/converted_sources_dfm4_summarization`
- cap generation by rows per source file and by scanned rows per file so sparse
  paragraph sources cannot stall an entire generation pass
- support `--only {all,paragraph,summarization,laion}` for targeted
  regeneration, and `--laion-workers` for parallel LAION Scientific-Summaries
  conversion
- preserve response space for long summarization rows by using compact LAION
  fallbacks when full structured summaries do not fit the 4k-context training
  format
- for paragraph reordering, split the full document into paragraphs before
  trimming and sample deterministic contiguous paragraph windows instead of
  using only the beginning of long documents

Smoke test, 2026-06-01:

```bash
cd /work/dfm/HRM-Text
python scripts/generate_dfm4_tasks.py --force \
  --paragraph-output-root data/tmp_dfm4_paragraph_smoke \
  --summary-output-root data/tmp_dfm4_summary_smoke \
  --dynaword-rows-per-file 1 \
  --common-pile-rows-per-file 1 \
  --arxiv-summary-rows-per-file 1 \
  --laion-rows-per-file 1 \
  --max-rows-scanned-per-file 500 \
  --limit-files 1
```

This produced one DynaWord paragraph-reorder row and one arXiv summary row
from already downloaded local sources. GovReport, WikiCatSum, and LAION rows
were absent in the smoke test because those downloads had not yet been run.

Verified full LAION regeneration command, 2026-06-01:

```bash
cd /work/dfm/HRM-Text
python scripts/generate_dfm4_tasks.py --only laion --force --laion-workers 16
```

This wrote `4006` LAION task files and `2,288,807` rows under
`data/converted_sources_dfm4_summarization/dfm4_laion_scientific_summaries`.
