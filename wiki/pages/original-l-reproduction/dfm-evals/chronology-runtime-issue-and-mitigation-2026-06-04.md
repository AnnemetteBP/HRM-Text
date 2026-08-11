---
type: Operational Record
title: Runtime issue and mitigation (2026-06-04)
description: 'Chronological record from dfm-evals: Runtime issue and mitigation (2026-06-04).'
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
# Runtime issue and mitigation (2026-06-04)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Runtime issue and mitigation, 2026-06-04. Confidence: high.

During the true CP4 no-EMA lite eval, the first `govreport` attempt OOMed while
loading the BERTScore `xlm-roberta-large` scorer on the same GPU as the HRM
server. The traceback pointed to `dfm_evals/tasks/summarization.py` constructing
`BERTScorer(...).to(cuda)`. The mitigation was to add
`bertscore_device=cpu` to both `hrm_summarization_govreport` and
`hrm_summarization_nordjyllandnews` in
`config/dfm_evals_hrm_single_tasks.yaml`. The stuck `govreport` eval process
and leftover HRM server were killed; the scheduler retried the shard and the
retry reached `completion 61/61 failed 0`.
