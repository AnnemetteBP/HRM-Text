---
type: Software Reference
title: '`scripts/queue_epoch_euroevals_on_free_gpus.sh`'
description: 'Part of Script Entities: `scripts/queue_epoch_euroevals_on_free_gpus.sh`.'
tags:
- scripts
- software
- catalog
- operations
status: stable
last_updated: 2026-08-11
confidence: high
part_of: /entities/scripts.md
---
# `scripts/queue_epoch_euroevals_on_free_gpus.sh`

Part of [Script Entities](/entities/scripts.md).

Added on 2026-06-12. Confidence: high for local syntax check and launch.

EuroEval-only queue for epoch checkpoints. It watches GPUs 4-7 by default and
launches one `scripts/run_euroeval_on_checkpoint.sh` job whenever a watched GPU
has no active NVIDIA compute process. This lets follow-up EuroEval jobs start
as soon as individual GPUs are freed by an earlier evaluation campaign, without
waiting for every GPU in the old campaign to finish.

Default queued jobs:

```text
checkpoints/dfm/L epoch_1..epoch_4
checkpoints/dfm4/XL-ddp epoch_1..epoch_2
```

Default runtime settings:

```text
GPUS=4,5,6,7
EUROEVAL_BATCH_SIZE=32
EUROEVAL_MAX_CONCURRENT_CALLS=32
EUROEVAL_LANGUAGES=da,en
```

DFM L results sync to W&B project `DFM L`, run id `kgnbdmwf`, run name
`dfm-L`. DFM4 XL results sync to project
`Original Plus Mixed Danish Instruction Rich L`, run id
`dfm4xlddpcleanfixed2`, run name `dfm4-XL-ddp clean corrected history v2`.

Launch command:

```bash
cd /work/dfm/HRM-Text
tmux new-session -d -s queued_dfm_euroevals \
  'cd /work/dfm/HRM-Text && scripts/queue_epoch_euroevals_on_free_gpus.sh'
```
