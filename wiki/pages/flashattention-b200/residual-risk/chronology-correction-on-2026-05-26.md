---
type: Technical Reference
title: Correction on (2026-05-26)
description: 'Chronological record from Residual Risk: Correction on (2026-05-26).'
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
# Correction on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Correction on 2026-05-26: the earlier dense XXS smoke run `smoke-xxs-mps-bs16384-ga4` in `wandb/run-20260525_173337-apkt56ui` used the same seed and same target batch settings but did not show the step `1161-1200` spike. Direct local W&B history comparison:

```text
dense run, steps 1120-1160:
  mean train/loss:     4.922174
  mean train/accuracy: 0.304512
dense run, steps 1161-1200:
  mean train/loss:     4.877770
  mean train/accuracy: 0.307725
dense run, steps 1201-1220:
  mean train/loss:     4.881029
  mean train/accuracy: 0.303363

custom run, steps 1120-1160:
  mean train/loss:     4.867869
  mean train/accuracy: 0.309116
custom run, steps 1161-1200:
  mean train/loss:     7.881740
  mean train/accuracy: 0.174512
custom run, steps 1201-1220:
  mean train/loss:     7.367802
  mean train/accuracy: 0.168310
```

This makes the experimental custom MPS attention kernel the leading suspect. The failure is probably cumulative numerical or backward-gradient error rather than an immediate forward mismatch, because early training matches dense closely and the divergence appears only after more than one thousand optimizer steps. Confidence: high for the dense-vs-custom metric comparison; medium for the suspected mechanism.
