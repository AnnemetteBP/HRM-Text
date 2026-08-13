---
type: Technical Reference
title: Three-Level No-Compression Experimental Path
description: 'Part of Model Architecture: Three-Level No-Compression Experimental
  Path.'
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
# Three-Level No-Compression Experimental Path

Part of [Model Architecture](/pages/model-architecture.md).

Added on 2026-05-24:

- Model: `models/baselines/hrm3_nocarry_bp_warmup.py`
- Config: `config/arch/net/hrm3.yaml`
- Hydra override: `arch/net@arch=hrm3`

This is a separate architecture path; the existing `hrm` model and config are unchanged.

The three levels are:

- `S_level`: token/local recurrent block.
- `M_level`: segment-reasoning-style recurrent block, but still token-aligned.
- `H_level`: global-planning-style recurrent block, but still token-aligned.

No compression is implemented. `S`, `M`, and `H` all use full sequence hidden states, the same hidden width, and additive injection through:

```python
hidden_states + input_injection
```

Injection relation after the 2026-05-27 Option D correction:

```text
S update: z_S = S_level(z_S, z_M + z_H)
M update: z_M = M_level(z_M, z_S + z_H)
H update: z_H = H_level(z_H, z_M)
```

This gives the token/local level immediate top-down global context without adding an extra M priming pass. The effective information graph is:

```text
H -> S
H -> M
M -> S
S -> M
M -> H
```

Earlier HRM3 notes are superseded where they imply that `S` only received `M`, or that `M` only received `S`. The first HRM3 draft updated `H` from `M` but did not feed `H` back down. The first 2026-05-27 correction fed `H` into `M`; Option D additionally feeds `H` into `S`. Confidence: high.

The initial states are:

- `z_H = x`
- `z_M = zM_init`
- `z_S = x + zS_init`

`z_S` starts token-aligned so the first S update has full sequence shape before M has been injected with token information.

Default schedule:

```yaml
third_layers: true
H_cycles: 2
M_cycles: 2
S_cycles: 2
bp_warmup_ratio: 0.2
bp_min_steps: 3
bp_max_steps: 7
```

With `third_layers: true`, the configured layer count is divided by 3 before constructing each level. A size config with `n_layers: 24` creates 8 Transformer layers in S, 8 in M, and 8 in H. The configured layer count must be divisible by 3; current `B`, `L`, and `XXL` sizes satisfy this, while the default `XL` and `XXL_wide` size configs do not.

The recurrence schedule is nested:

```text
for each of 2 H cycles:
  for each of 2 M cycles:
    run 2 S cycles
    run 1 M cycle
  run 1 H cycle
```

So each forward pass runs 8 S block applications, 4 M block applications, and 2 H block applications.

Backpropagation allocation extends the current two-level priority policy: prioritize H, then M, while keeping at least one S application in the graph. For default cycles:

| `bp_steps` | H apps with grad | M apps with grad | S apps with grad |
|---:|---:|---:|---:|
| 3 | 1 | 1 | 1 |
| 4 | 2 | 1 | 1 |
| 5 | 2 | 2 | 1 |
| 6 | 2 | 3 | 1 |
| 7 | 2 | 4 | 1 |

Verified locally:

```bash
python -m py_compile models/baselines/hrm3_nocarry_bp_warmup.py
```

and with the HRM env:

```bash
/home/ucloud/miniforge3/envs/hrm/bin/python - <<'PY'
from models.baselines.hrm3_nocarry_bp_warmup import ThreeLevelHierarchicalReasoningModel
cfg = dict(
    max_seq_len=16, n_layers=6, hidden_size=64, num_heads=4,
    expansion=4, norm_type='pre', norm_eps=1e-6,
    rope_theta=10000.0, pos_emb_type='rope', init_type='lecun_normal',
    third_layers=True, H_cycles=2, M_cycles=2, S_cycles=2,
    bp_warmup_ratio=0.2, bp_min_steps=3, bp_max_steps=7,
)
model = ThreeLevelHierarchicalReasoningModel(cfg)
print(len(model.H_level.core.layers), len(model.M_level.core.layers), len(model.S_level.core.layers))
for steps in range(3, 8):
    print(steps, model._allocate_bp_steps(steps))
PY
```

Output confirmed `2 2 2` layers for the tiny test config and BP allocations `(1,1,1)`, `(2,1,1)`, `(2,2,1)`, `(2,3,1)`, `(2,4,1)`.

CPU cache-path forward smoke also passed in the HRM env with a tiny config:

```text
torch.Size([2, 4, 64]) True
```

CUDA/FA4/FSDP diagnostics on 2026-05-25:

The `HRM-Text-3` checkout does not currently have local sampled data, so diagnostics used the original Sapient sample from the sibling checkout:

```text
/work/dfm/HRM-Text/data/sampled_original_sapient
```

Because the environment had another checkout on `PYTHONPATH`, diagnostics must force this checkout first:

```bash
PYTHONPATH=/work/dfm/HRM-Text-3
```

Also, default `torchrun` port `29500` was already in use, so diagnostics used explicit `--master_port` values.

Tiny one-GPU compiled check, using one Transformer layer per level and real sampled data:

```bash
cd /work/dfm/HRM-Text-3
CUDA_VISIBLE_DEVICES=7 PYTHONPATH=/work/dfm/HRM-Text-3 \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/ucloud/miniforge3/envs/hrm/bin/torchrun --master_port=29632 --nproc_per_node=1 \
  scripts/debug_nan_training_step.py \
  --steps 2 \
  --compiled-train-batch \
  --check-every-param \
  --override arch/net@arch=hrm3 \
  --override arch.n_layers=3 \
  --override arch.hidden_size=128 \
  --override arch.num_heads=4 \
  --override arch.expansion=2 \
  --override global_batch_size=512 \
  --override data.path=/work/dfm/HRM-Text/data/sampled_original_sapient \
  --override lr=1e-4
```

Result: two compiled optimizer steps completed. Step 1 and step 2 both reported `metric_tensors_finite=True` and `post_optim_params_finite=True`. Confidence: high.

Tiny one-GPU non-compiled check, same overrides:

```bash
cd /work/dfm/HRM-Text-3
CUDA_VISIBLE_DEVICES=7 PYTHONPATH=/work/dfm/HRM-Text-3 \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/ucloud/miniforge3/envs/hrm/bin/torchrun --master_port=29633 --nproc_per_node=1 \
  scripts/debug_nan_training_step.py \
  --steps 2 \
  --check-every-param \
  --override arch/net@arch=hrm3 \
  --override arch.n_layers=3 \
  --override arch.hidden_size=128 \
  --override arch.num_heads=4 \
  --override arch.expansion=2 \
  --override global_batch_size=512 \
  --override data.path=/work/dfm/HRM-Text/data/sampled_original_sapient \
  --override lr=1e-4
```

Result: two non-compiled optimizer steps completed with finite loss, finite metric tensors, finite parameters, finite gradients, and finite post-optimizer parameters. Observed losses were about `11.356` and `10.544`. Confidence: high.

Full L-size one-GPU non-compiled check, using `arch/size@arch=L` and a tiny `global_batch_size=512`:

```bash
cd /work/dfm/HRM-Text-3
CUDA_VISIBLE_DEVICES=7 PYTHONPATH=/work/dfm/HRM-Text-3 \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/ucloud/miniforge3/envs/hrm/bin/torchrun --master_port=29634 --nproc_per_node=1 \
  scripts/debug_nan_training_step.py \
  --steps 1 \
  --check-every-param \
  --override arch/net@arch=hrm3 \
  --override arch/size@arch=L \
  --override global_batch_size=512 \
  --override data.path=/work/dfm/HRM-Text/data/sampled_original_sapient \
  --override lr=1e-4
```

Result: one full L-size HRM3 step completed. The run reported finite loss (`11.638178825378418`), `metric_tensors_finite=True`, `params_finite=True`, `grads_finite=True`, and `post_optim_params_finite=True`. Confidence: high.

Superseded on 2026-05-27: these diagnostics were run before the corrected `M` injection included `z_H`. They still validate the original HRM3 scaffolding, but the corrected injection rule needs fresh CUDA finite-step diagnostics before training.

Fresh tiny compiled diagnostic after the first 2026-05-27 injection correction, before Option D:

```bash
cd /work/dfm/HRM-Text-3
CUDA_VISIBLE_DEVICES=7 PYTHONPATH=/work/dfm/HRM-Text-3 \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/ucloud/miniforge3/envs/hrm/bin/torchrun --master_port=29635 --nproc_per_node=1 \
  scripts/debug_nan_training_step.py \
  --steps 1 \
  --compiled-train-batch \
  --check-every-param \
  --override arch/net@arch=hrm3 \
  --override arch.n_layers=3 \
  --override arch.hidden_size=128 \
  --override arch.num_heads=4 \
  --override arch.expansion=2 \
  --override global_batch_size=512 \
  --override data.path=/work/dfm/HRM-Text/data/sampled_original_sapient \
  --override lr=1e-4
```

Result: one compiled optimizer step completed with the corrected `M` injection. The run reported `metric_tensors_finite=True` and `post_optim_params_finite=True`. Superseded for exact current architecture by the Option D diagnostic below. Confidence: high.

Fresh tiny compiled diagnostic after the 2026-05-27 Option D correction:

```bash
cd /work/dfm/HRM-Text-3
CUDA_VISIBLE_DEVICES=7 PYTHONPATH=/work/dfm/HRM-Text-3 \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/ucloud/miniforge3/envs/hrm/bin/torchrun --master_port=29636 --nproc_per_node=1 \
  scripts/debug_nan_training_step.py \
  --steps 1 \
  --compiled-train-batch \
  --check-every-param \
  --override arch/net@arch=hrm3 \
  --override arch.n_layers=3 \
  --override arch.hidden_size=128 \
  --override arch.num_heads=4 \
  --override arch.expansion=2 \
  --override global_batch_size=512 \
  --override data.path=/work/dfm/HRM-Text/data/sampled_original_sapient \
  --override lr=1e-4
```

Result: one compiled optimizer step completed with Option D. The run reported `metric_tensors_finite=True` with range `[0.0, 3894.86572265625]` and `post_optim_params_finite=True` with range `[-0.269079327583313, 0.26907840371131897]`. Confidence: high.

Residual risk: full production-shape HRM3 training remains untested. The checks above validate model construction, real sampled data loading, FA4 PrefixLM forward/backward, FSDP wrapping, optimizer update, and torch.compile on a tiny corrected HRM3 shape, but not multi-GPU scaling or production batch memory.
