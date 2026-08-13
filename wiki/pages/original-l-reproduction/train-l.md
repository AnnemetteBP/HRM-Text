---
type: Experiment Record
title: Train L
description: 'Part of Original L Reproduction: Train L.'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction.md
---
# Train L

Part of [Original L Reproduction](/pages/original-l-reproduction.md).

Use the README L recipe with the dedicated data config:

```bash
cd /work/dfm/HRM-Text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
torchrun --nproc_per_node=8 pretrain.py \
  data=original_sapient \
  arch/size@arch=L \
  lr=2.5e-4 \
  global_batch_size=172032 \
  +project_name="Original Sapient L HLM-torch" \
  +run_name=original-sapient-L \
  +checkpoint_path=checkpoints/original_sapient/L
```

Hydra note, verified locally on 2026-05-22: `project_name`, `run_name`, and `checkpoint_path` are fields on `PretrainConfig`, but they are not declared in `config/cfg_pretrain.yaml`. Use `+project_name=...`, `+run_name=...`, and `+checkpoint_path=...` so Hydra appends them during composition.

Logging note, verified locally on 2026-05-22: the training loop logs scalar metrics to W&B from rank 0 every `log_interval=5` steps. It does not print the scalar values to stdout; stdout mainly shows epoch banners, warnings, and the rank-0 `tqdm` progress bar. Expected W&B history keys include `train/loss`, `train/accuracy`, `train/exact_accuracy`, `train/lr`, and `bp_steps`.

Runtime memory note, verified locally on 2026-05-22: the L run intentionally ramps `bp_steps` during the first `20%` of total training. With `total_steps=326338`, `bp_min_steps=2`, `bp_max_steps=5`, and `bp_warmup_ratio=0.2`, the approximate thresholds are `bp_steps=2` through step `21754`, `bp_steps=3` through `43510`, `bp_steps=4` through `65266`, and `bp_steps=5` from step `65267` onward. GPU memory therefore rises during early training; at step `~84475`, after epoch 1 and with `bp_steps=5`, `nvidia-smi` showed about `93-97 GiB` used per B200. CPU RSS for DataLoader worker children can also look very large after epoch transitions, but inspection showed it was mostly shared/file-backed mapped data (`RssFile`/`Shared_Clean`) with no swap, not equivalent private anonymous RAM. Confidence: high.

NaN-loss note, 2026-05-22: the first L reproduction launches reported NaN loss in W&B. The sampled original data was checked for empty-supervision rows: `resp_len` had no zero entries across epochs, so the simple zero-divisor explanation was ruled out. The failure was reproduced locally with `scripts/debug_nan_training_step.py`: step 1 was finite, but step 2 produced non-finite gradients first at `model.H_level.core.layers.0.attn.gqkv_proj.weight` while loss and parameters were still finite. This localized the issue to FA4 PrefixLM attention backward, not data, W&B, or optimizer state. `models/flash_attention_prefixlm_v2.py` was changed to compact dense prefix and causal Q/K/V sequences separately, call FA4 without `seqused_*` holes or zero-length query entries, and scatter results back. Confidence: high.

Second NaN-loss note, 2026-05-22: local W&B run `wandb/run-20260522_071714-5l4tsw6k` also logged `train/loss: NaN`, `train/accuracy: 0`, and `train/exact_accuracy: 0` at `_step: 200`, then was interrupted. Its config still used `+run_name=original-sapient-L` and `+checkpoint_path=checkpoints/original_sapient/L`, so it did not use the planned `original-sapient-L-fa4-compact` run/checkpoint names. The checkpoint directory contained only `all_config.yaml`, `train_metadata.yaml`, and `hrm_nocarry_bp_warmup.py`; no epoch checkpoint was present. Confidence: high.

Post-fix diagnostics, 2026-05-22:

```bash
cd /work/dfm/HRM-Text
CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
torchrun --nproc_per_node=1 scripts/debug_nan_training_step.py \
  --steps 12 \
  --compiled-train-batch \
  --override data=original_sapient \
  --override arch/size@arch=L \
  --override lr=2.5e-4 \
  --override global_batch_size=21504
```

Result: 12 one-GPU compiled steps had finite metric tensors and finite post-optimizer parameters.

```bash
cd /work/dfm/HRM-Text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
torchrun --nproc_per_node=8 scripts/debug_nan_training_step.py \
  --steps 4 \
  --compiled-train-batch \
  --override data=original_sapient \
  --override arch/size@arch=L \
  --override lr=2.5e-4 \
  --override global_batch_size=172032
```

Result: 4 eight-GPU compiled steps at the production global batch size had finite metric tensors and finite post-optimizer parameters on every rank. A later 3-step one-GPU compiled check also stayed finite after marking the dynamic FA4 PrefixLM wrapper with `@torch.compiler.disable`.

Dry-run cleanup helper:

```bash
cd /work/dfm/HRM-Text
scripts/cleanup_failed_training_run.sh --original-l-latest
```

Execute the cleanup only after inspection:

```bash
cd /work/dfm/HRM-Text
scripts/cleanup_failed_training_run.sh --original-l-latest --execute
```

Equivalent path-only override:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
torchrun --nproc_per_node=8 pretrain.py \
  arch/size@arch=L \
  lr=2.5e-4 \
  global_batch_size=172032 \
  data.path=data/sampled_original_sapient \
  +project_name="Original Sapient L HLM-torch" \
  +run_name=original-sapient-L \
  +checkpoint_path=checkpoints/original_sapient/L
```

Effective batch shape on 8 GPUs:

```text
Global token slots per optimizer step: 172,032
Per-GPU token slots: 21,504
Gradient accumulation: none
```
