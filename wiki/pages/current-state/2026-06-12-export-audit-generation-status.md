---
type: Operational Record
title: 2026-06-12 Export Audit Generation Status
description: 'Part of Current State: 2026-06-12 Export Audit Generation Status.'
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
# 2026-06-12 Export Audit Generation Status

Part of [Current State](/pages/current-state.md).

Confidence: high for local status command output and live process inspection.

At `2026-06-12 14:16 +0200`, the accepted-token audit status for the
post-training export datasets was:

```text
common-pile-denoising:                   100.1M / 100.0M done
common-pile-prefix-continuation:          76.9M / 100.0M open
common-pile-span-filling:                 92.0M / 100.0M open
danish-dynaword-paragraph-reordering:     50.7M /  50.0M done
```

The manual GPU layout at that point was:

```text
GPU0: common-pile-span-filling shard 1/2
GPU1: common-pile-denoising shard 0/3
GPU2: common-pile-span-filling shard 0/2
GPU3: common-pile-prefix-continuation shard 0/1
GPU6: common-pile-denoising shard 1/3
GPU7: common-pile-denoising shard 2/3
```

`common-pile-denoising` had crossed the cap, but the three manual audit clients
were still live at inspection time. The user explicitly reserved GPUs 4 and 5
for another thread; this thread should not manage those processes.

Update at `2026-06-12 14:24 +0200`: the denoising audit clients on GPUs 1, 6,
and 7 were stopped after denoising reached `101.3M / 100.0M` accepted tokens.
`common-pile-span-filling` was restarted under tmux session
`export_span_gpus01267` as five shards using the partial prior span audits as
skip inputs:

```text
GPU0: common-pile-span-filling shard 0/5, port 8903
GPU1: common-pile-span-filling shard 1/5, port 8900
GPU2: common-pile-span-filling shard 2/5, port 8902
GPU6: common-pile-span-filling shard 3/5, port 8916
GPU7: common-pile-span-filling shard 4/5, port 8917
```

`common-pile-prefix-continuation` continued on GPU3.

Update at `2026-06-12 14:47 +0200`: after
`common-pile-span-filling` crossed the cap (`100.9M / 100.0M`), the five span
audit clients and the old single prefix client were stopped. Prefix was
restarted under tmux session `export_prefix_gpus012367` as six shards:

```text
GPU0: common-pile-prefix-continuation shard 0/6, port 8903
GPU1: common-pile-prefix-continuation shard 1/6, port 8900
GPU2: common-pile-prefix-continuation shard 2/6, port 8902
GPU3: common-pile-prefix-continuation shard 3/6, port 8901
GPU6: common-pile-prefix-continuation shard 4/6, port 8916
GPU7: common-pile-prefix-continuation shard 5/6, port 8917
```

The prefix aggregate was `78.2M / 100.0M` accepted tokens immediately after the
reassignment. GPUs 4 and 5 remained reserved for other work and were not
managed by this thread.

Final stop at `2026-06-12 18:05 +0200`: the six prefix audit clients were
stopped after `common-pile-prefix-continuation` reached
`128.6M / 100.0M` accepted tokens. The aggregate accepted-token total across
the eight audited export datasets was `778.6M`. The tmux launcher session
`export_prefix_gpus012367` had exited after the clients were killed.
