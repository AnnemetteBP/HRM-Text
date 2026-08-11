---
type: Operational Record
title: EMA dfm-eval retry status (2026-06-07)
description: 'Chronological record from DFM L CP2 Evaluation Queue: EMA dfm-eval retry
  status (2026-06-07).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm-l-cp2-evaluation-queue.md
---
# EMA dfm-eval retry status (2026-06-07)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

EMA dfm-eval retry status, 2026-06-07. Confidence: high for local process logs,
telemetry, local merged JSON, and W&B sync logs. Three `step_400000` EMA dfm-evals OOMed and were manually
recorded in:

```text
logs/eval/dfm4_XL_ddp_ema_lite_400k_20260606_tmux/step_400000/eval_attempts.tsv
```

Recorded OOM attempts:

```text
IFEval-DA        batch 8, GPU0, free-before 16557 MiB, OOM
GovReport        batch 4, GPU2, free-before  8999 MiB, OOM
WMT24++ en-da    batch 4, GPU7, free-before  7399 MiB, OOM
GovReport        batch 2, GPU2, free-before  8999 MiB, OOM
WMT24++ en-da    batch 2, GPU7, free-before  7399 MiB, OOM
WMT24++ en-da    batch 2, GPU2, free-before  8999 MiB, OOM
```

Final successful retries:

```text
IFEval-DA        batch 4 on GPU0
GovReport        batch 2 on GPU0
WMT24++ en-da    batch 1 on GPU2
```

GovReport batch 2 succeeded on GPU0 because it had about `16.6 GiB` free above
training at launch. WMT24++ en-da was forced to batch 1 for the final pass after
batch 2 had failed on low-headroom GPUs; that retry completed at
`2026-06-07T12:47:40+02:00`. The three EMA DFM-lite shard outputs were merged
and synced to W&B run `dfm4xlddpclean` under `lite_dfm_eval_ema/*` at
`lite_dfm_eval_ema/epoch = 1.092162098698`:

```text
IFEval-DA        17 samples
GovReport        61 samples
WMT24++ en-da   120 samples
```

Merged outputs:

```text
logs/dfm_evals/dfm4_XL_ddp_ema_lite_400k_20260606_tmux/step_400000/merged_ifeval_da_metrics.json
logs/dfm_evals/dfm4_XL_ddp_ema_lite_400k_20260606_tmux/step_400000/govreport/merged_metrics.json
logs/dfm_evals/dfm4_XL_ddp_ema_lite_400k_20260606_tmux/step_400000/wmt24pp_en_da/merged_metrics.json
```
