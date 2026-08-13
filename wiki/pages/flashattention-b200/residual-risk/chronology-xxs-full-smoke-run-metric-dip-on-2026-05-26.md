---
type: Technical Reference
title: XXS full smoke run metric dip on (2026-05-26)
description: 'Chronological record from Residual Risk: XXS full smoke run metric dip
  on (2026-05-26).'
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
# XXS full smoke run metric dip on (2026-05-26)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

XXS full smoke run metric dip on 2026-05-26:

Run directory:

```text
wandb/run-20260526_010620-pe62hvad
```

Config:

```text
arch/size@arch=XXS
global_batch_size=16384
gradient_accumulation_steps=4
local_microbatch_size=4096
epochs=1
log_interval=1
HRM_ENABLE_EXPERIMENTAL_MPS_KERNEL=1
```

Observed event:

```text
steps 1120-1160:
  mean train/loss:     4.867869
  mean train/accuracy: 0.309116

steps 1161-1200:
  mean train/loss:     7.881740
  mean train/accuracy: 0.174512

steps 1201-1220:
  mean train/loss:     7.367802
  mean train/accuracy: 0.168310
```

The change starts gradually at step `1161`: loss rises from about `4.85-5.08` to `5.23`, then reaches `7-8.7` by steps `1167-1180`; token accuracy falls from about `0.30-0.32` to `0.14-0.18`. `train/exact_accuracy` stayed `0`, `bp_steps` stayed `5`, and `train/lr` stayed `2.5e-4`, so this was not caused by LR scheduling or recurrence warmup. Step runtime stayed in the same general range, with no local W&B error/warning at the transition.

Dataset reconstruction from `data/sampled_original_sapient_partial_smoke` showed no top-level source switch across the dip. The windows are all dominated by the same SYNTH smoke subset:

```text
steps 1120-1160:
  SYNTH rows: 1681
  UNKNOWN rows from reconstructed range mapping: 68
  top tasks: SYNTH__synth_230.parquet, SYNTH__synth_175.parquet, SYNTH__synth_176.parquet

steps 1161-1200:
  SYNTH rows: 1663
  UNKNOWN rows from reconstructed range mapping: 62
  top tasks: SYNTH__synth_176.parquet, SYNTH__synth_230.parquet, SYNTH__synth_175.parquet
```

Decoded rows around the dip include harder long-form synthetic writing/legal/history examples, including near-max-length responses such as a Hellenistic papyrus-style creative fragment (`resp_len=3917`) at step `1168`. Superseded interpretation: this initially looked like a data/batch difficulty region in the smoke sample, not a kernel, optimizer, LR, or W&B failure. Confidence: high for the metric extraction and config; low for the original data-difficulty interpretation after dense-vs-custom comparison below.
