---
type: Operational Record
title: 2026-06-11 Export Dataset Audit/Recreation Setup
description: 'Part of Current State: 2026-06-11 Export Dataset Audit/Recreation Setup.'
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
# 2026-06-11 Export Dataset Audit/Recreation Setup

Part of [Current State](/pages/current-state.md).

Confidence: high for local script validation and file inspection; medium until
the full vLLM judge audit completes.

The first eight non-synthetic export datasets are not pre-audited:

```text
common-pile-denoising
common-pile-paragraph-reordering
common-pile-prefix-continuation
common-pile-span-filling
danish-dynaword-denoising
danish-dynaword-paragraph-reordering
danish-dynaword-prefix-continuation
danish-dynaword-span-filling
```

Each of these eight folders now has a self-contained `recreate_dataset.py` with
three roles:

1. recreate similar raw-text-derived rows from source Parquet;
2. audit the current folder's `data/*.jsonl.gz` rows with an OpenAI-compatible
   judge via `python recreate_dataset.py audit ...`;
3. create a filtered copy via `python recreate_dataset.py filter ...`.

No separate per-folder audit helper is required. Filtering keeps only
`keep=true` rows from the audit JSONL. Negatively judged rows, judge errors, and
unaudited rows are excluded, so final upload filtering should use a full audit,
not a sample audit.

The 8-GPU runner is:

```bash
SAMPLE_RATE=1.0 CONCURRENCY=8 bash scripts/run_export_audits_8gpu_vllm.sh
```

It starts one vLLM Gemma 4 31B IT judge server per GPU/dataset and writes
`audit_full/audit.jsonl` plus `audit_full/summary.json` inside each export
folder. The default model path is
`data/models/google/gemma-4-31B-it-fresh-20260604`, falling back to
`/work/dfm/brainsurgery/models/google/gemma-4-31B-it`.

Validation performed:

```bash
bash -n scripts/run_export_audits_8gpu_vllm.sh
python -m py_compile $(find export -maxdepth 2 -name recreate_dataset.py | sort) scripts/build_expert_exports.py scripts/audit_export_datasets.py
```

Both passed locally. `__pycache__` directories created by validation were
removed from `export/`.
