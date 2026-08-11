---
type: Technical Reference
title: CRM3 Latent-Compressed Experimental Path
description: 'Part of Model Architecture: CRM3 Latent-Compressed Experimental Path.'
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
# CRM3 Latent-Compressed Experimental Path

Part of [Model Architecture](/pages/model-architecture.md).

Implemented on 2026-05-27. Confidence: high for implementation and tiny CUDA diagnostic; medium for production training behavior.

CRM3 is a separate model, not a config variant of HRM3 or CRM2:

```text
models/baselines/crm3_latent_nocarry_bp_warmup.py
config/arch/net/crm3.yaml
```

State shapes:

```text
z_S: token-level packed sequence state, [T, d]
z_M: per-sequence mid latent slots, [B * K_M, d]
z_H: per-sequence high latent slots, [B * K_H, d]
```

Default config:

```yaml
H_cycles: 2
M_cycles: 2
S_cycles: 2
num_m_latents: 256
num_h_latents: 64
latent_cross_attn_heads: 8
bp_warmup_ratio: 0.2
bp_min_steps: 3
bp_max_steps: 7
```

No-extra-pass Option-D-style flow:

```text
z_S = token embeddings
z_M = learned M latent slots per sequence
z_H = learned H latent slots per sequence

for each H cycle:
  for each M cycle:
    expanded_M = S-token queries attend to z_M
    expanded_H_to_S = S-token queries attend to z_H
    repeat S_cycles:
      z_S = S_level(z_S + expanded_M + expanded_H_to_S)

    compressed_S = M-latent queries attend to z_S
    expanded_H_to_M = M-latent queries attend to z_H
    z_M = M_level(z_M + compressed_S + expanded_H_to_M)

  compressed_M = H-latent queries attend to z_M
  z_H = H_level(z_H + compressed_M)

return z_S
```

This preserves the current HRM3 Option D information graph while compressing the upper two levels:

```text
H -> S
H -> M
M -> S
S -> M
M -> H
```

but with:

```text
S token states
M latent slots
H fewer latent slots
```

The main design risk is expansion cost. Since `z_H` expands directly to all S tokens each M cycle, CRM3 adds a `T * K_H` cross-attention path. That may still be acceptable if `K_H` is small, but a cheaper future variant is:

```text
H expands only to M
M expands to S
```

This cheaper variant removes direct `H -> S` and relies on `H -> M -> S`, so it is less faithful to HRM3 Option D but cleaner computationally.

Verified locally:

```bash
/home/ucloud/miniforge3/envs/hrm/bin/python -m py_compile models/baselines/crm3_latent_nocarry_bp_warmup.py
```

Tiny one-GPU compiled diagnostic with real sampled data:

```bash
cd /work/dfm/HRM-Text-3
CUDA_VISIBLE_DEVICES=7 PYTHONPATH=/work/dfm/HRM-Text-3 \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/ucloud/miniforge3/envs/hrm/bin/torchrun --master_port=29641 --nproc_per_node=1 \
  scripts/debug_nan_training_step.py \
  --steps 1 \
  --compiled-train-batch \
  --check-every-param \
  --override arch/net@arch=crm3 \
  --override arch.n_layers=3 \
  --override arch.hidden_size=128 \
  --override arch.num_heads=4 \
  --override arch.expansion=2 \
  --override arch.num_m_latents=8 \
  --override arch.num_h_latents=4 \
  --override arch.latent_cross_attn_heads=4 \
  --override global_batch_size=512 \
  --override data.path=/work/dfm/HRM-Text/data/sampled_original_sapient \
  --override lr=1e-4
```

Result: one compiled optimizer step completed. The run reported `metric_tensors_finite=True` with range `[0.0, 3894.79248046875]` and `post_optim_params_finite=True` with range `[-0.26907771825790405, 0.2690773606300354]`. Confidence: high.

Residual risk: full production-shape CRM3 training remains untested. Inference/export handling for two compressed latent levels is scaffolded but not validated end to end.
