---
type: Operational Record
title: Follow-up on (2026-05-25)
description: 'Chronological record from dfm-evals: Follow-up on (2026-05-25).'
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
# Follow-up on (2026-05-25)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Follow-up on 2026-05-25. Confidence: high. GEC-DaLA became visible in the UI, but DaLA did not. DaLA was re-logged with `wandb.log()` under both the original dfm-evals keys and simpler aliases:

```text
dfm_eval/dala/linguistic-acceptability/dfm_evals_macro_f1 = 0.06285135215101485
dfm_eval/dala/linguistic-acceptability/dfm_evals_mcc = -0.015338488073023071
dfm_eval/dala/macro_f1/mean = 0.06285135215101485
dfm_eval/dala/mcc/mean = -0.015338488073023071
```

The re-log process reported a successful W&B sync and run summary containing all four DaLA keys.
