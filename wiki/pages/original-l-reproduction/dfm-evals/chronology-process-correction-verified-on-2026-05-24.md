---
type: Operational Record
title: Process correction, verified on (2026-05-24)
description: 'Chronological record from dfm-evals: Process correction, verified on
  (2026-05-24).'
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
# Process correction, verified on (2026-05-24)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Process correction, verified on 2026-05-24: the original all-epoch dfm-evals wrapper advanced from epoch 1 to epoch 2 while the dedicated epoch 2 wrapper was already running. This created a duplicate epoch 2 dfm-evals process writing to the same Inspect directory and produced duplicate partial MultiWikiQA `.eval` files. The newer duplicate process was stopped, leaving the dedicated epoch 2 wrapper/server running. Confidence: high.
