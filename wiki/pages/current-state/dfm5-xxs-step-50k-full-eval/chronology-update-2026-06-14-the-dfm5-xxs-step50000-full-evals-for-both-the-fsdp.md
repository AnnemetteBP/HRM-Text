---
type: Operational Record
title: 'Update 2026-06-14: The DFM5 XXS step50000 full evals for both the FSDP'
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Update 2026-06-14:
  The DFM5 XXS step50000 full evals for both the FSDP.'
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
# Update 2026-06-14: The DFM5 XXS step50000 full evals for both the FSDP

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Update, 2026-06-14. Confidence: high. The DFM5 XXS `step_50000` full evals
for both the FSDP run and the DDP run used the default EMA checkpoint weights.
`scripts/schedule_checkpoint_evals.sh` defaults `NO_EMA=0`; standard evals
only add `ckpt_use_ema=false` when `NO_EMA=1`, and DFM/EuroEval server launch
paths only add `--no-ema` when `NO_EMA=1`. Focused searches of the relevant
50K launch/eval logs found no `NO_EMA=1`, `ckpt_use_ema=false`, or `--no-ema`
override. Therefore the observed 50K FSDP-vs-DDP full-eval differences should
be interpreted as EMA-vs-EMA, not EMA-vs-raw or raw-vs-raw.

DFM5 XXS-DDP EMA sanity check, 2026-06-14. Confidence: high for inspected
config and checkpoint tensors; medium for metric interpretation. The DFM5
XXS-DDP W&B config for run id `pqc9g81u` records `distributed_strategy=ddp`,
`checkpoint_format=unsharded`, `ddp_params_precision=fp32`,
`fwd_bwd_dtype=bfloat16`, and `ema=0.9999`. This means it is not using the old
broken low-precision EMA-shadow setup from early DFM4 XL-DDP experiments.
Inspecting `checkpoints/dfm5/XXS-ddp/unsharded_step_50000.pt`,
`unsharded_step_100000.pt`, and `unsharded_step_150000.pt` showed all 26
optimizer `param_ema` tensors are `torch.float32`. Mean absolute
EMA-current-weight deltas were nonzero and decreased over time:
`0.00946` at 50K, `0.00677` at 100K, and `0.00465` at 150K, which is
consistent with a working EMA update. The unsharded inference loader applies
EMA directly from the optimizer state into the model state when
`ckpt_use_ema=True`. A key-coverage check for `step_50000` found 27 model
tensors and 26 EMA tensors; the only model tensor without EMA is
`model.zL_init`, which is an `nn.Buffer`, not an optimizer parameter. Current
evidence does not point to a DDP EMA storage/load bug for DFM5 XXS-DDP; a
remaining possibility is ordinary EMA lag or model/task noise, which should be
tested by paired EMA vs no-EMA evals on the same checkpoints.
