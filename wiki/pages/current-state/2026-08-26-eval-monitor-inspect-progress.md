---
type: Technical Reference
title: Eval Monitor Live Progress Sources
description: Verified progress and ETA sources used by the evaluation scheduler monitor.
tags: [evaluation, scheduler, monitoring, inspect, eta]
status: stable
last_updated: 2026-08-26
confidence: high
---
# Eval Monitor Live Progress Sources

Update, 2026-08-26. The scheduler monitor now uses evaluator-native progress
sources before fallbacks:

- Standard eval and batched EuroEval tqdm output supplies the completed count,
  total, and rolling ETA. This avoids treating vLLM startup time as generation
  time.
- DFM evals use Inspect's live journaled `.eval` ZIP. `_journal/start.json`
  provides the exact dataset sample count, and unique `samples/*.json` members
  provide the completed count while `dfm-evals.log` is still buffered.
- EuroEval's existing pass/sample parser remains responsible for multi-pass and
  multi-stage tasks. Server request counts remain a fallback when no evaluator
  progress artifact exists.

Inspect rewrites the ZIP central directory while a task runs. A concurrent read
can therefore briefly raise `BadZipFile`; the monitor catches that condition
and uses its older fallbacks until the next 30-second refresh. Once all sample
members are present, the monitor reports `finalizing` rather than claiming that
the active job is fully done, because scoring and EEE export may remain.

The behavior was verified live against the DFM9 XXL-32 step-20K campaign:
DFM IFEval changed from `progress unknown` to exact values such as
`samples 15/17` with an ETA, while EuroEval IFEval retained exact `X/541`
progress and its rolling ETA. Focused scheduler tests cover tqdm ETA parsing,
live Inspect sample counting, and the finalization state.
