---
type: Operational Record
title: Single-task scheduling note, verified on (2026-05-24)
description: 'Chronological record from dfm-evals: Single-task scheduling note, verified
  on (2026-05-24).'
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
# Single-task scheduling note, verified on (2026-05-24)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Single-task scheduling note, verified on 2026-05-24: `config/dfm_evals_hrm_single_tasks.yaml` defines one suite per `hrm_danish` task so future runs can schedule one eval task per GPU or run safe waves when training memory pressure is high. The suites are `hrm_danish_danish_citizen_tests`, `hrm_danish_dala`, `hrm_danish_gec_dala`, `hrm_danish_wmt24pp_en_da`, `hrm_danish_multi_wiki_qa`, `hrm_danish_piqa`, `hrm_danish_ifeval_da`, and `hrm_danish_generative_talemaader`. No original+mixed checkpoint eval worker was launched when this config was created; the user chose to wait until GPU pressure drops. Confidence: high.

Launch pattern used for the new-task-only run:

```bash
cd /work/dfm/HRM-Text
python scripts/transformers_openai_server.py \
  unsloth/gemma-4-E4B-it \
  --served-model-name gemma-4-e4b-judge \
  --host 127.0.0.1 \
  --port 8099 \
  --dtype bfloat16 \
  --attn-implementation sdpa \
  --max-new-tokens 512

for spec in 1:0 2:1 3:2 4:3; do
  epoch="${spec%%:*}"
  gpu="${spec##*:}"
  EPOCHS="${epoch}" \
  GPU="${gpu}" \
  PORT_BASE=8210 \
  SUITE_FILE=/work/dfm/HRM-Text/config/dfm_evals_hrm_new_tasks_only.yaml \
  SUITE=hrm_danish_new_tasks_only \
  LOG_ROOT=/work/dfm/HRM-Text/logs/dfm_evals/original_sapient_L_new_tasks_gemma4_judge \
  JUDGE_MODEL=openai/gemma-4-e4b-judge \
  JUDGE_BASE_URL=http://127.0.0.1:8099/v1 \
  INCREMENTAL_WANDB_SYNC=1 \
  SYNC_INTERVAL_SECONDS=30 \
  FINAL_WANDB_SYNC=0 \
  OPENAI_API_KEY=inspectai \
  scripts/run_dfm_evals_on_checkpoints.sh
done
```

Manual sync command pattern:

```bash
cd /work/dfm/HRM-Text
uv run --project dfm-evals evals eee inspect \
  --log-path logs/dfm_evals/original_sapient_L/epoch_${epoch}/manual_sync_completed_20260524_1216/eval_logs \
  --output-dir logs/dfm_evals/original_sapient_L/epoch_${epoch}/manual_sync_completed_20260524_1216/eee \
  --source-organization-name "schneiderkamplab" \
  --evaluator-relationship "first_party" \
  --inference-base-url "http://127.0.0.1:${port}/v1" \
  --inference-provider-name "hrm-openai-shim"

python scripts/log_dfm_evals_to_wandb.py \
  --eee-dir logs/dfm_evals/original_sapient_L/epoch_${epoch}/manual_sync_completed_20260524_1216/eee \
  --epoch "${epoch}" \
  --project "Original Plus Mixed Danish Instruction Rich L" \
  --run-id "origLclean" \
  --run-name "original-sapient-L-clean-history" \
  --prefix "dfm_eval"
```

Manual sync results:

```text
epoch 1:
  dfm_eval/danish-citizen-tests/knowledge/accuracy = 0.00550
  dfm_eval/danish-citizen-tests/knowledge/dfm_evals_mcc = -0.01355
  dfm_eval/dala/linguistic-acceptability/dfm_evals_macro_f1 = 0.03815
  dfm_eval/dala/linguistic-acceptability/dfm_evals_mcc = -0.01899
  dfm_eval/gec_dala/exact_match/mean = 0.00000

epoch 2:
  dfm_eval/danish-citizen-tests/knowledge/accuracy = 0.17615
  dfm_eval/danish-citizen-tests/knowledge/dfm_evals_mcc = 0.06919

epoch 3:
  dfm_eval/danish-citizen-tests/knowledge/accuracy = 0.15963
  dfm_eval/danish-citizen-tests/knowledge/dfm_evals_mcc = 0.00582

epoch 4:
  dfm_eval/danish-citizen-tests/knowledge/accuracy = 0.13028
  dfm_eval/danish-citizen-tests/knowledge/dfm_evals_mcc = 0.02170
```

Smoke command:

```bash
cd /work/dfm/HRM-Text
INSTALL=1 EPOCHS="4" scripts/run_dfm_evals_on_checkpoints.sh -- --limit 10
```

Full default command:

```bash
cd /work/dfm/HRM-Text
scripts/run_dfm_evals_on_checkpoints.sh
```
