---
type: Operational Record
title: DFM5 XXS FSDP bf16-parameter run (2026-06-14)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5 XXS FSDP
  bf16-parameter run (2026-06-14).'
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
# DFM5 XXS FSDP bf16-parameter run (2026-06-14)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5 XXS FSDP bf16-parameter run, 2026-06-14. Confidence: high for W&B API
history; medium for causal interpretation. The run `4ch8y3e8`
(`dfm5-XXS-fsdp-bf16`, `fsdp_params_precision=bf16`) shows a substantially
worse early training curve than the fp32-parameter FSDP baseline `2tv9u438`
and the fp32-parameter DDP run `pqc9g81u`. W&B history bin means:

```text
bin          fsdp_fp32 loss/acc   ddp_fp32 loss/acc   fsdp_bf16 loss/acc
0-1000       7.5082 / 0.1587      7.4919 / 0.1587     9.4289 / 0.1010
1000-2000    4.7824 / 0.2771      4.7953 / 0.2737     5.9497 / 0.2098
2000-5000    3.9038 / 0.3659      3.9806 / 0.3515     4.7019 / 0.2916
5000-10000   3.3444 / 0.4367      3.4738 / 0.4161     4.3216 / 0.3320
10000-20000  2.9804 / 0.4825      3.0299 / 0.4755     4.2301 / 0.3438*
```

`*` The bf16 run only had 289 logged rows in the 10K-20K bin at inspection
time, through `_step=11435`. Because this run uses persistent bf16 model
parameters and bf16 AdamATan2 moment buffers (`zeros_like(p)` follows parameter
dtype), while only EMA is forced to fp32, the most likely explanation is
optimizer/update precision degradation rather than an EMA evaluation issue.
Use `fsdp_params_precision=fp32` for comparable FSDP/ DDP training curves unless
a separate fp32-master-parameter or fp32-optimizer-state path is implemented.
