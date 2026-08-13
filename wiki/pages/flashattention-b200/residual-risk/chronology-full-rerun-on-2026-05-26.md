---
type: Technical Reference
title: Full rerun on (2026-05-26)
description: 'Chronological record from Residual Risk: Full rerun on (2026-05-26).'
tags:
- flashattention
- b200
- cuda
- performance
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/flashattention-b200/residual-risk.md
---
# Full rerun on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Full rerun on 2026-05-26: `smoke-xxs-custom-mps-bs16384-ga4-rerun` in `wandb/run-20260526_041126-tbtcaqxu` used the same XXS custom MPS settings after the on-disk kernel diagnostics. It did not reproduce the loss/accuracy spike:

```text
rerun custom, steps 1120-1160:
  mean train/loss:     4.862339
  mean train/accuracy: 0.309331
rerun custom, steps 1161-1200:
  mean train/loss:     4.816304
  mean train/accuracy: 0.312102
rerun custom, steps 1201-1220:
  mean train/loss:     4.818233
  mean train/accuracy: 0.308371
rerun custom, steps 1300-1410:
  mean train/loss:     4.769467
  mean train/accuracy: 0.313416
```

Conclusion: the spike in `smoke-xxs-custom-mps-bs16384-ga4` is not reproducible with the current custom MPS kernel. The most likely explanation is that the bad run used an older in-memory version of the experimental MPS kernel from before the later edits, or some other transient run-specific state, rather than a persistent issue in the current on-disk kernel. Confidence: high for the rerun comparison; medium for the causal explanation.
