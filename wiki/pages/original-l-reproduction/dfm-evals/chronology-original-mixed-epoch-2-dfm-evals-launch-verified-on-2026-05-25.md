---
type: Operational Record
title: Original+mixed epoch-2 dfm-evals launch, verified on (2026-05-25)
description: 'Chronological record from dfm-evals: Original+mixed epoch-2 dfm-evals
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
# Original+mixed epoch-2 dfm-evals launch, verified on (2026-05-25)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Original+mixed epoch-2 dfm-evals launch, verified on 2026-05-25. Confidence:
high.

Epoch 2 checkpoint files are present under:

```text
checkpoints/original_plus_mixed_danish_instruction_rich/L/fsdp2_epoch_2
checkpoints/original_plus_mixed_danish_instruction_rich/L/carry_epoch_2.{0..7}.pt
```

The seven non-IFEval Danish tasks were launched first, with GPU 7 reserved for
the Gemma judge:

```text
log root: logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch2_parallel_then_ifeval
judge: unsloth/gemma-4-E4B-it as openai/gemma-4-e4b-judge
judge URL: http://127.0.0.1:8799/v1
GPU 0: hrm_danish_danish_citizen_tests, port 8702
GPU 1: hrm_danish_dala, port 8712
GPU 2: hrm_danish_gec_dala, port 8722
GPU 3: hrm_danish_wmt24pp_en_da, port 8732
GPU 4: hrm_danish_multi_wiki_qa, port 8742
GPU 5: hrm_danish_piqa, port 8752
GPU 6: hrm_danish_generative_talemaader, port 8762
GPU 7: Gemma judge, port 8799
```

As non-IFEval tasks finish, IFEval-DA shards are scheduled onto freed GPUs with
`BATCH_SIZE=1`, `INSPECT_MAX_CONNECTIONS=1`, no per-shard W&B logging, and a
final merged W&B sync.

Correction note: the first scheduler version accidentally reused port `8872`
for shard 1 because a Bash local-assignment expression used a stale `shard`
variable while calculating `port_base`. The invalid shard-1 attempt was killed
and moved aside as:

```text
logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch2_parallel_then_ifeval/ifeval_shard_1_invalid_port_*
```

The valid shard layout is:

```text
shard 0: port 8872, launched before the correction
shard 1+: ports 8912, 8922, 8932, 8942, 8952, 8962, 8972 as scheduled by the corrected supervisor
```

Corrected supervisor log:

```text
logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch2_parallel_then_ifeval/supervisor_remaining.log
```

When all shards complete, the corrected supervisor merges:

```bash
cd /work/dfm/HRM-Text
python scripts/merge_ifeval_da_shards.py \
  logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch2_parallel_then_ifeval/ifeval_shard_{0,1,2,3,4,5,6,7}/epoch_2/inspect/*.eval \
  --epoch 2 \
  --output logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch2_parallel_then_ifeval/merged_ifeval_da_metrics.json \
  --log-wandb \
  --project "Original Plus Mixed Danish Instruction Rich L" \
  --run-id es1od1in \
  --run-name "original-plus-mixed-danish-instruction-rich-L"
```
