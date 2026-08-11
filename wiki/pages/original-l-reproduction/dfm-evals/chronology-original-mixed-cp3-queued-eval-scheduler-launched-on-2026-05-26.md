---
type: Operational Record
title: Original+mixed CP3 queued-eval scheduler, launched on (2026-05-26)
description: 'Chronological record from dfm-evals: Original+mixed CP3 queued-eval
  scheduler, launched on (2026-05-26).'
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
# Original+mixed CP3 queued-eval scheduler, launched on (2026-05-26)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Original+mixed CP3 queued-eval scheduler, launched on 2026-05-26. Confidence:
high for local queue state; medium for runtime until jobs complete.

The user requested one 8-GPU queue covering all CP3 standard eval tasks, all
8 standard MATH shards, all Danish dfm-eval tasks, and 4 IFEval-DA shards. The
following files were added:

```text
scripts/schedule_original_plus_mixed_cp3_evals.sh
config/dfm_evals_hrm_ifeval_da_4_shards.yaml
```

The scheduler is detached and running as:

```text
PID: 2007215
log root: logs/eval/original_plus_mixed_danish_instruction_rich_L_epoch3_queued_all
dfm log root: logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch3_queued_all
status: logs/eval/original_plus_mixed_danish_instruction_rich_L_epoch3_queued_all/status.tsv
queue: logs/eval/original_plus_mixed_danish_instruction_rich_L_epoch3_queued_all/jobs.tsv
```

At launch, `fsdp2_epoch_3` and `carry_epoch_3.{0..7}.pt` were not yet visible
under `checkpoints/original_plus_mixed_danish_instruction_rich/L`, so the
scheduler is in `WAIT_CHECKPOINT` state and will not start workers until the
checkpoint files exist. The check interval is `CHECKPOINT_WAIT_SECONDS=300`.

Queued jobs, `26` total:

```text
standard: GSM8k, DROP, MMLU, ARC, HellaSwag, Winogrande, BoolQ
standard_math: shard 0..7 of 8
dfm: danish_citizen_tests, dala, gec_dala, wmt24pp_en_da, multi_wiki_qa, piqa, generative_talemaader
dfm_ifeval: shard 0..3 of 4
```

Each worker owns one GPU and takes the next job from the shared queue when its
current job exits. `generative_talemaader` starts the Gemma judge
`unsloth/gemma-4-E4B-it` as `openai/gemma-4-e4b-judge` on the same GPU as that
job. Standard MATH and IFEval-DA are merged and synced after all workers finish.

Monitor:

```bash
cd /work/dfm/HRM-Text
tail -f logs/eval/original_plus_mixed_danish_instruction_rich_L_epoch3_queued_all/status.tsv
```

Stop if needed:

```bash
cd /work/dfm/HRM-Text
kill "$(cat logs/eval/original_plus_mixed_danish_instruction_rich_L_epoch3_queued_all/scheduler.pid)"
```
