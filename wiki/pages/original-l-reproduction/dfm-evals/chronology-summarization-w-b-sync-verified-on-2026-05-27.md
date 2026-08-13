---
type: Operational Record
title: Summarization W&B sync, verified on (2026-05-27)
description: 'Chronological record from dfm-evals: Summarization W&B sync, verified
  on (2026-05-27).'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction/dfm-evals.md
---
# Summarization W&B sync, verified on (2026-05-27)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Summarization W&B sync, verified on 2026-05-27. Confidence: high for W&B upload
logs and original clean summary visibility; medium for active-run summary
visibility because the live original+mixed training run has previously
overwritten sidecar summaries.

`scripts/log_summarization_evals_to_wandb.py` parses
`logs/eval/summarization_all_checkpoints_20260527T085348` and logs
`GovReport`/`NordjyllandNews` metrics under the standard `eval/*` prefix with
`eval/epoch` as the step metric. It maps:

```text
original_sapient -> project "Original Plus Mixed Danish Instruction Rich L", run "origLclean"
original_plus_mixed_danish_instruction_rich -> same project, run "es1od1in"
```

The sync command was:

```bash
cd /work/dfm/HRM-Text
python scripts/log_summarization_evals_to_wandb.py \
  2>&1 | tee logs/eval/summarization_all_checkpoints_20260527T085348/wandb_sync.log
```

W&B reported successful uploads for both runs. The original clean run API
summary shows `eval/summarization_last_synced_epoch=4`. The active
original+mixed sidecar run reported upload success for `history_lines=3` at
`status="200 OK"`, but its public summary did not retain the summarization keys,
matching the known active-run summary overwrite behavior.
