---
type: Technical Reference
title: Schedule
description: 'Part of Model Architecture: Schedule.'
tags:
- architecture
- hrm
- crm
- checkpoints
- inference
status: stable
last_updated: 2026-07-23
confidence: high
part_of: /pages/model-architecture.md
---
# Schedule

Part of [Model Architecture](/pages/model-architecture.md).

Default HRM config:

```yaml
half_layers: true
H_cycles: 2
L_cycles: 3
bp_warmup_ratio: 0.2
bp_max_steps: 5
```

With `half_layers: true`, the configured layer count is divided in half before constructing the H and L blocks, so a size config with `n_layers: 24` creates 12 Transformer layers in H and 12 in L.

The recurrence schedule is nested:

```text
for each of 2 H cycles:
  run 3 L cycles
  run 1 H cycle
```

So each forward pass runs 6 L block applications and 2 H block applications.

Backpropagation through recurrent applications is truncated by `bp_steps`, which warms from `bp_min_steps=2` to `bp_max_steps=5` over the first `20%` of total training steps. Allocation prioritizes H while leaving at least one L step:

```python
H_bp_steps = min(H_cycles, bp_steps - 1)
L_bp_steps = bp_steps - H_bp_steps
```

For the default `H_cycles=2`, `L_cycles=3`:

| `bp_steps` | H recurrent apps with grad | L recurrent apps with grad |
|---:|---:|---:|
| 2 | 1 | 1 |
| 3 | 2 | 1 |
| 4 | 2 | 2 |
| 5 | 2 | 3 |

All earlier recurrent applications still run, but with gradients disabled.
