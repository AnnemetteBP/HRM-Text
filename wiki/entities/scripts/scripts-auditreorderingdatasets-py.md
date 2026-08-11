---
type: Software Reference
title: '`scripts/audit_reordering_datasets.py`'
description: 'Part of Script Entities: `scripts/audit_reordering_datasets.py`.'
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
# `scripts/audit_reordering_datasets.py`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-10; prompt audited/revised on 2026-06-11. Confidence: high
for local syntax, row counting, and prompt design; medium until a judge run has
been executed.

Audits the two expert paragraph-reordering exports with an OpenAI-compatible
judge model:

```text
expert/danish-dynaword-paragraph-reordering: 939,361 rows
expert/common-pile-paragraph-reordering:     277,029 rows
```

The script is non-mutating. It reads chat `.jsonl.gz` rows, asks a judge whether
each row is a meaningful supervised paragraph-reordering example, and writes
`logs/expert_reordering_audit/reordering_judge.audit.jsonl` plus
`summary.json`. It rejects rows that are semantically arbitrary, index/catalog
fragments, bibliographies, metadata lists, OCR garbage, too fragmented, or
where the response does not restore the same source content.

Prompt audit result, 2026-06-11: the judge prompt now explicitly distinguishes
topic interest from discourse-ordering usefulness, requires inferable order
from chronology/argument/local coherence, rejects arbitrary alphabetical/list
ordering, and asks for `primary_failure_type` so later filtering can be
diagnosed.

Suggested first pass against a local OpenAI-compatible judge:

```bash
python scripts/audit_reordering_datasets.py \
  --base-url http://127.0.0.1:8100/v1 \
  --model posttrain-gemma-teacher \
  --sample-rate 0.01 \
  --concurrency 8 \
  --audit-root logs/expert_reordering_audit/sample_1pct \
  --force
```

If the sample looks sane, run with `--sample-rate 1.0` or without
`--sample-rate`.

Superseded for the upload export folders: use each dataset folder's
self-contained `recreate_dataset.py audit` / `recreate_dataset.py filter`
commands instead. The standalone reordering audit script remains useful for
local experiments.
