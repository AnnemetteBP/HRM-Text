---
type: Knowledge Collection
title: dfm-evals
description: 'Part of Original L Reproduction: dfm-evals.'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/original-l-reproduction.md
collection_type: Experiment Record
---
# dfm-evals

Part of [Original L Reproduction](/pages/original-l-reproduction.md).

Prepared on 2026-05-24, not yet run end-to-end: `dfm-evals` was cloned from `https://github.com/danish-foundation-models/dfm-evals`, and three local scripts were added:

```text
scripts/hrm_openai_server.py
scripts/run_dfm_evals_on_checkpoints.sh
scripts/log_dfm_evals_to_wandb.py
```

The wrapper starts a local OpenAI-compatible HTTP shim for each checkpoint, runs dfm-evals through Inspect, exports Inspect logs to Every Eval Ever JSON, and logs numeric results to W&B under `dfm_eval/...` instead of `eval/...`.

The default suite is `config/dfm_evals_hrm.yaml:hrm_danish`, which includes Danish citizen tests, DaLA, GEC-DaLA, WMT24++ English-to-Danish, and MultiWikiQA. It intentionally avoids the upstream `fundamentals` suite's judge-only and long-context RULER tasks because the original HRM L checkpoints use a 4096-token context. Confidence: medium until a full run completes.

## Chronological Records

### Runtime Update 2026-05-24

[Open the chronological record](dfm-evals/chronology-runtime-update-2026-05-24.md).

### Superseded on (2026-05-24)

[Open the chronological record](dfm-evals/chronology-superseded-on-2026-05-24.md).

### Parallel dfm-evals launch, verified on (2026-05-24)

[Open the chronological record](dfm-evals/chronology-parallel-dfm-evals-launch-verified-on-2026-05-24.md).

### Manual dfm-evals sync, verified on (2026-05-24)

[Open the chronological record](dfm-evals/chronology-manual-dfm-evals-sync-verified-on-2026-05-24.md).

### Runtime Update 2026-05-24

[Open the chronological record](dfm-evals/chronology-runtime-update-2026-05-24-2.md).

### Second manual dfm-evals sync, verified on (2026-05-24)

[Open the chronological record](dfm-evals/chronology-second-manual-dfm-evals-sync-verified-on-2026-05-24.md).

### Third manual dfm-evals sync, verified on (2026-05-24)

[Open the chronological record](dfm-evals/chronology-third-manual-dfm-evals-sync-verified-on-2026-05-24.md).

### Incremental sync update, verified locally on (2026-05-24)

[Open the chronological record](dfm-evals/chronology-incremental-sync-update-verified-locally-on-2026-05-24.md).

### Process correction, verified on (2026-05-24)

[Open the chronological record](dfm-evals/chronology-process-correction-verified-on-2026-05-24.md).

### Current-run incremental watcher, verified on (2026-05-24)

[Open the chronological record](dfm-evals/chronology-current-run-incremental-watcher-verified-on-2026-05-24.md).

### Completion update, verified on (2026-05-24)

[Open the chronological record](dfm-evals/chronology-completion-update-verified-on-2026-05-24.md).

### W&B workspace panel update, verified on (2026-05-24)

[Open the chronological record](dfm-evals/chronology-w-b-workspace-panel-update-verified-on-2026-05-24.md).

### Superseded/context update (2026-05-24)

[Open the chronological record](dfm-evals/chronology-superseded-context-update-2026-05-24.md).

### Suite update, verified on (2026-05-24)

[Open the chronological record](dfm-evals/chronology-suite-update-verified-on-2026-05-24.md).

### Single-task scheduling note, verified on (2026-05-24)

[Open the chronological record](dfm-evals/chronology-single-task-scheduling-note-verified-on-2026-05-24.md).

### Original+mixed checkpoint eval launch, verified on (2026-05-25)

[Open the chronological record](dfm-evals/chronology-original-mixed-checkpoint-eval-launch-verified-on-2026-05-25.md).

### W&B sync caveat for active original+mixed run, verified on (2026-05-25)

[Open the chronological record](dfm-evals/chronology-w-b-sync-caveat-for-active-original-mixed-run-verified-on-2026-05-25.md).

### Follow-up on (2026-05-25)

[Open the chronological record](dfm-evals/chronology-follow-up-on-2026-05-25.md).

### Superseded on (2026-05-25)

[Open the chronological record](dfm-evals/chronology-superseded-on-2026-05-25.md).

### PIQA scorer correction, verified on (2026-05-25)

[Open the chronological record](dfm-evals/chronology-piqa-scorer-correction-verified-on-2026-05-25.md).

### W&B sync update, verified on (2026-05-25)

[Open the chronological record](dfm-evals/chronology-w-b-sync-update-verified-on-2026-05-25.md).

### IFEval-DA sharding update, verified on (2026-05-25)

[Open the chronological record](dfm-evals/chronology-ifeval-da-sharding-update-verified-on-2026-05-25.md).

### Original+mixed epoch-2 dfm-evals launch, verified on (2026-05-25)

[Open the chronological record](dfm-evals/chronology-original-mixed-epoch-2-dfm-evals-launch-verified-on-2026-05-25.md).

### Epoch-2 completion, verified locally and through W&B sync logs on (2026-05-25)

[Open the chronological record](dfm-evals/chronology-epoch-2-completion-verified-locally-and-through-w-b-sync-logs-on-2026-05-25.md).

### Standard eval W&B sync, verified on (2026-05-25)

[Open the chronological record](dfm-evals/chronology-standard-eval-w-b-sync-verified-on-2026-05-25.md).

### CP2 standard MATH completion, verified on (2026-05-26)

[Open the chronological record](dfm-evals/chronology-cp2-standard-math-completion-verified-on-2026-05-26.md).

### Original+mixed CP3 queued-eval scheduler, launched on (2026-05-26)

[Open the chronological record](dfm-evals/chronology-original-mixed-cp3-queued-eval-scheduler-launched-on-2026-05-26.md).

### Incremental CP3 standard eval sync, verified on (2026-05-26)

[Open the chronological record](dfm-evals/chronology-incremental-cp3-standard-eval-sync-verified-on-2026-05-26.md).

### Original+mixed CP3 IFEval-DA completion, verified on (2026-05-26)

[Open the chronological record](dfm-evals/chronology-original-mixed-cp3-ifeval-da-completion-verified-on-2026-05-26.md).

### English summarization eval, added on (2026-05-27)

[Open the chronological record](dfm-evals/chronology-english-summarization-eval-added-on-2026-05-27.md).

### Danish summarization eval, added on (2026-05-27)

[Open the chronological record](dfm-evals/chronology-danish-summarization-eval-added-on-2026-05-27.md).

### Summarization eval scheduler launch, verified on (2026-05-27)

[Open the chronological record](dfm-evals/chronology-summarization-eval-scheduler-launch-verified-on-2026-05-27.md).

### Generation retention for summarization vs translation evals, verified on (2026-05-27)

[Open the chronological record](dfm-evals/chronology-generation-retention-for-summarization-vs-translation-evals-verified-on-2026-05-27.md).

### BERTScore note, updated on (2026-05-27)

[Open the chronological record](dfm-evals/chronology-bertscore-note-updated-on-2026-05-27.md).

### Stored-generation BERTScore run, verified on (2026-05-27)

[Open the chronological record](dfm-evals/chronology-stored-generation-bertscore-run-verified-on-2026-05-27.md).

### Stored-generation BERTScore W&B sync, verified on (2026-05-27)

[Open the chronological record](dfm-evals/chronology-stored-generation-bertscore-w-b-sync-verified-on-2026-05-27.md).

### Summarization under dfm-evals, added on (2026-05-27)

[Open the chronological record](dfm-evals/chronology-summarization-under-dfm-evals-added-on-2026-05-27.md).

### Summarization W&B sync, verified on (2026-05-27)

[Open the chronological record](dfm-evals/chronology-summarization-w-b-sync-verified-on-2026-05-27.md).

### Lite eval queue, verified on (2026-06-03)

[Open the chronological record](dfm-evals/chronology-lite-eval-queue-verified-on-2026-06-03.md).

### Clarification added (2026-06-04)

[Open the chronological record](dfm-evals/chronology-clarification-added-2026-06-04.md).

### True CP4 no-EMA lite eval, launched (2026-06-04)

[Open the chronological record](dfm-evals/chronology-true-cp4-no-ema-lite-eval-launched-2026-06-04.md).

### Runtime issue and mitigation (2026-06-04)

[Open the chronological record](dfm-evals/chronology-runtime-issue-and-mitigation-2026-06-04.md).

### CP4 EMA vs true no-EMA lite comparison (2026-06-04)

[Open the chronological record](dfm-evals/chronology-cp4-ema-vs-true-no-ema-lite-comparison-2026-06-04.md).

### CP1 true no-EMA lite eval, launched (2026-06-04)

[Open the chronological record](dfm-evals/chronology-cp1-true-no-ema-lite-eval-launched-2026-06-04.md).

### Original-plus-mixed lite eval queue, verified on (2026-06-04)

[Open the chronological record](dfm-evals/chronology-original-plus-mixed-lite-eval-queue-verified-on-2026-06-04.md).
