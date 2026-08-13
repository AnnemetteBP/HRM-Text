---
type: Operational Record
title: Current-run incremental watcher, verified on (2026-05-24)
description: 'Chronological record from dfm-evals: Current-run incremental watcher,
  verified on (2026-05-24).'
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
# Current-run incremental watcher, verified on (2026-05-24)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Current-run incremental watcher, verified on 2026-05-24: because the already-running epoch 2 wrapper predates the incremental-sync script change, a bounded watcher was started manually. It writes to `logs/dfm_evals/original_sapient_L/epoch_2/manual_incremental_sync_current`, has marker files for already-synced completed epoch 2 logs, and exits after the active epoch 2 eval process exits. Its purpose is to sync the remaining epoch 2 MultiWikiQA result if it completes. Confidence: high.
