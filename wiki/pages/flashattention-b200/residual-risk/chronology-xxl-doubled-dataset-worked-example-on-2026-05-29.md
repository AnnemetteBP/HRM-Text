---
type: Technical Reference
title: XXL doubled-dataset worked example on (2026-05-29)
description: 'Chronological record from Residual Risk: XXL doubled-dataset worked
  example on (2026-05-29).'
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
# XXL doubled-dataset worked example on (2026-05-29)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

XXL doubled-dataset worked example on 2026-05-29: for `arch/size@arch=XXL`, use `T=262144`, `D=1792`, `h=14`, `d=128`, `I=4864`, `V=65536`, `NH=NL=36` after `half_layers=true`, `HC=2`, `LC=3`, and the same HRM bp schedule. Starting from the XL reference `325925` steps at `196608` tokens/step, doubling the dataset and using `262144` tokens/step gives:

```text
steps = floor(2 * 325925 * 196608 / 262144) = 488887

bp_steps=2:  32,592 steps
bp_steps=3:  32,592 steps
bp_steps=4:  32,593 steps
bp_steps=5: 391,110 steps
```

Using conservative worst-case attention `A = T * max_seq_len = 262144 * 4096 = 1,073,741,824`:

```text
bp_steps=2: 13.346 PFLOPs/step
bp_steps=3: 15.632 PFLOPs/step
bp_steps=4: 17.918 PFLOPs/step
bp_steps=5: 20.204 PFLOPs/step
total:      9.430e21 FLOPs = 9.430 ZFLOPs
```

Using the first-smoke-batch observed average allowed attention density (`~462.5` keys/token) scaled to `T=262144` gives `A ~= 121,242,227`:

```text
bp_steps=2: 10.151 PFLOPs/step
bp_steps=3: 11.822 PFLOPs/step
bp_steps=4: 13.494 PFLOPs/step
bp_steps=5: 15.165 PFLOPs/step
total:      7.087e21 FLOPs = 7.087 ZFLOPs
```

Confidence: medium. The conservative number is the planning upper estimate; exact attention cost depends on packing.
