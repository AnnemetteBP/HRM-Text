---
type: Technical Reference
title: HF Export and Eval Loader Compatibility
description: 'Part of Model Architecture: HF Export and Eval Loader Compatibility.'
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
# HF Export and Eval Loader Compatibility

Part of [Model Architecture](/pages/model-architecture.md).

2026-07-23, Confidence: high from local inspection and smoke checks in the
`hrm` conda environment.

The active environment reports:

```text
transformers 5.12.1
torch 2.11.0+cu130
tokenizers 0.22.2
vllm 0.23.1rc1.dev102+ga46abb7ae
```

Installed Transformers has native `hrm_text` support under
`transformers.models.hrm_text`. `AutoModelForCausalLM.from_config()` expects
the explicit HF split projection layout:

```text
self_attn.gate_proj.weight
self_attn.q_proj.weight
self_attn.k_proj.weight
self_attn.v_proj.weight
self_attn.o_proj.weight
mlp.gate_proj.weight
mlp.up_proj.weight
mlp.down_proj.weight
```

Existing local HF exports such as
`exports/dfm8_XL_step1700000_ema_hf/model.safetensors` still contain the older
packed local layout:

```text
attn.gqkv_proj.weight   # chunk order: gate, q, k, v
attn.o_proj.weight
mlp.gate_up_proj.weight # chunk order: gate, up
mlp.down_proj.weight
```

This packed export still loads cleanly through the installed HF loader:
`missing_keys=0`, `unexpected_keys=0`, `mismatched_keys=0`, `error_msgs=0`.
Local tensor checks verified that the loader maps packed `gqkv` chunks to
`gate/q/k/v` exactly and maps packed `gate_up` chunks to `gate/up` exactly.

Superseded 2026-07-23 claim: `conversion/convert_to_hf.py` briefly wrote the
split HF layout by default and validated the converted state dict against
`AutoModelForCausalLM.from_config()`. That was compatible with Transformers
but not with the installed vLLM HRM implementation.

Replacement, 2026-07-23. Confidence: high from local export, directory
comparison, and vLLM smoke eval. Production HF export for vLLM-based evals
must use the packed vLLM layout. The converter default is now:

```text
--weight-layout vllm_packed
```

The opt-in split layout remains available only for explicit HF-only
experiments:

```text
--weight-layout hf_split
```

The installed vLLM HRM model expects packed modules named
`attn.gqkv_proj.weight` and `mlp.gate_up_proj.weight`; a split export failed
vLLM startup with:

```text
ValueError: There is no module or parameter named
'model.H_module.layers.0.mlp.gate_proj' in HrmTextForCausalLM.
The available parameters ... are:
{'model.H_module.layers.0.mlp.down_proj.weight',
 'model.H_module.layers.0.mlp.gate_up_proj.weight'}
```

A fresh packed re-export to
`exports/dfm8_XL_step1700000_ema_hf_reexport_packed_20260723` produced 131
tensors, all keys and tensors exactly matching
`exports/dfm8_XL_step1700000_ema_hf`; all non-weight files were hash-identical.
The fresh packed export loaded via HF with zero missing/unexpected/mismatched
keys and ran a vLLM smoke eval matching the official 1700K metrics:

| Task | Fresh packed smoke | Official 1700K |
| --- | ---: | ---: |
| ARC acc | 0.7867 | 0.7867 |
| BoolQ acc | 0.8777 | 0.8777 |

`simple_inference_engine.py` has two prompt modes:

- legacy HRM token mode using `condition_mapping` plus `boq/eoq`
- Gemma-template mode when checkpoint metadata has
  `template_mode: jinja_chat_template`

For DFM7/DFM8 Gemma-template checkpoints, the simple engine must load
`chat_template_path`, set `<bos>/<turn|>/<pad>` special tokens, render prompts
with `tokenizer.apply_chat_template(..., add_generation_prompt=True)`, and use
`<turn|>` as the stop token. A local tokenizer smoke rendered:

```text
<bos><|turn>user
What is 2+2?<turn|>
<|turn>model
```

The production vLLM eval chain primarily uses HF exports, but
`simple_inference_engine.py` remains relevant for checkpoint loading during HF
export and for direct/simple smoke eval scripts.
