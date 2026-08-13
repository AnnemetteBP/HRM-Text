---
type: Technical Reference
title: XXSwide custom rerun on (2026-05-26)
description: 'Chronological record from Residual Risk: XXSwide custom rerun on (2026-05-26).'
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
# XXSwide custom rerun on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

XXS_wide custom rerun on 2026-05-26: `smoke-xxs-wide-custom-mps-bs16384-ga4-rerun` in `wandb/run-20260526_065719-k1sjdsw2` used `arch/size@arch=XXS_wide` (`hidden_size=384`, `num_heads=3`, `head_dim=128`) with `HRM_EXPERIMENTAL_MPS_MAX_HEADS=3`. The run was still alive when inspected, but had already diverged by step `153`; no epoch checkpoint had been written yet.

```text
custom XXS_wide, steps 1-20:
  mean train/loss:     10.853374
  mean train/accuracy: 0.061030
custom XXS_wide, steps 100-140:
  mean train/loss:     6.313171
  mean train/accuracy: 0.213356
custom XXS_wide, last logged rows 153-172:
  loss range: roughly 6.47 -> 7.73 -> 7.36
  accuracy range: roughly 0.18-0.23
```

The earlier dense `XXS_wide` run `smoke-xxs-wide-mps-bs16384-ga4` in `wandb/run-20260525_201730-e75a2o1u` had identical metrics through early training (`1-20` and `100-140`) but remained stable later (`steps 1120-1200` loss about `4.64-4.68`, accuracy about `0.317-0.321`). Interpretation: the current custom MPS kernel appears stable for `XXS` with 2 heads but unstable for `XXS_wide` with 3 heads, or for some interaction exposed by the wider geometry. Confidence: high for metric comparison; medium for attributing specifically to `num_heads=3`.

Tighter dense-vs-custom comparison for `XXS_wide`: the dense run `wandb/run-20260525_201730-e75a2o1u` and custom run `wandb/run-20260526_065719-k1sjdsw2` are identical through step `149`; custom begins to diverge at steps `150-152` and then clearly fails from step `153`.

```text
dense XXS_wide:
  steps 141-152: loss 6.093142, accuracy 0.234157
  steps 153-172: loss 6.061670, accuracy 0.234757
  steps 173-192: loss 5.967895, accuracy 0.242694

custom XXS_wide:
  steps 141-152: loss 6.122311, accuracy 0.233062
  steps 153-172: loss 7.309322, accuracy 0.197355
  steps 173-192: loss 7.846729, accuracy 0.165831
```

Confidence: high.
