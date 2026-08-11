---
type: Operational Record
title: W&B sync caveat for active original+mixed run, verified on (2026-05-25)
description: 'Chronological record from dfm-evals: W&B sync caveat for active original+mixed
  run, verified on (2026-05-25).'
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
# W&B sync caveat for active original+mixed run, verified on (2026-05-25)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

W&B sync caveat for active original+mixed run, verified on 2026-05-25. Confidence: high.

The per-task sidecar W&B sync processes reported successful `wandb.init(..., resume=...)` logging to active run id `es1od1in`, and local sidecar run directories contained the expected `dfm_eval/...` keys. However, the W&B public API initially showed no `dfm_eval/...` summary keys for that active run. The likely cause is concurrent sidecar resumes while the training process owns the same live run. DaLA and GEC-DaLA were patched into the online run summary directly with the W&B API:

```text
dfm_eval/dala/linguistic-acceptability/dfm_evals_macro_f1 = 0.06285135215101485
dfm_eval/dala/linguistic-acceptability/dfm_evals_mcc = -0.015338488073023071
dfm_eval/gec_dala/exact_match/mean = 0.1435546875
dfm_eval/epoch = 1
dfm_eval/last_epoch = 1
```

For future evals against a live training run, prefer either direct API summary updates or logging to a separate eval run and merging after training, rather than relying on multiple short-lived processes resuming the live training run.
