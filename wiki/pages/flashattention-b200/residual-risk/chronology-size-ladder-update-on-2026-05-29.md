---
type: Technical Reference
title: Size-ladder update on (2026-05-29)
description: 'Chronological record from Residual Risk: Size-ladder update on (2026-05-29).'
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
# Size-ladder update on (2026-05-29)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Size-ladder update on 2026-05-29: added only the non-wide branch above `XXL`:

```text
XXXL:  n_layers=96,  hidden_size=2048, num_heads=16, head_dim=128
XXXXL: n_layers=128, hidden_size=2560, num_heads=20, head_dim=128
```

No new `*_wide` configs were kept. Hydra config composition was checked successfully for both `arch/size@arch=XXXL` and `arch/size@arch=XXXXL`. Confidence: high.
