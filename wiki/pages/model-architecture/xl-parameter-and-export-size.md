---
type: Technical Reference
title: XL Parameter and Export Size
description: Exact XL parameter count and its BF16 Hugging Face export size.
tags:
- architecture
- xl
- hf-export
status: stable
last_updated: 2026-08-15
confidence: high
part_of: /pages/model-architecture.md
---
# XL Parameter and Export Size

The current XL model has `1,786,773,504` model parameters. The DFM9 XL EMA
Hugging Face export additionally serializes the `model.z_L_init` state buffer,
which contains `1,536` values. Thus `model.safetensors` contains
`1,786,775,040` BF16 values across 131 tensors.

For `exports/dfm9_XL_step_2000000_ema_hf/model.safetensors`, this gives:

```text
BF16 tensor payload: 1,786,775,040 * 2 = 3,573,550,080 bytes
SafeTensors overhead:                         16,120 bytes
File size:                             3,573,566,200 bytes
```

The file is therefore `3.5736 GB` in decimal units or `3.3281 GiB`. An FP32
export of the same state would require about twice the tensor payload. HRM
cycles reuse parameters and therefore increase computation without adding a
separate copy of the weights for each cycle.

The input embedding and untied output LM head each contain `402,653,184`
parameters (`262,144 * 1,536`). Excluding both vocabulary-sized matrices leaves
`981,467,136` non-embedding/core parameters. If “non-embedding” excludes only
the input embedding but retains the output classifier, the count is instead
`1,384,120,320`; reports must state which convention they use because
`tie_word_embeddings` is false for this export.
