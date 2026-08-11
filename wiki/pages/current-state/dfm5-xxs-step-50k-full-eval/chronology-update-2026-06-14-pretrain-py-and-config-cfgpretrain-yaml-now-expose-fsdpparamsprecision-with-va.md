---
type: Operational Record
title: 'Update 2026-06-14: pretrain.py and config/cfgpretrain.yaml now expose fsdpparamsprecision
  with values fp32 and'
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Update 2026-06-14:
  pretrain.py and config/cfgpretrain.yaml now expose fsdpparamsprecision with values
  fp32 and.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/current-state/dfm5-xxs-step-50k-full-eval.md
---
# Update 2026-06-14: pretrain.py and config/cfgpretrain.yaml now expose fsdpparamsprecision with values fp32 and

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-06-14. Confidence: high. `pretrain.py` and
`config/cfg_pretrain.yaml` now expose `fsdp_params_precision` with values
`fp32` and `bf16`. The default is `fp32`, preserving the previous FSDP
behavior: fp32 persistent sharded parameters/optimizer state with bf16
FSDP compute materialization when `fwd_bwd_dtype=bfloat16`.

When `fsdp_params_precision=bf16`, the model is cast to bf16 before FSDP
wrapping and optimizer construction, so the original/persistent FSDP sharded
parameters and Adam moments are bf16. To avoid repeating the DDP bf16 EMA
precision issue, the optimizer EMA shadow weights are kept in fp32 for this
mode.

Validation performed:

```bash
cd /work/dfm/HRM-Text
python -m py_compile pretrain.py
python - <<'PY'
from hydra import initialize, compose
from omegaconf import OmegaConf
from pretrain import PretrainConfig
with initialize(version_base=None, config_path='config'):
    cfg = compose(config_name='cfg_pretrain', overrides=[
        'data=dfm5',
        'arch/size@arch=XXS',
        'distributed_strategy=fsdp',
        'fsdp_params_precision=bf16',
        'fwd_bwd_dtype=bfloat16',
    ])
parsed = PretrainConfig(**OmegaConf.to_container(cfg, resolve=True))
print(parsed.distributed_strategy, parsed.fsdp_params_precision, parsed.fwd_bwd_dtype)
PY
```

The compose check printed:

```text
fsdp bf16 bfloat16
```
