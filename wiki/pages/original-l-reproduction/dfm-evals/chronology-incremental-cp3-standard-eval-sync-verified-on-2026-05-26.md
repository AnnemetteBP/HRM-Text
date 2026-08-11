---
type: Operational Record
title: Incremental CP3 standard eval sync, verified on (2026-05-26)
description: 'Chronological record from dfm-evals: Incremental CP3 standard eval sync,
  verified on (2026-05-26).'
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
# Incremental CP3 standard eval sync, verified on (2026-05-26)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Incremental CP3 standard eval sync, verified on 2026-05-26. Confidence: high.

After the CP3 scheduler started, the first completed standard evals were synced
to W&B run `es1od1in` at `eval/epoch=3`:

```text
eval/ARC/acc: 0.5904
eval/ARC/invalid: 0.0
eval/ARC/n: 1172
eval/BoolQ/acc: 0.8294
eval/BoolQ/invalid: 0.0
eval/BoolQ/n: 3270
eval/Winogrande/acc: 0.6464
eval/Winogrande/invalid: 0.0
eval/Winogrande/n: 1267
```

W&B history verification returned epoch-3 values for all three tasks. At that
time, no dfm-evals had completed and MATH was still partial. Confidence: high.
