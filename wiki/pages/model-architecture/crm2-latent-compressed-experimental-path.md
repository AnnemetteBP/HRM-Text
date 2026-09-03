---
type: Technical Reference
title: CRM2 Latent-Compressed Experimental Path
description: 'Part of Model Architecture: CRM2 Latent-Compressed Experimental Path.'
tags:
- architecture
- hrm
- crm
- checkpoints
- inference
status: stable
last_updated: 2026-09-02
confidence: high
part_of: /pages/model-architecture.md
---
# CRM2 Latent-Compressed Experimental Path

Part of [Model Architecture](/pages/model-architecture.md).

Added on 2026-05-27:

- Model: `models/baselines/crm2_latent_nocarry_bp_warmup.py`
- Config: `config/arch/net/crm2.yaml`
- Hydra override: `arch/net@arch=crm2`

CRM2 is a separate compressed two-level model. It does not mutate the existing token-aligned HRM2 path.

## Gradient-reachability blocker (2026-09-02)

Static forward-graph review found that the final H update is task-dead. Each
cycle computes the token-level L states, compresses them, and updates H, but
the model returns `z_L` immediately after the final H update. That last H value
is never expanded back into a token state that contributes to cross-entropy.

At the default minimum `bp_steps=2`, the final H call is also the only H call
inside the gradient horizon. H can therefore receive an auxiliary loss but no
language-model task gradient at that phase. At larger BP values an earlier H
call can affect the following L cycle, but the final H call remains task-dead.

This finding supersedes any interpretation of the one-step finite diagnostic
below as evidence that all CRM2 levels receive task gradients. Before placing
MoE in H, reorder the recurrence or add a final downward expansion/token
update, then add explicit per-level gradient-reachability tests.

State shapes:

```text
z_L: token-level packed sequence state, [T, d]
z_H: learned latent slots per sequence, [B * K, d]
```

Default config:

```yaml
half_layers: true
H_cycles: 2
L_cycles: 3
num_latents: 256
latent_cross_attn_heads: 8
bp_warmup_ratio: 0.2
bp_min_steps: 2
bp_max_steps: 5
```

Forward structure:

```text
z_L = token embeddings
z_H = learned latent slots repeated per packed sequence

for each H cycle:
  expanded_H = token queries attend to z_H
  repeat L_cycles:
    z_L = L_level(z_L + expanded_H)
  compressed_L = latent queries attend to z_L
  z_H = H_level(z_H + compressed_L)

return z_L
```

Compression and expansion use learned cross-attention:

- `compress`: latent queries attend over the token states of their own packed sequence.
- `expand`: token queries attend over the latent slots for their own packed sequence.

The latent H Transformer gets its own PrefixLM-style sequence metadata where every latent slot is treated as prefix/bidirectional within each sequence. This keeps H attention on `K` latent slots per example rather than all token positions.

Implementation note: the packed latent helper uses scalar `.item()` calls to build dense per-sequence token grids, but those calls are isolated inside `@torch.compiler.disable` helpers. The cleaned tiny compiled diagnostic no longer reported Dynamo scalar graph-break warnings from CRM2; FA4/CUTLASS still emits its usual deprecation warnings. Confidence: high.

Verified locally:

```bash
/home/ucloud/miniforge3/envs/hrm/bin/python -m py_compile models/baselines/crm2_latent_nocarry_bp_warmup.py
```

Tiny one-GPU compiled diagnostic with real sampled data:

```bash
cd /work/dfm/HRM-Text-3
CUDA_VISIBLE_DEVICES=7 PYTHONPATH=/work/dfm/HRM-Text-3 \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/ucloud/miniforge3/envs/hrm/bin/torchrun --master_port=29640 --nproc_per_node=1 \
  scripts/debug_nan_training_step.py \
  --steps 1 \
  --compiled-train-batch \
  --check-every-param \
  --override arch/net@arch=crm2 \
  --override arch.n_layers=4 \
  --override arch.hidden_size=128 \
  --override arch.num_heads=4 \
  --override arch.expansion=2 \
  --override arch.num_latents=8 \
  --override arch.latent_cross_attn_heads=4 \
  --override global_batch_size=512 \
  --override data.path=/work/dfm/HRM-Text/data/sampled_original_sapient \
  --override lr=1e-4
```

Result: one compiled optimizer step completed. The run reported `metric_tensors_finite=True` with range `[0.0, 3866.23974609375]` and `post_optim_params_finite=True` with range `[-0.2690795361995697, 0.26907792687416077]`. Confidence: high.

Residual risk: full production-shape CRM2 training remains untested.
Inference/export handling for the latent H cache is also only scaffolded, not
validated end to end, and the upper-level gradient-reachability blocker above
must be corrected before an H-level MoE experiment.
