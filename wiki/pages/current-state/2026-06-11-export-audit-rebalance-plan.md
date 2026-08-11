---
type: Operational Record
title: 2026-06-11 Export Audit Rebalance Plan
description: 'Part of Current State: 2026-06-11 Export Audit Rebalance Plan.'
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
# 2026-06-11 Export Audit Rebalance Plan

Part of [Current State](/pages/current-state.md).

Confidence: high for local scripts and active tmux sessions; medium until the
first rebalance round completes.

The eight non-synthetic export audits are running in tmux session
`export_audits_8gpu`. The initial full-everything estimate was too long for
full audit of all rows with Gemma 4 31B, so the working target was changed to
`100M` accepted tokens per dataset. Average token estimates used by the
controller are:

```text
common-pile-denoising:                    398.1 tokens/accepted row
common-pile-paragraph-reordering:         818.3
common-pile-prefix-continuation:          207.5
common-pile-span-filling:                 397.8
danish-dynaword-denoising:               1898.4
danish-dynaword-paragraph-reordering:     916.5
danish-dynaword-prefix-continuation:      954.3
danish-dynaword-span-filling:            1845.7
```

The active rebalance watcher is tmux session `export_audit_rebalance_watch`:

```bash
cd /work/dfm/HRM-Text
python scripts/rebalance_export_audits.py watch \
  --target-tokens 100000000 \
  --interval-seconds 300 \
  --gpus 0,1,2,3,4,5,6,7
```

When at least one dataset reaches the target and at least one remains below
target, the watcher stops the current monolithic audit session and relaunches
only unfinished datasets as stable hash shards with `--skip-audit` pointing at
previous audit files. This avoids the unsafe pattern of killing one child
worker under `scripts/run_export_audits_8gpu_vllm.sh`, whose cleanup trap owns
all vLLM servers.

The older `export_audit_filter_watch` was stopped because it only filters
`audit_full`. After rebalance shards exist, final filtering should use all
audit roots:

```bash
cd /work/dfm/HRM-Text
python scripts/filter_all_export_audits.py
```
