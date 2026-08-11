---
type: Technical Reference
title: Parameter and FLOP estimates for the new non-wide sizes on (2026-05-29)
description: 'Chronological record from Residual Risk: Parameter and FLOP estimates
  for the new non-wide sizes on (2026-05-29).'
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
# Parameter and FLOP estimates for the new non-wide sizes on (2026-05-29)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Parameter and FLOP estimates for the new non-wide sizes on 2026-05-29, assuming HRM `half_layers=true`, `H_cycles=2`, `L_cycles=3`, `bp_warmup_ratio=0.2`, and a 50B-token dataset iterated for 4 epochs (`200B` token presentations):

```text
XXXL:
  physical params:          5.604B
  effective forward params: 21.609B
  smoke-density training:   19.223 ZFLOPs
  worst-attention training: 24.796 ZFLOPs

XXXXL:
  physical params:          11.325B
  effective forward params: 44.292B
  smoke-density training:   39.186 ZFLOPs
  worst-attention training: 48.473 ZFLOPs
```

Here “effective forward params” means transformer-stack parameters counted once per recurrent stack call plus embeddings/LM head once; it is not additional stored parameters. “Smoke-density” uses the observed first-smoke-batch average of about `462.5` allowed attention keys per token; “worst-attention” uses `max_seq_len=4096`. Confidence: medium.

Follow-up on 2026-05-26: several attention/model support files were edited during the wall-clock window of this run, overlapping the metric dip. The run started at `2026-05-26 01:06:20` local time; the dip started around step `1161`, roughly `03:40`. File mtimes showed `models/flash_attention_prefixlm_common.py` at `03:41:09`, `models/flash_attention_prefixlm_fa3.py` at `03:42:16`, `models/flash_attention_prefixlm_mps.py` at `03:43:54`, `models/flash_attention_prefixlm_fa4.py` at `03:46:53`, `models/flash_attention_prefixlm_dense.py` at `03:47:15`, and `models/flash_attention_prefixlm_v2.py` at `03:47:59`; core model files such as `models/layers.py`, `models/transformer.py`, `models/lm_head.py`, and `models/baselines/hrm_nocarry_bp_warmup.py` had older mtimes from 2026-05-24/25. A normal running Python process does not pick up `.py` file changes after import unless code explicitly reloads modules, and this training path does not do that. The attention dispatcher lazily imports the backend on first use, but by step `1161` the XXS run had already executed many attention calls, so the active module/function objects and Metal shader source were already resident in memory. Conclusion: the overlapping file rewrites can affect later runs, but they are not a plausible cause of the active run's loss/accuracy dip unless some external process forced dynamic module reloads, for which there is no evidence. Confidence: high for file timestamps; medium-high for non-causality based on Python import semantics and inspected dispatcher code.
