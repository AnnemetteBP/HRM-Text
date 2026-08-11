---
type: Operational Record
title: Suite update, verified on (2026-05-24)
description: 'Chronological record from dfm-evals: Suite update, verified on (2026-05-24).'
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
# Suite update, verified on (2026-05-24)

Part of [dfm-evals](/pages/original-l-reproduction/dfm-evals.md).

Suite update, verified on 2026-05-24: `config/dfm_evals_hrm.yaml:hrm_danish` now includes `dfm_evals/piqa`, `dfm_evals/ifeval-da`, and `dfm_evals/generative-talemaader` in the same suite as the existing Danish tasks. `uv sync --project dfm-evals --extra ifeval` was run successfully, installing `instruction-following-eval`, `nltk`, `langdetect`, `immutabledict`, and `joblib` for `ifeval-da`. `scripts/run_dfm_evals_on_checkpoints.sh` now accepts `JUDGE_MODEL` and `JUDGE_BASE_URL` and forwards them to `evals suite`; `JUDGE_MODEL` is required when running `generative-talemaader`, because that task uses a model-graded scorer. Confidence: high.

New-task dfm-evals run, verified on 2026-05-24: the three newly added tasks were run for all four original Sapient L checkpoints without rerunning the older dfm-evals tasks. A temporary suite file, `config/dfm_evals_hrm_new_tasks_only.yaml`, contains only `dfm_evals/piqa`, `dfm_evals/ifeval-da`, and `dfm_evals/generative-talemaader`. `generative-talemaader` used a local Transformers OpenAI-compatible server for `unsloth/gemma-4-E4B-it`, served as `openai/gemma-4-e4b-judge` at `http://127.0.0.1:8099/v1`. vLLM was not used for this judge because its Gemma 4 path required `flash_attn.ops`, which is absent in the local FA4/B200 environment. Completed Inspect logs and W&B sync markers exist for all three new tasks across epochs 1, 2, 3, and 4 under `logs/dfm_evals/original_sapient_L_new_tasks_gemma4_judge/epoch_{1..4}`. Confidence: high.
