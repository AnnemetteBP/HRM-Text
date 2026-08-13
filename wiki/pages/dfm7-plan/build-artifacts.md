---
type: Plan Record
title: Build Artifacts
description: 'Part of DFM7 Plan: Build Artifacts.'
tags:
- dfm7
- data
- training
- evaluation
status: stable
last_updated: 2026-07-02
confidence: medium
part_of: /pages/dfm7-plan.md
---
# Build Artifacts

Part of [DFM7 Plan](/pages/dfm7-plan.md).

DFM7 initial build scaffolding, 2026-06-30. Confidence: high from local file
edits, medium until full download/tokenization/sample execution.

Created separate DFM7 artifacts and commands:

- Training config: `config/data/dfm7.yaml` points at `data/sampled_dfm7`.
- Sampling config: `data_io/prefix_config_dfm7.yaml` starts from the DFM6
  policy and adds DFM7-specific broader Danish instruction/chat/math sources.
- Source tree builder: `scripts/build_dfm7_chat_source_tree.py` writes
  `data/dfm7_chat_sources`.
- Tokenized union builder: `scripts/build_tokenized_dfm7_tree.py` writes
  `data/tokenized_dfm7`.
- Special-source converter: `scripts/prepare_dfm7_special_sources.py` prepares
  benchmark-shaped training rows such as Kaenguruen as explicit
  instruction/response JSONL.
- End-to-end preparation script: `scripts/prepare_dfm7_data.sh`.

Gemma 4 template invariant:

- DFM7 must use `data_io/chat_templates/gemma4_native_chat.jinja` throughout.
- `scripts/prepare_dfm7_data.sh` checks the template path and exits if a
  different template is supplied.
- `scripts/prepare_dfm7_data.sh` also defaults to the Gemma 4 tokenizer at
  `/work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json` and rejects
  non-Gemma tokenizer paths.
- Tokenization output goes through `scripts/tokenize_chat_template.py`; do not
  use the legacy Rust HRM marker-tokenizer for DFM7.

Incremental DFM7 correction, 2026-06-30. Confidence: high from local command
output. An initial `scripts/prepare_dfm7_data.sh` run mistakenly built a full
DFM6-plus source tree and began retokenizing 10,528 files. The largest inherited
groups were `sapient_cleaned` (4,891 files),
`converted_sources_dfm4_summarization` (4,019 files), and `export-upload`
(1,431 files). That run was stopped after 155 files and its partial
`data/tokenized_dfm7_jinja` output was deleted because it had also used the old
65k BPE tokenizer path. The DFM7 prep path now uses
`scripts/build_dfm7_chat_source_tree.py --new-only` and
`scripts/build_tokenized_dfm7_tree.py --base-tokenized data/tokenized_dfm6`, so
DFM7 reuses the existing Gemma-tokenized DFM6 tree and tokenizes only new DFM7
additions. Current new-only source-tree verification found only
`dfm7_special_sources/kaenguruen/train.jsonl`; the remaining DFM7 additions
must still be downloaded before tokenization.

DFM7 source-format notes:

- Preferred training schema is `messages` with assistant responses/tool calls.
- Flat instruction data should use `condition`, `instruction`, `response`.
- `scripts/tokenize_chat_template.py` now has a generic fallback for common HF
  fields such as `instruction/prompt/question` plus
  `response/completion/answer/target`, but dataset-specific converters are
  still preferred for MCQ/tool/math sources where the answer contract matters.
- Kaenguruen is converted to a Danish MCQ prompt that asks for
  `Svar: <bogstav>`, preserving answer choices instead of relying on generic
  question/answer extraction.

DFM7 novel eval scaffolding, 2026-06-30. Confidence: high for local imports
once tests pass; medium for task schemas that still need full smoke evals.

- New task module: `dfm-evals/dfm_evals/tasks/dfm7.py`.
- New suite config: `config/dfm_evals_dfm7_novel.yaml`.
- Added task wrappers for MultiIFEval, Danish GSM8K, GSM-Symbolic,
  Kaenguruen, Global PIQA DA, linguistic quality, SDU Daisy, DA-BIRD, and the
  Schneiderkamplab Danish/English tool-calling benchmark.
- Prompt policy:
  - MCQ tasks request a single option letter.
  - GSM-style tasks request a short final numeric answer and use a numeric
    extractor that accepts boxed or final numeric answers.
  - Translation/summarization tasks keep existing DFM eval prompts.
  - Tool-calling eval uses Inspect tool-call messages and a parser-aligned
    scorer rather than loose text matching.



DFM6-DFM7 1050K-1200K eval scheduler restart, 2026-07-05. Confidence: high from
local plan edit, scheduler status, tmux inspection, and process/GPU inspection.

- Reused plan directory:
  `logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253`.
- The plan was locked, backed up, and edited so stale `running` wait rows for
  `step_1050000`, `step_1100000`, `step_1150000`, and `step_1200000` were reset
  to `pending`. The `step_1250000` block was marked `skipped` for this launch.
- The stop flag was cleared. Initial active rows are the four checkpoint waits;
  the actual checkpoint directories were not present at launch, so the scheduler
  is expected to wait until each full checkpoint is written.
- The scheduler was launched from inside the `hrm` conda environment in tmux
  window `hrm-0:4` (`dfm7-eval-1050-1200`):

```bash
cd /work/dfm/HRM-Text
source /home/ucloud/miniforge3/etc/profile.d/conda.sh
conda activate hrm
/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler run \
  --plan-dir logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253 \
  --gpus 0,1,2,3,4,5,6,7
```

- The Rich monitor was launched in tmux window `hrm-0:5` (`dfm7-mon-1050-1200`):

```bash
cd /work/dfm/HRM-Text
source /home/ucloud/miniforge3/etc/profile.d/conda.sh
conda activate hrm
/home/ucloud/miniforge3/envs/hrm/bin/python -m eval_scheduler monitor \
  --plan-dir logs/scheduler/dfm6_dfm7_XL_gas2_steps850k_1000k_vllm_hrmenv_20260701_202253 \
  --gpus 0,1,2,3,4,5,6,7 \
  --interval 30 \
  --rich
```

- At launch, training was independently active from
  `resume_checkpoint_tag=ephemeral_step_1028500`, consuming the GPUs; the
  scheduler itself had only checkpoint-wait rows active.
- Follow-up on 2026-07-05: the existing `step_1250000` block was re-added to
  the live plan. Its rows were changed from `skipped` back to `pending`, except
  for the intentionally skipped EuroEval `valeu-da` row. The live scheduler
  picked up `wait-01737` for `step_1250000` at `2026-07-05T09:42:09+02:00`.
