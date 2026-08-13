---
type: Operational Record
title: DFM5 L step100000 full eval completion (2026-06-14)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5 L step100000
  full eval completion (2026-06-14).'
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
# DFM5 L step100000 full eval completion (2026-06-14)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5 L `step_100000` full eval completion, 2026-06-14. Confidence: high for
local scheduler logs, merged artifacts, and W&B client sync output. The guarded
EuroEval-first run completed all `188` attempts with `status=0` and `oom=0`:

```text
EuroEval:      20
DFM IFEval-DA: 32
Standard:      85
DFM:           51
FINAL_MERGE_START  2026-06-14T22:42:30+02:00
FINAL_MERGE_END    2026-06-14T22:43:46+02:00
```

Merge/sync logs were present and had W&B markers with no local error markers:

```text
standard merge logs: 8/8 with W&B markers
dfm merge logs:      11/11 with W&B markers
euroeval logs:       20/20 with W&B markers
```

The `step_100000` headline averages were logged to W&B project `DFM5`, run
`oti1lisg` (`dfm5-L`) with:

```bash
cd /work/dfm/HRM-Text
python scripts/log_dfm5_headline_averages.py \
  --project DFM5 \
  --run-id oti1lisg \
  --run-name dfm5-L \
  --item 100000:0.5521769236437283:logs/eval/dfm5_L_step100000_full_20260614_eurofirst_guard:logs/dfm_evals/dfm5_L_step100000_full_20260614_eurofirst_guard:logs/euroeval/dfm5_L_step100000_full_20260614_eurofirst_guard/step_100000
```

W&B client output confirmed sync and summary update for:

```text
headline_avg/danish      0.3481170617668168   count=18
headline_avg/english     0.4285458041771221   count=15
headline_avg/math_code   0.14095378072745426  count=4
headline_avg/overall     0.30587221555713107
headline_avg/epoch       0.5521769236437283
headline_avg/train_step  100000
```
