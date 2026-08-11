---
type: Operational Record
title: Second manual dfm-evals sync, verified on (2026-05-24)
description: 'Chronological record from dfm-evals: Second manual dfm-evals sync, verified
  on (2026-05-24).'
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
# Second manual dfm-evals sync, verified on (2026-05-24)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Second manual dfm-evals sync, verified on 2026-05-24: DaLA and GEC-DaLA for epochs 2-4 were exported from completed Inspect logs and logged to W&B run `origLclean` under the same `dfm_eval/...` prefix. WMT24++ remained partial and was not synced. Confidence: high.

Second manual sync results:

```text
epoch 2:
  dfm_eval/dala/linguistic-acceptability/dfm_evals_macro_f1 = 0.00388
  dfm_eval/dala/linguistic-acceptability/dfm_evals_mcc = 0.00418
  dfm_eval/gec_dala/exact_match/mean = 0.00000

epoch 3:
  dfm_eval/dala/linguistic-acceptability/dfm_evals_macro_f1 = 0.00097
  dfm_eval/dala/linguistic-acceptability/dfm_evals_mcc = 0.00000
  dfm_eval/gec_dala/exact_match/mean = 0.00000

epoch 4:
  dfm_eval/dala/linguistic-acceptability/dfm_evals_macro_f1 = 0.00388
  dfm_eval/dala/linguistic-acceptability/dfm_evals_mcc = 0.00000
  dfm_eval/gec_dala/exact_match/mean = 0.00000
```
