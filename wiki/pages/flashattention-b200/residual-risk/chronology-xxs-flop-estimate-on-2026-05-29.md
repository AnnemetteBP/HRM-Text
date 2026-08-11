---
type: Technical Reference
title: XXS FLOP estimate on (2026-05-29)
description: 'Chronological record from Residual Risk: XXS FLOP estimate on (2026-05-29).'
tags:
- flashattention
- b200
- cuda
- performance
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/flashattention-b200/residual-risk.md
---
# XXS FLOP estimate on (2026-05-29)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

XXS FLOP estimate on 2026-05-29: with `arch/size@arch=XXS`, HRM uses `hidden_size=256`, `num_heads=2`, `head_dim=128`, `n_layers=6`, and `half_layers=true`, so the H and L modules each have 3 transformer layers. `H_cycles=2`, `L_cycles=3`, for 8 recurrent transformer-stack calls per forward pass. At `global_batch_size=16384`, linear/LM-head FLOPs are approximately:

```text
bp_steps=2: 2.73e12 FLOPs before attention
bp_steps=5: 3.27e12 FLOPs before attention
```

For the first smoke optimizer step (`gradient_accumulation_steps=4`), the actual packed microbatches contained 15,882 tokens and 7,345,463 allowed PrefixLM query-key pairs, about 462 attended keys/token. Scaling to the nominal 16,384-token step gives an attention term of roughly `0.28e12` FLOPs at `bp_steps=2` and `0.42e12` FLOPs at `bp_steps=5`. Total expected forward+backward FLOPs per XXS optimizer step are therefore roughly:

```text
bp_steps=2: ~3.0e12 FLOPs
bp_steps=3: ~3.24e12 FLOPs
bp_steps=4: ~3.47e12 FLOPs
bp_steps=5: ~3.69e12 FLOPs
```

The simpler dense-transformer back-of-envelope `6 * num_params * tokens` with `num_params=39,059,456` and `tokens=16,384` gives `3.84e12` FLOPs/step, but it overcounts embedding lookup work and does not model HRM recurrence explicitly. Confidence: medium; exact attention FLOPs vary with packing/sequence lengths.

General HRM FLOP formula used for this estimate:

```text
T       = supervised/packed tokens per optimizer step, usually global_batch_size
A       = allowed PrefixLM query-key pairs per optimizer step, before multiplying by heads
D       = hidden_size
h       = num_heads
d       = head_dim = D / h
hk      = num_key_value_heads, currently h
I       = intermediate_size
V       = vocab_size
NH, NL  = number of transformer layers in the H and L stacks
HC, LC  = H_cycles and L_cycles
b       = bp_steps
Hbp     = min(HC, max(0, b - 1))
Lbp     = min(HC * LC, max(0, b - Hbp))

QKVout          = (2h + 2hk) * d
F_linear_fwd    = T * (2D * QKVout + 2D^2 + 6DI)
F_linear_bwd    = 2 * F_linear_fwd
F_attn_fwd      = 4h d A
F_attn_bwd      = 10h d A + 2h d T
F_layer_fwd     = F_linear_fwd + F_attn_fwd
F_layer_bwd     = F_linear_bwd + F_attn_bwd
F_recurrent     = (HC * NH + HC * LC * NL) * F_layer_fwd
                + (Hbp * NH + Lbp * NL) * F_layer_bwd
F_lm_head       = 6T D V
F_step          = F_recurrent + F_lm_head
```

This counts multiply-add matmul/attention FLOPs and intentionally excludes most elementwise ops; using `A = T * max_seq_len` gives a conservative attention upper bound. Confidence: medium-high for matmul/attention accounting; low for exact hardware instruction count.
