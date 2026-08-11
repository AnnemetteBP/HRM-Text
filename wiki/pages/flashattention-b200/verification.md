---
type: Technical Reference
title: Verification
description: 'Part of FlashAttention on B200: Verification.'
tags:
- flashattention
- b200
- cuda
- performance
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/flashattention-b200.md
---
# Verification

Part of [FlashAttention on B200](/pages/flashattention-b200.md).

Earlier verified:

- `python -m py_compile models/flash_attention_prefixlm_v2.py models/layers.py`
- FA4 B200 forward smoke test
- PrefixLM forward/backward CUDA smoke test
- cache attention CUDA smoke test
- imports for `pretrain`, `simple_inference_engine`, and `evaluation.engines`

Refactor verification on 2026-05-26:

```bash
python -m py_compile models/flash_attention_prefixlm_common.py models/flash_attention_prefixlm_v2.py models/flash_attention_prefixlm_fa4.py models/flash_attention_prefixlm_dense.py models/flash_attention_prefixlm_mps.py
```

Also verified a tiny CPU dense PrefixLM forward/backward smoke through `models.flash_attention_prefixlm_v2.flash_attn_varlen_prefixlm`; outputs and gradients were finite. Confidence: high.

After regenerating `/private/tmp/hrm_tiny_sampled`, a one-step `scripts/debug_nan_training_step.py` CPU smoke also completed with finite loss, metric tensors, gradients, parameters, and post-optimizer parameters. Confidence: high.

Later on 2026-05-26, the SM100/FA4 implementation moved out of `models/flash_attention_prefixlm_v2.py` into `models/flash_attention_prefixlm_fa4.py`, and the dense fallback moved into `models/flash_attention_prefixlm_dense.py`.

Refactor update on 2026-05-29: accelerator selection moved from `models/flash_attention_prefixlm_v2.py` into `models/flash_attention_prefixlm_dispatch.py`. `v2` now remains a stable public compatibility module for `dataset_new.py`, `models/layers.py`, and debug scripts, while backend policy lives in the dispatcher. Verified with:

```bash
python -m py_compile models/flash_attention_prefixlm_v2.py models/flash_attention_prefixlm_dispatch.py models/flash_attention_prefixlm_fa4.py models/flash_attention_prefixlm_dense.py
```

Also verified a tiny CPU dense PrefixLM forward/backward smoke through `models.flash_attention_prefixlm_v2.flash_attn_varlen_prefixlm`; outputs and gradients were finite. Confidence: high.

SM90 layout update on 2026-05-29: the original H100/FA3 implementation was moved back into `models/flash_attention_prefixlm_v2.py` to minimize drift from commit `00b4fe5`. The separate `models/flash_attention_prefixlm_fa3.py` backend file was removed. `v2` now dispatches to `models.flash_attention_prefixlm_dispatch.flash_attn_varlen_prefixlm` only when `accelerator_type != "sm90"`. The FA3 import is lazy-safe so CPU/MPS/SM100 environments without `flash_attn_interface` can still import `v2`; attempting the SM90 path without FlashAttention 3 raises an explicit ImportError. Verified with:

```bash
python -m py_compile models/flash_attention_prefixlm_v2.py models/flash_attention_prefixlm_dispatch.py models/flash_attention_prefixlm_fa4.py models/flash_attention_prefixlm_dense.py models/flash_attention_prefixlm_mps.py
```

Also verified a tiny CPU dense PrefixLM forward/backward smoke through the `v2` public entrypoint; outputs and gradients were finite. Confidence: high.

MPS dispatch update on 2026-05-29: the Metal PrefixLM path no longer uses environment variables for opt-in or shape caps. For `accelerator_type=mps`, the dispatcher now chooses the Metal kernel dynamically when the actual attention tensors are on MPS, are `float32`, and have matching `q/k/v` shapes; otherwise it falls back to dense SDPA. The raw MPS kernel still validates dtype and shape internally. Debug scripts compare dense vs custom by temporarily switching the process-local `accelerator_type`, not by mutating environment variables. Confidence: high.

MPS bf16 update on 2026-05-26: `pretrain.py` no longer rewrites `fwd_bwd_dtype=bfloat16` to `float32` for `mps`/`cpu`/`none`. Instead, `TrainState` records the resolved forward/backward dtype and non-CUDA train steps use `torch.autocast(device_type=..., dtype=...)` when that dtype is not float32. This keeps parameters in fp32 while allowing bf16 forward/backward activations on supported CPU/MPS operations. Verified outside the sandbox on the M2 Max with `torch==2.13.0.dev20260524`: bf16 MPS matmul works, dense PrefixLM bf16 forward/backward on `mps:0` works, and a 3-step MPS training smoke with `fwd_bwd_dtype=bfloat16` completed with finite losses, metric tensors, gradients, parameters, and post-optimizer parameters. Confidence: high for the tiny smoke; larger XS/S/B runs still need memory/performance validation.

MPS memory diagnostic update on 2026-05-26: a user float32 run grew from about `18 GB` to `44 GB` Activity Monitor memory by step 33. Because this happened in float32, bf16/autocast caching is not the primary explanation for that run. `pretrain.py` initially supported `mps_memory_log_interval` and `mps_empty_cache_interval` config fields; those names are now superseded by backend-neutral `memory_log_interval` and `empty_cache_interval`. If MPS `allocated` stays bounded while `reserved` rises, this is likely MPS allocator/driver high-water or fragmentation from dense attention temporaries; if `allocated` rises monotonically after zero-grad, investigate real tensor retention. Use `empty_cache_interval=10` or `25` as a mitigation/experiment, expecting some throughput cost. Confidence: medium until a long real XS/S/B run reports allocated-vs-reserved numbers.

Memory diagnostic update on 2026-05-29: memory logging and cache clearing were generalized across supported backends. Use `memory_log_interval` and `empty_cache_interval`; the older `mps_memory_log_interval` and `mps_empty_cache_interval` aliases were removed. Backend behavior:

```text
CUDA / sm90 / sm100:
  memory: allocated, reserved, max_allocated, max_reserved from torch.cuda
  empty cache: torch.cuda.empty_cache()

MPS:
  memory: allocated/current and reserved/driver from torch.mps
  empty cache: torch.mps.empty_cache()

CPU / none:
  memory: process RSS
  empty cache: no-op
```

The shared helpers live in `models/accelerator.py` as `memory_stats_for_device`, `synchronize_device`, and `empty_accelerator_cache`. `scripts/debug_nan_training_step.py` now uses the same backend-neutral memory reporting. Verified with `py_compile`, Hydra override composition for the new interval names, and a one-step CPU diagnostic on `/private/tmp/hrm_tiny_sampled` showing sane RSS values around `402-485 MiB`. Confidence: high.

Verified locally on 2026-05-25:

```bash
python -m py_compile models/accelerator.py models/flash_attention_prefixlm_fa3.py models/flash_attention_prefixlm_v2.py models/layers.py models/lm_head.py models/baselines/hrm_nocarry_bp_warmup.py pretrain.py scripts/debug_nan_training_step.py scripts/create_tiny_sampled_dataset.py
python scripts/create_tiny_sampled_dataset.py /private/tmp/hrm_tiny_sampled --rows 96 --epochs 1 --vocab-size 512 --inst-len 5 --resp-len 11
python scripts/debug_nan_training_step.py --steps 3 --allow-mps-cpu-fallback --override data.path=/private/tmp/hrm_tiny_sampled --override accelerator_type=mps --override compile_train_batch=false --override fwd_bwd_dtype=float32 --override global_batch_size=64 --override epochs=1 --override lr_warmup_steps=1 --override ema=null --override arch.n_layers=2 --override arch.hidden_size=64 --override arch.num_heads=4 --override arch.expansion=2 --override arch.half_layers=false --override arch.H_cycles=1 --override arch.L_cycles=1 --override +arch.bp_min_steps=1 --override arch.bp_max_steps=1
```

The 3-step diagnostic produced finite losses, metric tensors, gradients, and post-optimizer parameters. Inside the normal command sandbox, PyTorch reported `torch.backends.mps.is_built() == True` but `torch.backends.mps.is_available() == False`, so the first diagnostic used the explicit CPU fallback while still selecting the `mps` attention backend. Confidence: high for dense backend execution.

Fresh conda env update, 2026-05-25:

```bash
conda env remove -y -n hrm
conda create -y -n hrm python=3.13
conda run -n hrm uv pip install torch
conda run -n hrm uv pip install --upgrade --pre torch --index-url https://download.pytorch.org/whl/nightly/cpu
conda run -n hrm uv pip install hydra-core einops numba coolname wandb pydantic numpy pyyaml tqdm
```

The fresh `hrm` env is Python `3.13.13` on `osx-arm64`. Stable PyTorch installed as `torch==2.12.0`; the nightly upgrade installed `torch==2.13.0.dev20260524`.

Inside the sandbox, both builds report:

```text
torch.backends.mps.is_built() == True
torch.backends.mps.is_available() == False
torch.mps.device_count() == 0
```

Outside the sandbox, the same fresh `hrm` env with nightly PyTorch reports:

```text
torch==2.13.0.dev20260524
torch.backends.mps.is_built() == True
torch.backends.mps.is_available() == True
torch.mps.device_count() == 1
torch.ones(2, device="mps") + 1 -> tensor([2., 2.], device='mps:0')
```

The machine itself reports Apple M2 Max graphics with Metal support via `system_profiler SPDisplaysDataType`. Conclusion: the earlier MPS blocker was sandbox device visibility, not repo code, absent hardware, or the conda env.

The new explicit CPU backend was verified in the fresh `hrm` env:

```bash
conda run -n hrm python -m py_compile models/accelerator.py models/flash_attention_prefixlm_fa3.py models/flash_attention_prefixlm_v2.py models/layers.py models/lm_head.py models/baselines/hrm_nocarry_bp_warmup.py pretrain.py scripts/debug_nan_training_step.py scripts/create_tiny_sampled_dataset.py
conda run -n hrm python scripts/create_tiny_sampled_dataset.py /private/tmp/hrm_tiny_sampled --rows 96 --epochs 1 --vocab-size 512 --inst-len 5 --resp-len 11
conda run -n hrm python scripts/debug_nan_training_step.py --steps 3 --override data.path=/private/tmp/hrm_tiny_sampled --override accelerator_type=cpu --override compile_train_batch=false --override fwd_bwd_dtype=float32 --override global_batch_size=64 --override epochs=1 --override lr_warmup_steps=1 --override ema=null --override arch.n_layers=2 --override arch.hidden_size=64 --override arch.num_heads=4 --override arch.expansion=2 --override arch.half_layers=false --override arch.H_cycles=1 --override arch.L_cycles=1 --override +arch.bp_min_steps=1 --override arch.bp_max_steps=1
```

Result: 3 training steps completed with finite losses, metrics, gradients, and post-optimizer parameters. Confidence: high.

Actual MPS verification, run outside the sandbox on 2026-05-25:

```bash
conda run -n hrm python scripts/debug_nan_training_step.py --steps 3 --override data.path=/private/tmp/hrm_tiny_sampled --override accelerator_type=mps --override compile_train_batch=false --override fwd_bwd_dtype=float32 --override global_batch_size=64 --override epochs=1 --override lr_warmup_steps=1 --override ema=null --override arch.n_layers=2 --override arch.hidden_size=64 --override arch.num_heads=4 --override arch.expansion=2 --override arch.half_layers=false --override arch.H_cycles=1 --override arch.L_cycles=1 --override +arch.bp_min_steps=1 --override arch.bp_max_steps=1
```

Result: 3 training steps completed on `mps:0` with finite losses, metric tensors, gradients, and post-optimizer parameters. Confidence: high.

Gradient accumulation verification, run outside the sandbox on 2026-05-25:

```bash
conda run -n hrm python scripts/debug_nan_training_step.py \
  --steps 1 \
  --override data.path=data/sampled_original_sapient_partial_smoke \
  --override arch/size@arch=B \
  --override accelerator_type=mps \
  --override compile_train_batch=false \
  --override fwd_bwd_dtype=float32 \
  --override global_batch_size=131072 \
  --override gradient_accumulation_steps=8 \
  --override epochs=4 \
  --override lr=2.5e-4 \
  --override lr_warmup_steps=50 \
  --override ema=null
```

Result: one effective optimizer step completed with `local_microbatch_size=16384`, eight accumulated microbatches, finite loss, finite metrics, finite gradients, and finite post-optimizer parameters. This avoids the MPS dense-attention OOM seen when trying to run `global_batch_size=131072` as one physical dense-attention batch. Confidence: high.

Small model-size configs added on 2026-05-25:

```text
S:          n_layers=8, hidden_size=768, num_heads=6
XS:         n_layers=6, hidden_size=512, num_heads=4
XXS:        n_layers=6, hidden_size=256, num_heads=2
XXS_wide:   n_layers=4, hidden_size=384, num_heads=3
```

All new configs keep 128-dimensional attention heads and even layer counts for HRM `half_layers: true`. Hydra composition was verified for all four sizes, and a one-step MPS `XXS` diagnostic on `data/sampled_original_sapient_partial_smoke` completed with finite loss, metrics, gradients, and post-optimizer parameters. User-reported follow-up XXS run used `global_batch_size=16384` with `gradient_accumulation_steps=4`. Confidence: high for local diagnostic verification; medium for the user-reported follow-up setting.
