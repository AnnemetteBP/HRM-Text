---
type: Operational Record
title: Early DFM5 XXS FSDP-vs-DDP training comparison (2026-06-14)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: Early DFM5 XXS
  FSDP-vs-DDP training comparison (2026-06-14).'
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
# Early DFM5 XXS FSDP-vs-DDP training comparison (2026-06-14)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

Early DFM5 XXS FSDP-vs-DDP training comparison, 2026-06-14. Confidence:
high for W&B API history values; medium for interpretation because the DDP run
was started from step 0 rather than from a converted FSDP checkpoint, so
initialization differs.

Runs compared:

```text
FSDP: project DFM5, run_id 2tv9u438, run_name dfm5-XXS, checkpoint_path checkpoints/dfm5/XXS
DDP:  project DFM5, run_id pqc9g81u, run_name dfm5-XXS-ddp, checkpoint_path checkpoints/dfm5/XXS-ddp
```

W&B dense history scan over the overlapping early region found:

```text
bin          fsdp_loss fsdp_acc  ddp_loss ddp_acc  loss_delta  acc_delta
0-1000        7.5082   0.1587    7.4919   0.1587   -0.0164    +0.0000
1000-2000     4.7858   0.2768    4.7986   0.2735   +0.0129    -0.0034
2000-5000     3.9048   0.3658    3.9815   0.3514   +0.0767    -0.0144
5000-10000    3.3445   0.4367    3.4740   0.4160   +0.1295    -0.0207
10000-15000   3.0544   0.4736    3.1153   0.4647   +0.0609    -0.0089
15000-20000   2.9061   0.4913    2.9444   0.4862   +0.0383    -0.0051
20000-25000   2.8366   0.4992    2.8848   0.4926   +0.0483    -0.0066
25000-30000   2.7886   0.5053    2.8348   0.4990   +0.0461    -0.0063
```

Throughput from the same W&B sample tail:

```text
FSDP tail 29010->30000: about 22.6 steps/s
DDP tail  28380->29370: about 25.2 steps/s
```

Interpretation: DDP is slightly but consistently behind FSDP on early
training metrics after the first few thousand steps, with roughly `0.04-0.13`
higher loss and `0.5-2.1` percentage points lower token accuracy in the
overlap. This is not a failure pattern: no NaNs, loss is falling, accuracy is
rising, and the DDP tail reaches about `0.505` token accuracy near `29K`
steps. Because the two runs did not start from identical weights, this should
not be treated as proof that DDP trains worse. For a fair optimizer/distributed
strategy comparison, resume DDP from a converted FSDP checkpoint and compare
matched continuation windows.
