---
type: Operational Record
title: Standard eval W&B sync, verified on (2026-05-25)
description: 'Chronological record from dfm-evals: Standard eval W&B sync, verified
  on (2026-05-25).'
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
# Standard eval W&B sync, verified on (2026-05-25)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Standard eval W&B sync, verified on 2026-05-25. Confidence: high.

The current original+mixed L run's standard HRM evals are logged under the
`eval/...` prefix, separate from the Danish `dfm_eval/...` suite. Because the
standard eval jobs were split across per-task logs and sharded MATH logs,
`scripts/log_original_plus_mixed_standard_eval_to_wandb.py` composes exactly:

```text
epoch 1: ARC, BoolQ, DROP, GSM8k, HellaSwag, MATH, MMLU, Winogrande
epoch 2: ARC, BoolQ, DROP, GSM8k, HellaSwag, MMLU, Winogrande
```

CP2 MATH is intentionally omitted until all epoch-2 MATH shards complete and
are merged.

Command used:

```bash
cd /work/dfm/HRM-Text
python scripts/log_original_plus_mixed_standard_eval_to_wandb.py
```

The sidecar W&B sync reported success for run `es1od1in`, but the active
training run again showed the known live-run sidecar issue where remote summary
keys did not appear through the public API immediately. The same parsed metrics
were therefore patched into the remote run summary through the W&B API. A
post-patch API check returned `777` `eval/*` summary keys, with:

```text
eval/standard_eval_last_synced_epoch: 2
eval/standard_eval_cp2_math_synced: False
eval/MATH/acc/epoch_1: 0.3658
eval/MATH/acc/epoch_2: <missing>
eval/GSM8k/acc/epoch_2: 0.7301
eval/Winogrande/acc/epoch_2: 0.5951
```

At that check, the only active standard eval work left was CP2 MATH shard 6
and shard 7. Confidence: high.
