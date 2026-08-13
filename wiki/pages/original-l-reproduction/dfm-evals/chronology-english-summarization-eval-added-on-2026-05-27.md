---
type: Operational Record
title: English summarization eval, added on (2026-05-27)
description: 'Chronological record from dfm-evals: English summarization eval, added
  on (2026-05-27).'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction/dfm-evals.md
---
# English summarization eval, added on (2026-05-27)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

English summarization eval, added on 2026-05-27. Confidence: high for local
implementation and smoke tests; medium for source-card metadata.

`GovReport` was added to the standard `eval/*` path in
`evaluation/benchmarks.py` and `evaluation/config/hrm_benchmarking.yaml`.
It uses the parquet-converted Hugging Face dataset
`ccdv/govreport-summarization`, config `document`, split `test`, with `report`
as the source document and `summary` as the reference. The originally considered
`launch/gov_report` source is CC-BY-4.0 and has simple `document`/`summary`
fields, but local smoke testing showed it still includes a dataset script and
this environment's `datasets` version refuses script-backed datasets:
`RuntimeError: Dataset scripts are no longer supported, but found gov_report.py`.

`GovReport` generation overrides are `condition=direct`, `max_context=4096`,
`max_tokens=512`, and `batch_size=2`. Metrics are `n`, `rouge1`, `rouge2`,
`rougeL`, `rougeLsum`, `bleu`, `chrf3`, and `chrf3pp`. ROUGE uses
`rouge_score` F1; BLEU and chrF use `sacrebleu` corpus scores, with `chrf3`
using `beta=3, word_order=0` and `chrf3pp` using `beta=3, word_order=2`.
Local smoke tests verified that `GovReport(split="test[:2]")` loads, computes
all metrics as plain Python floats, and resolves through
`load_model_class("benchmarks@GovReport", prefix="evaluation.")`. Run with:

```bash
cd /work/dfm/HRM-Text
python -m evaluation.main ckpt_path="<CHECKPOINT_PATH>" "run_only=[GovReport]"
```

It is less obviously contaminated by the original Sapient/FLAN summarization
task set than CNN/DailyMail, XSum, SAMSum, Gigaword, BillSum, Reddit TIFU,
Multi-News, or EUR-Lex summarization, all of which appear by name in the
original Sapient analytics. Source pages:
https://huggingface.co/datasets/launch/gov_report and
https://huggingface.co/datasets/ccdv/govreport-summarization.
