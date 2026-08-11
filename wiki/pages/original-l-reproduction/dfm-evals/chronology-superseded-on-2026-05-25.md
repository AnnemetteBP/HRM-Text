---
type: Operational Record
title: Superseded on (2026-05-25)
description: 'Chronological record from dfm-evals: Superseded on (2026-05-25).'
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
# Superseded on (2026-05-25)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Superseded on 2026-05-25. Confidence: high. The user could see the correct original DaLA keys, so the simpler DaLA aliases were no longer wanted. The online W&B summary no longer contained the alias keys:

```text
dfm_eval/dala/macro_f1/mean
dfm_eval/dala/mcc/mean
dfm_eval/dala/f1/mean
```

W&B history rows are append-only, so alias keys that were logged once may still appear in the run's metric browser or auto-generated workspace panels. They should not be used for reporting; use only the original dfm-evals DaLA keys.
