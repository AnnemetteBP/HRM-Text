---
type: Operational Record
title: DFM5 XXS DDP health check at about 65K (2026-06-14)
description: 'Chronological record from DFM5 XXS Step-50K Full Eval: DFM5 XXS DDP
  health check at about 65K (2026-06-14).'
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
# DFM5 XXS DDP health check at about 65K (2026-06-14)

Part of [DFM5 XXS Step-50K Full Eval](/pages/current-state/dfm5-xxs-step-50k-full-eval.md).

DFM5 XXS DDP health check at about 65K, 2026-06-14. Confidence: high for W&B
API history and local checkpoint inspection. The DDP run `pqc9g81u` was
`running`, with local regular checkpoints through `step_60000` and an
ephemeral checkpoint at `step_65000`. Matched W&B history against the FSDP run
`2tv9u438` over the shared early window:

```text
bin          fsdp_loss fsdp_acc  ddp_loss ddp_acc  loss_delta  acc_delta
0-1000        7.5082   0.1587    7.4919   0.1587   -0.0164    +0.0000
1000-2000     4.7824   0.2771    4.7953   0.2737   +0.0129    -0.0034
2000-5000     3.9046   0.3658    3.9813   0.3515   +0.0767    -0.0144
5000-10000    3.3444   0.4367    3.4739   0.4161   +0.1295    -0.0207
10000-20000   2.9803   0.4825    3.0299   0.4755   +0.0496    -0.0070
20000-30000   2.8124   0.5023    2.8576   0.4960   +0.0452    -0.0062
30000-40000   2.7384   0.5111    2.7687   0.5064   +0.0304    -0.0047
40000-50000   2.7032   0.5152    2.7173   0.5123   +0.0141    -0.0028
50000-60000   2.7081   0.5140    2.6557   0.5200   -0.0524    +0.0060
60000-70000   2.3528   0.5539    2.3904   0.5497   +0.0375    -0.0043
```

Latest rows in the scan:

```text
FSDP step_70000: loss=2.3034 acc=0.5591 exact=0.0496 bp_steps=3
DDP  step_64995: loss=2.3030 acc=0.5528 exact=0.0378 bp_steps=3
```

Interpretation: DDP is healthy and close to FSDP. The initial FSDP advantage
shrinks substantially after 30K; DDP is briefly ahead in the 50K-60K bin and
slightly behind again in the 60K-70K bin. This looks like ordinary trajectory
noise plus implementation differences, not a failing DDP run. Tail throughput
from the W&B scan was lower for DDP (`~7.7` steps/s vs `~13.5` for the sampled
FSDP tail), but that DDP window overlapped the full `step_50000` eval running
on the same GPUs, so it should not be read as clean training throughput.
