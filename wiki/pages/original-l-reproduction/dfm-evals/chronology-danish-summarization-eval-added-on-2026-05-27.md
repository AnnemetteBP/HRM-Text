---
type: Operational Record
title: Danish summarization eval, added on (2026-05-27)
description: 'Chronological record from dfm-evals: Danish summarization eval, added
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
# Danish summarization eval, added on (2026-05-27)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Danish summarization eval, added on 2026-05-27. Confidence: high.

`NordjyllandNews` was added to the standard `eval/*` path in
`evaluation/benchmarks.py` and `evaluation/config/hrm_benchmarking.yaml`. It
uses the local DynaWord parquet file:

```text
data/downloads/datasets/danish_dynaword/data/nordjyllandnews/nordjyllandnews.parquet
```

The source file has `75,215` rows with a single `text` field. The benchmark uses
the `37,522` rows that contain an explicit `Referat:` reference. If the source
starts with `Lav et referat af nedenstående tekst:\n\nTekst:\n`, that wrapper is
removed before prompting. By default the eval uses an evenly spaced `1,000`
example subset to keep runtime practical; pass `max_samples=null` only when a
full 37k-example run is intended.

`NordjyllandNews` generation overrides are `condition=direct`,
`max_context=4096`, `max_tokens=128`, and `batch_size=8`. It uses the same
summarization metrics as `GovReport`: `n`, ROUGE F1, BLEU, `chrf3`, and
`chrf3pp`. Local smoke tests verified `NordjyllandNews(max_samples=3)` loads and
computes all metrics as plain Python values. Run with:

```bash
cd /work/dfm/HRM-Text
python -m evaluation.main ckpt_path="<CHECKPOINT_PATH>" "run_only=[NordjyllandNews]"
```
