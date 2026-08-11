---
type: Operational Record
title: DFM5 L step150000 full eval completion and averages (2026-06-15)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5 L step150000
  full eval completion and averages (2026-06-15).'
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
# DFM5 L step150000 full eval completion and averages (2026-06-15)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5 L `step_150000` full eval completion and averages, 2026-06-15.
Confidence: high for local scheduler logs, merged artifacts, W&B client sync
output, and local W&B summary. The run completed all `188` scheduled jobs. The
attempt log had `191` rows because `3` attempts failed before retry; the final
completed job count was clean:

```text
EuroEval:      20
DFM IFEval-DA: 32
Standard:      85
DFM:           51
FINAL_MERGE_END 2026-06-15T08:02:10+02:00
```

Merge/sync logs were present and had W&B markers with no local error markers:

```text
standard merge logs: 8/8 with W&B markers
dfm merge logs:      11/11 with W&B markers
euroeval logs:       20/20 with W&B markers
```

The `step_150000` headline averages were logged to W&B project `DFM5`, run
`oti1lisg` (`dfm5-L`) with:

```bash
cd /work/dfm/HRM-Text
python scripts/log_dfm5_headline_averages.py \
  --project DFM5 \
  --run-id oti1lisg \
  --run-name dfm5-L \
  --item 150000:0.8282653854655924:logs/eval/dfm5_L_step150000_full_20260615_eurofirst_guard:logs/dfm_evals/dfm5_L_step150000_full_20260615_eurofirst_guard:logs/euroeval/dfm5_L_step150000_full_20260615_eurofirst_guard/step_150000
```

W&B client output confirmed sync; the local summary file
`wandb/run-20260615_081458-oti1lisg/files/wandb-summary.json` contains:

```text
headline_avg/danish      0.39596249125111194  count=18
headline_avg/english     0.4978719019178343   count=15
headline_avg/math_code   0.19459343879065813  count=4
headline_avg/overall     0.3628092773198681
headline_avg/epoch       0.8282653854655924
headline_avg/train_step  150000
```
