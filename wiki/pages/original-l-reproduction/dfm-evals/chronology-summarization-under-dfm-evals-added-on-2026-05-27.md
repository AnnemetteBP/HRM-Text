---
type: Operational Record
title: Summarization under dfm-evals, added on (2026-05-27)
description: 'Chronological record from dfm-evals: Summarization under dfm-evals,
  added on (2026-05-27).'
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
# Summarization under dfm-evals, added on (2026-05-27)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Summarization under dfm-evals, added on 2026-05-27. Confidence: high for local
registration and shell/compile checks; medium until the full scheduler is run.

`dfm-evals/dfm_evals/tasks/summarization.py` adds `dfm_evals/govreport` and
`dfm_evals/nordjyllandnews` as Inspect tasks. They use the same data/prompt
policy as the standard `evaluation.main` summarization tasks but persist
per-sample generations in Inspect `.eval` archives. Their scorer logs ROUGE,
BLEU, chrF3, chrF3++, and BERTScore precision/recall/F1 with
`xlm-roberta-large` by default.

`config/dfm_evals_hrm_single_tasks.yaml` now exposes:

```text
hrm_summarization_govreport
hrm_summarization_nordjyllandnews
```

`scripts/schedule_dfm_summarization_bertscore_all_checkpoints.sh` queues the
two summarization tasks over the seven existing L checkpoints: original Sapient
epochs 1-4 and original-plus-mixed epochs 1-3. It runs up to 8 independent jobs
in parallel using `GPUS=0,1,2,3,4,5,6,7`; each job sets
`CUDA_VISIBLE_DEVICES` for both the HRM checkpoint server and the dfm-evals
process, so a single eval is not distributed across GPUs. The launch command is:

```bash
cd /work/dfm/HRM-Text
export LOG_ROOT="logs/dfm_evals/summarization_bertscore_all_checkpoints_$(date +%Y%m%dT%H%M%S)"
mkdir -p "$LOG_ROOT"
setsid scripts/schedule_dfm_summarization_bertscore_all_checkpoints.sh \
  > "$LOG_ROOT/scheduler.log" 2>&1 < /dev/null &
echo $! > "$LOG_ROOT/scheduler.pid"
```

To get BERTScore for the summarization tasks, rerun these CP x eval pairs under
dfm-evals because the previous standard `eval/*` summarization run did not store
generations:

```text
original_sapient epochs 1,2,3,4: govreport, nordjyllandnews
original_plus_mixed_danish_instruction_rich epochs 1,2,3: govreport, nordjyllandnews
```
