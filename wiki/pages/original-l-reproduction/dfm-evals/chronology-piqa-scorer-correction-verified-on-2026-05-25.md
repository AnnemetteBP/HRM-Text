---
type: Operational Record
title: PIQA scorer correction, verified on (2026-05-25)
description: 'Chronological record from dfm-evals: PIQA scorer correction, verified
  on (2026-05-25).'
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
# PIQA scorer correction, verified on (2026-05-25)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

PIQA scorer correction, verified on 2026-05-25. Confidence: high.

The local `dfm-evals` checkout remotes are:

```text
origin:   https://github.com/schneiderkamplab/dfm-evals.git
upstream: https://github.com/danish-foundation-models/dfm-evals
```

`dfm_evals/tasks/piqa.py` was patched so PIQA outputs that contain both standalone `A` and standalone `B` are treated as invalid. Previously, the scorer searched for the first standalone `A` or `B` anywhere in the completion. This made prompt/instruction echoes like `Svar kun med A eller B.` score as `A`, which inflated scores because PIQA-da has a strong label skew toward `A`.

Existing PIQA EEE JSONL outputs were rescored without rerunning generation using:

```bash
cd /work/dfm/HRM-Text
python scripts/rescore_piqa_evals.py \
  logs/dfm_evals/original_sapient_L_new_tasks_gemma4_judge/epoch_1/eee/PIQA-da/openai/hrm-original-sapient-L-epoch-1/dfa50a05c3b23d8609cd.jsonl \
  logs/dfm_evals/original_sapient_L_new_tasks_gemma4_judge/epoch_2/eee/PIQA-da/openai/hrm-original-sapient-L-epoch-2/839f2ca592f63c907898.jsonl \
  logs/dfm_evals/original_sapient_L_new_tasks_gemma4_judge/epoch_3/eee/PIQA-da/openai/hrm-original-sapient-L-epoch-3/7c3e7067c63b3396c133.jsonl \
  logs/dfm_evals/original_sapient_L_new_tasks_gemma4_judge/epoch_4/eee/PIQA-da/openai/hrm-original-sapient-L-epoch-4/aa0255714ba09be35e8f.jsonl \
  logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch1_parallel/piqa/epoch_1/eee/PIQA-da/openai/hrm-original-plus-mixed-L-piqa-epoch-1/203b5a01f3cab150e4a7.jsonl \
  --output logs/dfm_evals/piqa_strict_rescore_20260525.json
```

Strict rescore results:

```text
original_sapient epoch 1: accuracy 0.0000, invalid 108/108
original_sapient epoch 2: accuracy 0.0000, invalid 108/108
original_sapient epoch 3: accuracy 0.0000, invalid 108/108
original_sapient epoch 4: accuracy 0.0000, invalid 106/108
original+mixed epoch 1:  accuracy 0.1667, invalid 3/108
```

The old original Sapient PIQA scores were therefore scorer artifacts, not genuine PIQA performance. The original+mixed checkpoint mostly predicted `B` on an `A`-skewed set and remains low under the stricter scorer.
