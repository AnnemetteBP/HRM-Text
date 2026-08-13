---
type: Operational Record
title: Stored-generation BERTScore W&B sync, verified on (2026-05-27)
description: 'Chronological record from dfm-evals: Stored-generation BERTScore W&B
  sync, verified on (2026-05-27).'
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
# Stored-generation BERTScore W&B sync, verified on (2026-05-27)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Stored-generation BERTScore W&B sync, verified on 2026-05-27. Confidence:
high for upload logs and original clean API summary visibility; medium for the
active original-plus-mixed run summary because that live run has repeatedly
overwritten sidecar summary values.

`scripts/log_stored_bertscore_to_wandb.py` logs
`logs/dfm_evals/bertscore_xlm_roberta_large/stored_metrics.json` to W&B under
metric keys such as:

```text
dfm_eval/wmt24pp-en-da/bertscore_xlm_roberta_large/f1
dfm_eval/gec-dala/bertscore_xlm_roberta_large/precision
dfm_eval/generative-talemaader/bertscore_xlm_roberta_large/recall
dfm_eval/multi-wiki-qa/bertscore_xlm_roberta_large/n
```

The sync command was:

```bash
cd /work/dfm/HRM-Text
python scripts/log_stored_bertscore_to_wandb.py \
  2>&1 | tee logs/dfm_evals/bertscore_xlm_roberta_large/wandb_sync.log
```

W&B reported upload success for `origLclean` with history steps `65227-65230`
and for `es1od1in`. The public API summary check confirmed representative
`origLclean` keys, for example
`dfm_eval/wmt24pp-en-da/bertscore_xlm_roberta_large/f1/epoch_1 =
0.857831776017944`. The active `es1od1in` run did not retain these values in
the public summary immediately after sync, matching prior active-run summary
overwrite behavior; the W&B client still reported a successful history upload.
