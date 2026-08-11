---
type: Operational Record
title: Original+mixed checkpoint eval launch, verified on (2026-05-25)
description: 'Chronological record from dfm-evals: Original+mixed checkpoint eval
  launch, verified on (2026-05-25).'
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
# Original+mixed checkpoint eval launch, verified on (2026-05-25)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Original+mixed checkpoint eval launch, verified on 2026-05-25. Confidence: high.

The first checkpoint of the ongoing `original_plus_mixed_danish_instruction_rich` L run is available as `checkpoints/original_plus_mixed_danish_instruction_rich/L/fsdp2_epoch_1` plus `carry_epoch_1.{0..7}.pt`. Eight single-task dfm-evals jobs were launched in parallel, one per GPU, using `config/dfm_evals_hrm_single_tasks.yaml` and logging to the active W&B run id `es1od1in` in project `Original Plus Mixed Danish Instruction Rich L`.

Log root:

```text
logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch1_parallel
```

GPU/task mapping:

```text
GPU 0: hrm_danish_danish_citizen_tests, port 8411
GPU 1: hrm_danish_dala, port 8421
GPU 2: hrm_danish_gec_dala, port 8431
GPU 3: hrm_danish_wmt24pp_en_da, port 8441
GPU 4: hrm_danish_multi_wiki_qa, port 8451
GPU 5: hrm_danish_piqa, port 8461
GPU 6: hrm_danish_ifeval_da, port 8471
GPU 7: hrm_danish_generative_talemaader, port 8481
```

`generative_talemaader` requires a judge. The judge was launched on the same GPU 7:

```text
model: unsloth/gemma-4-E4B-it
served name: gemma-4-e4b-judge
base URL: http://127.0.0.1:8499/v1
log: logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch1_parallel/judge_gemma4_e4b_gpu7/server.log
```

At launch verification, all task wrappers were active except `piqa`, which had already completed successfully with `accuracy = 0.194`. The remaining HRM shim health ports responded; the judge health endpoint can time out during active generation on GPU 7, but it started successfully before the judged task was launched.
