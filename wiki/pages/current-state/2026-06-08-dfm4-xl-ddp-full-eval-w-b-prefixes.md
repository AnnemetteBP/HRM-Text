---
type: Operational Record
title: 2026-06-08 DFM4 XL-DDP Full Eval W&B Prefixes
description: 'Part of Current State: 2026-06-08 DFM4 XL-DDP Full Eval W&B Prefixes.'
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
# 2026-06-08 DFM4 XL-DDP Full Eval W&B Prefixes

Part of [Current State](/pages/current-state.md).

Confidence: high for local merged metrics and W&B sync output.

The full epoch-1 DFM4 XL-DDP eval backlog first logged full DFM evals under
explicit split prefixes: `dfm_eval_noema/*` and `dfm_eval_ema/*`. Existing
full-eval panels that look for plain `dfm_eval/*` therefore did not show these
values. The EMA full epoch-1 metrics were later aliased to plain `dfm_eval/*`
on W&B run `dfm4xlddpclean` in project
`Original Plus Mixed Danish Instruction Rich L`. Example synced alias:
`dfm_eval/nordjyllandnews/chrf3pp/mean = 36.61799648303162`. The explicit
`dfm_eval_ema/*` and `dfm_eval_noema/*` metrics remain present.

The same prefix issue applied to standard full evals. They were initially
logged as `eval_ema/*` and `eval_noema/*`, while existing panels look for plain
`eval/*`. The EMA full epoch-1 standard metrics were aliased to plain `eval/*`
on the same run. Example synced aliases: `eval/MATH/acc = 0.2840029`,
`eval/BoolQ/acc = 0.4523`, `eval/MMLU/acc = 0.36845`, and
`eval/GSM8k/acc = 0.1258516300227445`. The explicit split-prefix metrics remain
present.

HumanEval uses the local scorer key `verify_sanitized`, so the canonical full
metric is `dfm_eval/humaneval/verify_sanitized/accuracy`. For compatibility
with panels expecting the older `verify` scorer name, EMA full epoch-1 aliases
were also logged as `dfm_eval/humaneval/verify/*` and
`dfm_eval_ema/humaneval/verify/*`. Example:
`dfm_eval/humaneval/verify/accuracy = 0.06097560975609756`.

Epoch-2 repair, 2026-06-11. Confidence: high for local merged metrics, W&B
client output, and W&B API readback. The 2026-06-10 eval campaign completed
epoch-2 full EMA/no-EMA locally and logged explicit split prefixes, but the
plain-panel aliases such as `dfm_eval/nordjyllandnews/chrf3pp/mean` were still
showing the epoch-1 value. `scripts/backfill_dfm4_full_epoch2_plain_alias_wandb.py`
was added to read the already-merged epoch-2 EMA JSON files and log aliases
`dfm_eval_ema/* -> dfm_eval/*` and `eval_ema/* -> eval/*`, plus the HumanEval
compatibility alias `dfm_eval/humaneval/verify/*`.

The first alias attempt logged at W&B history step `163273`, below the run's
current `_step`, so it did not update the latest plain metric values. A second
attempt at explicit `--wandb-step 812076` was ignored because W&B had already
advanced to `812121`. The successful relog used `--wandb-step 900000`.

Command:

```bash
cd /work/dfm/HRM-Text
python scripts/backfill_dfm4_full_epoch2_plain_alias_wandb.py \
  --standard-root logs/eval/dfm4_XL_ddp_eval_campaign_20260610/full_ema/epoch_2 \
  --dfm-root logs/dfm_evals/dfm4_XL_ddp_eval_campaign_20260610/full_ema/epoch_2 \
  --wandb-step 900000
```

API readback after the successful relog:

```text
_step = 900000
dfm_eval/epoch = 2
dfm_eval/nordjyllandnews/chrf3pp/mean = 36.57873558881677
dfm_eval/nordjyllandnews/chrf3pp/stderr = 0.350586469648215
dfm_eval/humaneval/verify/accuracy = 0.054878048780487805
eval/epoch = 2
eval/MATH/acc = 0.28720693999999997
```

No-EMA comparison run, 2026-06-11. Confidence: high for local merged metrics,
W&B client output, and W&B API readback. A new W&B run was created for comparing
full no-EMA evals separately from the EMA/full run:

```text
project: Original Plus Mixed Danish Instruction Rich L
run id:  dfm4xlddpnoema
name:    dfm4-XL-ddp-noema
```

The run was backfilled from stored merged metrics only; no inference was rerun.
It aliases `eval_noema/* -> eval/*` and `dfm_eval_noema/* -> dfm_eval/*` for
epoch 1 and epoch 2, plus the HumanEval compatibility alias
`dfm_eval/humaneval/verify/*`.

Command:

```bash
cd /work/dfm/HRM-Text
python scripts/backfill_dfm4_full_noema_new_run_wandb.py \
  --eval 1:logs/eval/dfm4_XL_ddp_noema_full_epoch1_20260608/epoch_1:logs/dfm_evals/dfm4_XL_ddp_noema_full_epoch1_20260608/epoch_1 \
  --eval 2:logs/eval/dfm4_XL_ddp_eval_campaign_20260610/full_noema/epoch_2:logs/dfm_evals/dfm4_XL_ddp_eval_campaign_20260610/full_noema/epoch_2 \
  --project "Original Plus Mixed Danish Instruction Rich L" \
  --run-id dfm4xlddpnoema \
  --run-name dfm4-XL-ddp-noema
```

API readback:

```text
epoch 1:
  eval/MATH/acc = 0.23919526000000002
  dfm_eval/nordjyllandnews/chrf3pp/mean = 36.57039389543406
  dfm_eval/humaneval/verify/accuracy = 0.018292682926829267
epoch 2:
  eval/MATH/acc = 0.30840231999999995
  dfm_eval/nordjyllandnews/chrf3pp/mean = 36.634404429441005
  dfm_eval/humaneval/verify/accuracy = 0.17682926829268292
```
