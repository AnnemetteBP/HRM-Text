---
type: Technical Reference
title: XL full-run worked example on (2026-05-29)
description: 'Chronological record from Residual Risk: XL full-run worked example
  on (2026-05-29).'
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
# XL full-run worked example on (2026-05-29)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

XL full-run worked example on 2026-05-29: for `arch/size@arch=XL`, use `T=196608`, `D=1536`, `h=12`, `d=128`, `I=4096`, `V=65536`, `NH=NL=16` after `half_layers=true`, `HC=2`, `LC=3`, `bp_min=2`, `bp_max=5`, `bp_warmup_ratio=0.2`, and `steps=325925`. The HRM bp schedule gives:

```text
bp_steps=2: 21,728 steps
bp_steps=3: 21,728 steps
bp_steps=4: 21,728 steps
bp_steps=5: 260,741 steps
```

Using conservative worst-case attention `A = T * max_seq_len = 196608 * 4096 = 805,306,368` allowed query-key pairs per step:

```text
bp_steps=2: 3.463 PFLOPs/step
bp_steps=3: 4.047 PFLOPs/step
bp_steps=4: 4.631 PFLOPs/step
bp_steps=5: 5.215 PFLOPs/step
total:      1.624e21 FLOPs = 1.624 ZFLOPs
```

Using the first-smoke-batch observed average allowed attention density (`~462.5` keys/token) scaled to XL gives `A ~= 90,931,670` and a less conservative estimate:

```text
bp_steps=2: 2.551 PFLOPs/step
bp_steps=3: 2.959 PFLOPs/step
bp_steps=4: 3.367 PFLOPs/step
bp_steps=5: 3.775 PFLOPs/step
total:      1.177e21 FLOPs = 1.177 ZFLOPs
```

Confidence: medium. The conservative number intentionally overestimates attention; exact attention cost depends on the original Sapient packing distribution.
