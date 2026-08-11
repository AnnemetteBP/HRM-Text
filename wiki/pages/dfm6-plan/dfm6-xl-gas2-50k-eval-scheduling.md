---
type: Plan Record
title: DFM6 XL-GAS2 50K Eval Scheduling
description: 'Part of DFM6 Plan: DFM6 XL-GAS2 50K Eval Scheduling.'
tags:
- dfm6
- data
- training
- evaluation
status: stable
last_updated: 2026-06-28
confidence: high
part_of: /pages/dfm6-plan.md
---
# DFM6 XL-GAS2 50K Eval Scheduling

Part of [DFM6 Plan](/pages/dfm6-plan.md).

Last updated: 2026-06-20
Confidence: high
Scope: Local scheduler plan for the ongoing `dfm6-XL-gas2` training run.

The ongoing DFM6 XL gradient-accumulation run is:

```text
checkpoint_path: checkpoints/dfm6/XL-gas2
run_name:        dfm6-XL-gas2
wandb_project:   DFM5
wandb_run_id:    39ht9plp
```

The local W&B run id was verified from
`wandb/run-20260620_140018-39ht9plp/logs/debug.log`, whose config has
`run_name='dfm6-XL-gas2'`, `gradient_accumulation_steps=2`,
`checkpoint_path='checkpoints/dfm6/XL-gas2'`, and
`data.path='data/sampled_dfm6'`.

The 50K eval epoch is:

```text
50000 * 262144 / 62819933768 = 0.208647147709613
```

The eval plan was created at:

```text
logs/scheduler/dfm6_XL_gas2_step50000_vllm_main_20260620
```

with logs under:

```text
logs/eval/dfm6_XL_gas2_step50000_vllm_main_20260620
logs/dfm_evals/dfm6_XL_gas2_step50000_vllm_main_20260620
logs/euroeval/dfm6_XL_gas2_step50000_vllm_main_20260620
```

Important DFM6-specific differences from the DFM5-L wrapper:

- `--ckpt-path checkpoints/dfm6/XL-gas2`
- `--wandb-run-id 39ht9plp`
- `--wandb-run-name dfm6-XL-gas2`
- `--vllm-extra-args` uses
  `evaluation/chat_templates/gemma4_native_chat.jinja`, not
  `hrm_direct_chat.jinja`, because DFM6 was tokenized with Gemma-native chat
  rendering.
- `--no-include-report` is used because the scheduler report row currently
  regenerates the DFM5-L markdown report.
- `valeu-da` was marked `skipped`, matching the current failure-avoidance
  policy.

The launched tmux windows are:

```text
hrm-0:evaldfm6xl50
hrm-0:mondfm6xl50
```

Initial monitor state after launch:

```text
jobs done=0 running=1 ready=0 blocked_pending=208 failed=0 skipped=1 total=210
```

This means the scheduler is waiting for `step_50000` and has not started eval
work yet.

Update, 2026-06-20. Confidence: high for local plan inspection, code
inspection, and syntax checks. The first DFM6 50K plan initially had
`vllm_extra_args` set to the Gemma native chat template for DFM and EuroEval,
but standard eval used `evaluation/config/hrm_vllm_benchmarking.yaml`, whose
`prompt_mode=hrm` formats prompts with HRM direct tokens instead of Gemma
native chat turns. Because the plan was still blocked on `step_50000`, it was
patched before any eval rows could start:

```text
standard_config: evaluation/config/dfm6_vllm_benchmarking.yaml
```

`evaluation/config/dfm6_vllm_benchmarking.yaml` uses:

```text
prompt_mode: gemma_chat
chat_template_path: evaluation/chat_templates/gemma4_native_chat.jinja
```

`evaluation/engines.py` now supports `VLLMEngine(prompt_mode="gemma_chat")`,
which renders standard-eval prompts as one user message plus an assistant
generation prompt via the Gemma native Jinja template. A lightweight render
smoke produced:

```text
<bos><|turn>user\nWhat is 2+2?<turn|>\n<|turn>model\n
```

The DFM6 comparison report script is:

```bash
cd /work/dfm/HRM-Text
python scripts/generate_dfm6_eval_comparison_report.py
```

It writes `docs/dfm6.md`, with columns ordered as DFM6 checkpoints first,
then `DFM5-L 900K`, then the four Original Sapient L EMA epoch columns, then
the model-card and Qwen comparison columns reused from the DFM5 report.

Update, 2026-06-21. Confidence: high for local plan creation, plan metadata
inspection, and live scheduler monitor snapshots. The 50K eval completed with
`209` done jobs, `1` skipped job (`valeu-da`), and no failures. Four additional
DFM6 XL-GAS2 checkpoint eval plans were created and launched with indefinite
checkpoint waits:

| Checkpoint | Eval epoch | Plan dir | Port base | tmux runner | tmux monitor |
|---|---:|---|---:|---|---|
| `step_100000` | `0.41729429541922597` | `logs/scheduler/dfm6_XL_gas2_step100000_vllm_main_20260621` | `30000` | `hrm-0:evald6x100` | `hrm-0:mond6x100` |
| `step_150000` | `0.6259414431288389` | `logs/scheduler/dfm6_XL_gas2_step150000_vllm_main_20260621` | `31000` | `hrm-0:evald6x150` | `hrm-0:mond6x150` |
| `step_200000` | `0.8345885908384519` | `logs/scheduler/dfm6_XL_gas2_step200000_vllm_main_20260621` | `32000` | `hrm-0:evald6x200` | `hrm-0:mond6x200` |
| `step_250000` | `1.0432357385480648` | `logs/scheduler/dfm6_XL_gas2_step250000_vllm_main_20260621` | `33000` | `hrm-0:evald6x250` | `hrm-0:mond6x250` |

Each plan was created with:

```text
checkpoint_wait_seconds: 60
checkpoint_wait_max_seconds: 0
standard_config: evaluation/config/dfm6_vllm_benchmarking.yaml
standard_engine_backend: vllm
hrm_server_backend: vllm
hrm_vllm_native_proxy: true
vllm_extra_args: --enforce-eager --attention-backend FLASH_ATTN --chat-template /work/dfm/HRM-Text/evaluation/chat_templates/gemma4_native_chat.jinja
wandb_project: DFM5
wandb_run_id: 39ht9plp
wandb_run_name: dfm6-XL-gas2
```

Each plan has `210` jobs total: `208` blocked/pending eval-or-merge jobs,
`1` running checkpoint wait job, and `1` skipped `valeu-da` job. Distinct
`port_base` values were used to reduce collision risk if two checkpoint evals
briefly overlap.

`scripts/generate_dfm6_eval_comparison_report.py` was updated so
`docs/dfm6.md` now includes columns for `50K`, `100K`, `150K`, `200K`, and
`250K`, followed by `DFM5-L 900K`, Original Sapient L EMA epochs 1-4, and the
model-card/Qwen comparison columns.

Update, 2026-06-21. Confidence: high from local logs, W&B API inspection, and
live scheduler process checks. The completed 50K DFM6 eval initially had a W&B
visibility issue: the post-run average job logged `avg/*` metrics, while the
current DFM5/DFM6 workspace convention expects `headline_avg/*`, and the first
manual repair attempt used explicit W&B `_step=50000`, which W&B rejected
because the active training run had already advanced beyond that step.

The accepted repair command was:

```bash
cd /work/dfm/HRM-Text
python scripts/backfill_external_eval_to_wandb.py \
  --entity peter-sk-sdu \
  --project DFM5 \
  --run-id 39ht9plp \
  --run-name dfm6-XL-gas2 \
  --standard-root logs/eval/dfm6_XL_gas2_step50000_vllm_main_20260620 \
  --dfm-root logs/dfm_evals/dfm6_XL_gas2_step50000_vllm_main_20260620 \
  --euroeval-root logs/euroeval/dfm6_XL_gas2_step50000_vllm_main_20260620/step_50000 \
  --epoch 0.208647147709613 \
  --step 50000 \
  --average-prefix headline_avg \
  --log-averages
```

This logs without an explicit W&B `_step` but includes
`eval/train_step=50000`, `dfm_eval/train_step=50000`,
`euroeval/train_step=50000`, and `headline_avg/train_step=50000`.

Superseding correction later on 2026-06-21: the W&B headline panels still did
not show the 50K averages reliably after this first repair. A second explicit
average-only W&B row was logged with both historical average namespaces,
`headline_avg/*` and `avg/*`, and both epoch keys. W&B accepted the row and
showed both namespaces in run history. The 50K average values are:

```text
headline_avg/danish: 0.2906948598718148
headline_avg/english: 0.33738026773051194
headline_avg/math_code: 0.15954299972604893
headline_avg/overall: 0.26253937577612524
```

To prevent recurrence for 100K and later, `eval_scheduler/eval_scheduler/runtime.py`
now implements the scheduler `average` action by calling
`scripts/backfill_external_eval_to_wandb.py` with `--average-prefix
headline_avg --extra-average-prefix avg --log-averages`, so the final post job
logs a consolidated row containing standard, DFM, EuroEval, and headline
average metrics from the local merged artifacts under both `headline_avg/*`
and `avg/*`. `scripts/backfill_external_eval_to_wandb.py` now defines
`*/train_step` as the W&B step metric, can log additional average namespaces,
and only uses an explicit W&B history step if `--wandb-step` is provided.

Superseded/updated on 2026-06-23. Confidence: high from local plan inspection,
syntax checks, dry-run average logging, and live W&B workspace update. The
single final average job and the first suite-only split were too coarse: a
Danish headline average should not wait for unrelated English/math/standard
work, and math/code should not wait for all standard tasks after GSM8K, MATH,
HumanEval, and BFCL are complete.

The scheduler now emits independent average jobs:

- `standard-average`, `dfm-average`, and `euroeval-average` log suite-level
  metrics under `suite_avg/{standard,dfm,euroeval}` only.
- `danish-average`, `english-average`, and `math-code-average` log
  `headline_avg/{danish,english,math_code}` plus compatibility `avg/*` as soon
  as their exact producer tasks are done.
- `headline-averages` logs only `headline_avg/overall` plus `avg/overall` and
  depends on all six preceding suite and section average jobs.

The Danish average still waits for both Danish DFM metrics and Danish
EuroEval metrics, because `headline_avg/danish` is intentionally a combined
headline metric. It no longer waits for English standard tasks, English
EuroEval tasks, or math/code tasks. The W&B workspace view was refreshed as
`https://wandb.ai/peter-sk-sdu/DFM5?nw=ccnaz38y6ro` and now has a separate
`Suite Averages` section backed by `suite_avg/*`. Active/future DFM6 XL-GAS2
plans for `250K`, `300K`, `350K`, `400K`, and `450K` were migrated to this
post-eval graph. The already-completed `50K`, `100K`, `150K`, and `200K`
plans were not rewritten in place.

Superseding correction later on 2026-06-23. Confidence: high from local W&B
logging output, plan inspection, and workspace manifest. The first 250K
average recovery was unsafe because the already-running scheduler process kept
the old `run_average` implementation in memory. When the migrated
`euroeval-average` job became ready, that stale runtime ignored the new
`average_scope`/`average_prefix` metadata and logged a partial full-average
row under both old namespaces, `avg/*` and `headline_avg/*`, at W&B history
step `50148`. Those prefixes are therefore contaminated for DFM6 after 200K
and should not be used for DFM6 reporting.

Clean replacement namespaces:

- `headline_avg_v2/*`: section headline averages and overall.
- `suite_avg_v2/*`: standard/DFM/EuroEval suite averages.

Implemented code changes:

- `eval_scheduler/eval_scheduler/plan.py` now writes average metadata with
  `average_prefix=headline_avg_v2` for section/overall jobs and
  `average_prefix=suite_avg_v2` for suite jobs.
- `eval_scheduler/eval_scheduler/runtime.py` defaults to `headline_avg_v2`
  and no longer writes compatibility `avg/*` rows unless explicitly requested
  in job metadata.
- `scripts/log_dfm5_headline_averages.py` and
  `scripts/backfill_external_eval_to_wandb.py` support `--average-scope
  suites`.
- `scripts/create_dfm5_headline_workspace.py` now defaults headline panels to
  `headline_avg_v2/*` and suite panels to `suite_avg_v2/*`.

The active/future 250K, 300K, 350K, 400K, and 450K plans were patched in place
so pending average jobs use the v2 prefixes. The prematurely completed 250K
`euroeval-average` was reset to `pending`; completed eval shards were not
changed. All 250K+ scheduler/monitor processes were stopped before this
patch, so future restarts will load the patched runtime.

The correct completed 50K, 100K, 150K, and 200K averages were relogged to W&B
under the v2 prefixes with:

```bash
cd /work/dfm/HRM-Text
python scripts/log_dfm5_headline_averages.py \
  --project DFM5 --run-id 39ht9plp --run-name dfm6-XL-gas2 \
  --metric-prefix headline_avg_v2 --average-scope sections \
  --item '50000:0.208647147709613:logs/eval/dfm6_XL_gas2_step50000_vllm_main_20260620:logs/dfm_evals/dfm6_XL_gas2_step50000_vllm_main_20260620:logs/euroeval/dfm6_XL_gas2_step50000_vllm_main_20260620/step_50000' \
  --item '100000:0.41729429541922597:logs/eval/dfm6_XL_gas2_step100000_vllm_main_20260621:logs/dfm_evals/dfm6_XL_gas2_step100000_vllm_main_20260621:logs/euroeval/dfm6_XL_gas2_step100000_vllm_main_20260621/step_100000' \
  --item '150000:0.6259414431288389:logs/eval/dfm6_XL_gas2_step150000_vllm_main_20260621:logs/dfm_evals/dfm6_XL_gas2_step150000_vllm_main_20260621:logs/euroeval/dfm6_XL_gas2_step150000_vllm_main_20260621/step_150000' \
  --item '200000:0.8345885908384519:logs/eval/dfm6_XL_gas2_step200000_vllm_main_20260621:logs/dfm_evals/dfm6_XL_gas2_step200000_vllm_main_20260621:logs/euroeval/dfm6_XL_gas2_step200000_vllm_main_20260621/step_200000'

python scripts/log_dfm5_headline_averages.py \
  --project DFM5 --run-id 39ht9plp --run-name dfm6-XL-gas2 \
  --metric-prefix suite_avg_v2 --average-scope suites \
  --item '50000:0.208647147709613:logs/eval/dfm6_XL_gas2_step50000_vllm_main_20260620:logs/dfm_evals/dfm6_XL_gas2_step50000_vllm_main_20260620:logs/euroeval/dfm6_XL_gas2_step50000_vllm_main_20260620/step_50000' \
  --item '100000:0.41729429541922597:logs/eval/dfm6_XL_gas2_step100000_vllm_main_20260621:logs/dfm_evals/dfm6_XL_gas2_step100000_vllm_main_20260621:logs/euroeval/dfm6_XL_gas2_step100000_vllm_main_20260621/step_100000' \
  --item '150000:0.6259414431288389:logs/eval/dfm6_XL_gas2_step150000_vllm_main_20260621:logs/dfm_evals/dfm6_XL_gas2_step150000_vllm_main_20260621:logs/euroeval/dfm6_XL_gas2_step150000_vllm_main_20260621/step_150000' \
  --item '200000:0.8345885908384519:logs/eval/dfm6_XL_gas2_step200000_vllm_main_20260621:logs/dfm_evals/dfm6_XL_gas2_step200000_vllm_main_20260621:logs/euroeval/dfm6_XL_gas2_step200000_vllm_main_20260621/step_200000'
```

Dry-run counts before logging were complete: `18` Danish metrics, `15`
English metrics, `4` math/code metrics, `8` standard suite metrics, `11` DFM
suite metrics, and `18` EuroEval suite metrics for every checkpoint from 50K
through 200K. The refreshed clean W&B workspace is:
`https://wandb.ai/peter-sk-sdu/DFM5?nw=d4558ye9fcw`.

Follow-up on 2026-06-23. Confidence: high from local dry-runs and W&B logging
output. The same v2-prefix policy was applied to the two older comparison
runs that appear in the DFM5/DFM6 workspace:

- `original-sapient-L-dfm5-backfill-20260615`
- `dfm5-l-clean-20260619-v3`

Script changes:

- `scripts/backfill_original_sapient_l_to_dfm5.py` now rebuilds original
  Sapient L headline averages as `headline_avg_v2/*`, filters old average
  prefixes out of replayed source rows, and defines `headline_avg_v2` metrics.
- `scripts/backfill_dfm5_l_clean_wandb.py`,
  `scripts/relog_dfm5_l_clean_eval_rows.py`, and
  `scripts/append_dfm5_l_clean_from_source_wandb.py` now treat old
  `avg/*`, `headline_avg/*`, and `suite_avg/*` keys as source-only keys and
  remap them to `headline_avg_v2/*` or `suite_avg_v2/*` before logging. Their
  W&B metric definitions include only `eval`, `dfm_eval`, `euroeval`,
  `headline_avg_v2`, and `suite_avg_v2` for eval-like prefixes.

The first attempt to relog original Sapient L v2 averages used explicit W&B
history steps `81478`, `162961`, `244443`, and `325928`; W&B rejected those
rows because the resumed run's current `_step` was already `325933`. The
accepted relog omitted explicit W&B `_step` and relied on
`headline_avg_v2/epoch` plus `headline_avg_v2/train_step`, matching the DFM6
repair pattern. Four original Sapient L rows were accepted for epochs `1..4`.

For `dfm5-l-clean-20260619-v3`, average-only rows were relogged without
explicit W&B `_step` for train steps:

```text
50000, 100000, 150000, 200000, 250000, 300000, 350000, 400000, 450000,
500000, 550000, 600000, 700000, 750000, 800000, 850000, 900000
```

The local dry-run for `scripts/relog_dfm5_l_clean_eval_rows.py` on
`logs/relog_dfm5_l_clean_850k_900k_explicit_train_step_20260620.jsonl`
produced `73` rows with `0` old average keys and `18`
`headline_avg_v2/*` keys. A full audit remap check on
`logs/backfill_dfm5_l_clean_rows_v3_history650_20260619.jsonl` produced
`0` old average keys and `171` v2 average keys.

The W&B average sections were refreshed again so the panel metrics are:

- `Headline Averages`: `headline_avg_v2/{overall,danish,english,math_code}`
  over `headline_avg_v2/epoch`.
- `Suite Averages`: `suite_avg_v2/{standard,dfm,euroeval}` over
  `suite_avg_v2/epoch`.

The refreshed workspace URL is:
`https://wandb.ai/peter-sk-sdu/DFM5?nw=760qd0evtsa`.

The already-launched 100K, 150K, 200K, and 250K scheduler processes were
stopped while still in checkpoint-wait state, then relaunched with
`/home/ucloud/miniforge3/envs/hrm/bin/python` so they load the patched
scheduler runtime. This restart was repeated after adding the `avg/*`
compatibility namespace. As of the final relaunch check, each plan had
`pending=208`, `running=1`, `skipped=1`, no failures, and an active
checkpoint-wait job.

Update, 2026-06-22. Confidence: high from local plan creation, scheduler
status checks, tmux process inspection, and wait-log inspection. Four
additional DFM6 XL-GAS2 checkpoint eval plans were created and launched with
indefinite checkpoint waits:

| Checkpoint | Eval epoch | Plan dir | Port base | tmux runner | tmux monitor |
|---|---:|---|---:|---|---|
| `step_300000` | `1.2518828862576779` | `logs/scheduler/dfm6_XL_gas2_step300000_vllm_main_20260622` | `34000` | `hrm-0:evald6x300` | `hrm-0:mond6x300` |
| `step_350000` | `1.4605300339672909` | `logs/scheduler/dfm6_XL_gas2_step350000_vllm_main_20260622` | `35000` | `hrm-0:evald6x350` | `hrm-0:mond6x350` |
| `step_400000` | `1.6691771816769039` | `logs/scheduler/dfm6_XL_gas2_step400000_vllm_main_20260622` | `36000` | `hrm-0:evald6x400` | `hrm-0:mond6x400` |
| `step_450000` | `1.8778243293865167` | `logs/scheduler/dfm6_XL_gas2_step450000_vllm_main_20260622` | `37000` | `hrm-0:evald6x450` | `hrm-0:mond6x450` |

The plans match the working DFM6 vLLM settings:

```text
checkpoint_wait_seconds: 60
checkpoint_wait_max_seconds: 0
standard_config: evaluation/config/dfm6_vllm_benchmarking.yaml
standard_engine_backend: vllm
hrm_server_backend: vllm
hrm_vllm_native_proxy: true
vllm_extra_args: --enforce-eager --attention-backend FLASH_ATTN --chat-template /work/dfm/HRM-Text/evaluation/chat_templates/gemma4_native_chat.jinja
vllm_gpu_memory_utilization: 0.28
hrm_vllm_gemma_bfcl_tools: true
hrm_vllm_gemma_bfcl_tool_mode: parser
standard_batch: 64
dfm_batch: 32
ifeval_batch: 32
euroeval_batch: 32
euroeval_max_concurrent_calls: 32
judged_batch: 16
judged_max_connections: 16
judge_model: openai/gemma-4-e4b-judge
judge_server_model: unsloth/gemma-4-E4B-it
judged_vllm_gpu_memory_utilization: 0.18
govreport_max_report_chars: 9000
wandb_project: DFM5
wandb_run_id: 39ht9plp
wandb_run_name: dfm6-XL-gas2
```

Each plan has `210` jobs total: `208` pending eval-or-merge jobs, `1`
running checkpoint-wait job, and `1` skipped `valeu-da` job. The wait logs
show the expected missing-checkpoint messages for all four checkpoints, so no
eval work has started yet.

`scripts/generate_dfm6_eval_comparison_report.py` and `docs/dfm6.md` now
include future columns for `300K`, `350K`, `400K`, and `450K`.

Update, 2026-06-23. Confidence: high from local command output and W&B sync
logs. The clean v2 suite-average namespace is now backfilled for the older
comparison runs and uses epoch-level W&B x-axis labels:

- `suite_avg_v2/*` is defined against `suite_avg_v2/epoch`.
- `headline_avg_v2/*` remains defined against `headline_avg_v2/epoch`.
- Raw `eval/*`, `dfm_eval/*`, and `euroeval/*` metrics can still use their
  own eval-family x-axis fields.

Commands run from `/work/dfm/HRM-Text`:

```bash
python scripts/relog_suite_averages_v2.py original-sapient-l \
  --run-id original-sapient-L-dfm5-backfill-20260615 \
  --run-name 'original Sapient L backfilled'

python scripts/relog_suite_averages_v2.py dfm5-l-clean \
  --run-id dfm5-l-clean-20260619-v3 \
  --run-name dfm5-l-clean-20260619-v3
```

Observed sync results:

- `original-sapient-L-dfm5-backfill-20260615`: 4 suite-average rows, epochs
  `1.0` through `4.0`, with counts `standard=8`, `dfm=11`, `euroeval=18`.
- `dfm5-l-clean-20260619-v3`: 17 suite-average rows for train steps `50K`
  through `900K`, excluding `650K` because the clean average series does not
  have a complete 650K row in the local audit inputs; each logged row has
  counts `standard=8`, `dfm=11`, `euroeval=18`.

The relog helper is `scripts/relog_suite_averages_v2.py`. The DFM5 clean
backfill/relog helper scripts now define v2 average namespaces against the
epoch metric so future average rows line up with the workspace's epoch x-axis.

The eval scheduler monitor now shows a `blocked pending` section. A verified
snapshot for `logs/scheduler/dfm6_XL_gas2_step250000_vllm_main_20260621`
reported `blocked_pending=4` and correctly explained that the DFM average,
Danish average, and headline average were blocked behind the failed
`generative_talemaader` merge. This is implemented in
`eval_scheduler/eval_scheduler/monitor.py` and documented in
`eval_scheduler/README.md`.
