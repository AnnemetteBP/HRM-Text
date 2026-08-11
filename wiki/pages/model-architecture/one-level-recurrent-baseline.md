---
type: Technical Reference
title: One-Level Recurrent Baseline
description: 'Part of Model Architecture: One-Level Recurrent Baseline.'
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
# One-Level Recurrent Baseline

Part of [Model Architecture](/pages/model-architecture.md).

Added on 2026-05-27:

- Model: `models/baselines/hrm1_nocarry_bp_warmup.py`
- Config: `config/arch/net/hrm1.yaml`
- Hydra override: `arch/net@arch=hrm1`

This is a separate one-level recurrent architecture, not the existing `ut_nocarry` baseline.

The model keeps one token-aligned recurrent state:

```text
z = x
for each recurrent cycle:
  z = R_level(z)
return z
```

There is no cross-level injection because there is only one level. Unlike `ut_nocarry`, this baseline does not keep injecting the original token embeddings into a learned recurrent state each pass; it initializes from the token embeddings and refines that state directly.

Default config:

```yaml
half_layers: true
cycles: 8
bp_warmup_ratio: 0.2
bp_min_steps: 1
bp_max_steps: 8
```

With `half_layers: true`, the configured layer count is divided by 2 before constructing the single recurrent block. This makes HRM1 compute-match HRM2 by recurrent application count: HRM2 runs 8 half-depth applications (`L,L,L,H,L,L,L,H`), and HRM1 runs 8 applications of one shared half-depth block. It is not parameter-matched to HRM2; it has about half the recurrent-block parameters. Backpropagation is truncated through the last `bp_steps` recurrent applications. Earlier recurrent applications still run with gradients disabled.

Verified locally:

```bash
/home/ucloud/miniforge3/envs/hrm/bin/python -m py_compile models/baselines/hrm1_nocarry_bp_warmup.py
```

CPU cache-path forward smoke also passed in the HRM env with a tiny config:

```text
torch.Size([2, 4, 64]) True
```

Tiny one-GPU compiled diagnostic with real sampled data:

```bash
cd /work/dfm/HRM-Text-3
CUDA_VISIBLE_DEVICES=7 PYTHONPATH=/work/dfm/HRM-Text-3 \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/ucloud/miniforge3/envs/hrm/bin/torchrun --master_port=29642 --nproc_per_node=1 \
  scripts/debug_nan_training_step.py \
  --steps 1 \
  --compiled-train-batch \
  --check-every-param \
  --override arch/net@arch=hrm1 \
  --override arch.n_layers=4 \
  --override arch.hidden_size=128 \
  --override arch.num_heads=4 \
  --override arch.expansion=2 \
  --override global_batch_size=512 \
  --override data.path=/work/dfm/HRM-Text/data/sampled_original_sapient \
  --override lr=1e-4
```

Result after adding `half_layers` and changing the default to `cycles=8`: one compiled optimizer step completed. The run reported `metric_tensors_finite=True` with range `[0.0, 3903.812744140625]` and `post_optim_params_finite=True` with range `[-0.26907622814178467, 0.26907891035079956]`. Confidence: high.
