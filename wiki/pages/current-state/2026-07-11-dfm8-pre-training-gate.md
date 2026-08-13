---
type: Operational Record
title: 2026-07-11 DFM8 Pre-Training Gate
description: 'Part of Current State: 2026-07-11 DFM8 Pre-Training Gate.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# 2026-07-11 DFM8 Pre-Training Gate

Part of [Current State](/pages/current-state.md).

Confidence: high for local request preparation and process inspection.

Do **not** restart DFM8 training until the prepared Danish OpenHermes
derivative generation/audit has been run, inspected, integrated into
`data/tokenized_dfm8`, and DFM8 has been resampled.

The current `dfm8-synthetic-*` generation is still active and must not be
disturbed. The Danish OpenHermes job has only been prepared offline:

```text
package:       dfm8_openhermes_da/
requests:      data/dfm8_openhermes_da_synthetic
upload root:   export-upload-dfm8-openhermes-da
runner:        dfm8_openhermes_da/scripts/run_openhermes_da_8gpu.sh
default ports: 8600-8607
prepared rows: 1,001,551
request shards: 512
```

The runner has a safety guard and refuses to start while the active
`dfm8_synthetic.cli generate|audit` or
`run_dfm8_targeted_synthetic_8gpu.sh` processes are present.

When GPUs are free, run from `/work/dfm/HRM-Text`:

```bash
CONCURRENCY=128 \
GPU_MEMORY_UTILIZATION=0.7 \
MAX_NUM_SEQS=128 \
bash dfm8_openhermes_da/scripts/run_openhermes_da_8gpu.sh
```

After it finishes, inspect row counts/examples, tokenize the accepted upload
folder with the Gemma4 chat-template path, rebuild `data/tokenized_dfm8`,
resample `data/sampled_dfm8`, and only then restart training.
