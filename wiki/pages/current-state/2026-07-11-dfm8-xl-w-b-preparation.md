---
type: Operational Record
title: 2026-07-11 DFM8-XL W&B Preparation
description: 'Part of Current State: 2026-07-11 DFM8-XL W&B Preparation.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# 2026-07-11 DFM8-XL W&B Preparation

Part of [Current State](/pages/current-state.md).

Confidence: high for local script output and W&B API verification; medium for
the source-history caveat below.

A new W&B run has been prepared for continuing from the completed
DFM6-DFM7 `epoch_5` checkpoint onto DFM8 data:

```text
project: DFM5
run id:  dfm8-xl-from-dfm6-dfm7-epoch5
name:    DFM8-XL from DFM6-DFM7 epoch5
url:     https://wandb.ai/peter-sk-sdu/DFM5/runs/dfm8-xl-from-dfm6-dfm7-epoch5
```

The backfill script is:

```text
scripts/backfill_dfm8_xl_from_dfm6_dfm7_wandb.py
```

It cloned numeric history from source run
`peter-sk-sdu/DFM5/dfm6-dfm7-xl-gas2` into the new run and rewrote the new run
config for DFM8 continuation:

```text
data.path:                  data/sampled_dfm8
checkpoint_path:            checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5
resume_checkpoint_path:     checkpoints/dfm7/XL-gas2-from-dfm6-epoch3
resume_checkpoint_tag:      epoch_5
resume checkpoint step:     1229504
```

W&B API verification after sync showed:

```text
state: finished
_step: 1200000
dfm8_backfill/backfilled_through_step: 1229504
dfm8_backfill/resume_checkpoint_tag: epoch_5
dfm8_backfill/target_data: data/sampled_dfm8
```

The source W&B history scan yielded:

```text
rows logged into new run: 199999
eval-like rows:          25
history min/max step:    0 / 1200000
eval steps:              0, 50K, ..., 1200K
audit file:              logs/dfm8/dfm8_xl_from_dfm6_dfm7_backfill_rows.jsonl
online log:              logs/dfm8/dfm8_xl_from_dfm6_dfm7_backfill_online_20260711T090235.log
```

Superseded caveat: the local checkpoint sidecar
`checkpoints/dfm7/XL-gas2-from-dfm6-epoch3/checkpoint_state_epoch_5.json`
records `step=1229504`, `epoch=5`, and `batch_in_epoch=0`, but the source
W&B scan exposed usable history rows only through step `1200000`. The new run
therefore has resume metadata for `epoch_5`/`1229504`, while its history curve
currently ends at `1.2M`.

Replacement, 2026-07-11. Confidence: high from W&B API verification. The
earlier broad W&B scan missed sparse late training rows. A follow-up repair
queried train metrics one-by-one and appended the late tail to
`dfm8-xl-from-dfm6-dfm7-epoch5`.

```text
tail audit file: logs/dfm8/dfm8_xl_from_dfm6_dfm7_tail_train_rows.jsonl
tail rows:       653
tail step range: 1200045..1229485
verified _step:  1229485
```

The repaired W&B run now shows training metrics through about `1,229.5K`, very
close to the local `epoch_5` checkpoint sidecar step `1,229,504`. The final
few checkpoint-save steps do not have ordinary train metric rows.

Do not continue training into this run until the DFM8 pre-training gate above
is complete.

Superseded/failure note, 2026-07-11. Confidence: high from user report and
follow-up W&B/API checks. The prepared run
`dfm8-xl-from-dfm6-dfm7-epoch5` was deleted by the user and must be considered
a failed backfill. The failure mode was misleading W&B history: the first
clone missed sparse late training rows, and the incremental tail repair
created a visually wrong line from about `1.2M` to the end. The approach is not
acceptable for production run preparation.

The helper `scripts/backfill_dfm8_xl_from_dfm6_dfm7_wandb.py` is now marked
deprecated and refuses to run unless `--allow-deprecated` is provided for
forensic reproduction. Do not use it for a new DFM8 run.

Source-run check after deleting the failed DFM8 run:

- `DFM5/dfm6-dfm7-xl-gas2` still exists and is `finished`.
- The `3.312946907575793` eval point is still present in remote source history.
  Sampled W&B API checks found this epoch for `eval/epoch`, `dfm_eval/epoch`,
  and `euroeval/epoch` around W&B internal steps `800xxx`.
- The local audit file also contains the complete 800K/epoch-3.312946 row with
  484 metrics, including `eval/MATH/acc=0.39380364`,
  `dfm_eval/dala/linguistic-acceptability/dfm_evals_macro_f1=0.7531413615`,
  `headline_avg_v3/danish=0.5864574335`,
  `headline_avg_v3/english=0.6516015330`, and
  `headline_avg_v3/math_code=0.4414167715`.

If a DFM8 W&B preparation run is still desired, use a safer design:

1. Do not clone raw W&B sparse history directly.
2. Build a deterministic local JSONL first from known-good scheduler merged
   metrics plus selected train metrics.
3. Log all eval rows at explicit `eval/train_step`/`*/epoch` axes and inspect
   a local/offline run before syncing.
4. Avoid incremental tail repairs that create artificial visual connections.

Follow-up remote check, 2026-07-11. Confidence: high from W&B API
`history(keys=..., samples=100000)` queries. Although the user reported that
the workspace only displayed eval metrics through 800K, the remote source run
does contain post-800K history rows for representative metrics, with metric,
epoch, and train-step axes present in combined API rows:

| Metric | Last checked post-800K points |
| --- | --- |
| `eval/MATH/acc` | 850K, 900K, 950K, 1000K, 1050K, 1100K, 1150K, 1200K, epoch_5 |
| `dfm_eval/dala/linguistic-acceptability/dfm_evals_macro_f1` | 850K, 900K, 950K, 1000K, 1050K, 1100K, 1150K, 1200K, epoch_5 |
| `headline_avg_v3/danish` | 850K, 900K, 950K, 1000K, 1050K, 1100K, 1150K, 1200K, epoch_5 |
| `suite_avg_v3/standard` | 850K, 900K, 950K, 1000K, 1050K, 1100K, 1150K, 1200K, epoch_5 |

Example: `eval/MATH/acc` is present with `eval/epoch=4.88737064657577` and
`eval/train_step=1200000`, and with `eval/epoch=5` for the final epoch row.
Therefore the missing display is likely a W&B workspace/panel/query/display
issue, not source-run history deletion.

Workspace average-panel check, 2026-07-11. Confidence: high from live W&B
workspace API inspection via `wandb_workspaces.workspaces.internal.get_view_dict`.
The DFM5 manual workspace `https://wandb.ai/peter-sk-sdu/DFM5?nw=760qd0evtsa`
currently uses old v2 average keys in its visible average panels, despite the
newer scripts and some saved specs defaulting to v3:

- Headline panels use `headline_avg_v2/{overall,danish,english,math_code}` on
  `headline_avg_v2/epoch`.
- Per-section average panels in Danish/English/Math & Code also use
  `headline_avg_v2/*`.
- Suite panels use `suite_avg_v2/{standard,dfm,euroeval}` on
  `suite_avg_v2/epoch`.

For DFM6-DFM7 `dfm6-dfm7-xl-gas2`, the latest corrected averages are logged
under `headline_avg_v3/*` and `suite_avg_v3/*`; v4 and generic `avg/*`
average namespaces are not present. If averages look missing in this manual
workspace, the likely cause is that its panels are still pointed at v2.

Fix applied, 2026-07-11. Confidence: high from W&B upsert response and live
view re-read. The manual workspace `nw=760qd0evtsa` was updated in place,
preserving its layout and replacing only average panel namespaces:
`headline_avg_v2/` -> `headline_avg_v3/` and `suite_avg_v2/` ->
`suite_avg_v3/`. Verification found `0` remaining v2 average panel references
and `10` v3 average panel references. Backups:

- `logs/wandb_workspace_specs/dfm5_live_760qd0evtsa_before_v3_avg_fix_20260711T105452.json`
- `logs/wandb_workspace_specs/dfm5_live_760qd0evtsa_after_v3_avg_fix_20260711T105603.json`
- `logs/wandb_workspace_specs/dfm5_live_760qd0evtsa_verified_after_v3_avg_fix_20260711T105628.json`

Clean DFM8-XL W&B backfill, 2026-07-11. Confidence: high from local payload
validation and remote W&B API checks. A replacement clean continuation run was
created without using the deprecated broad-history clone:

```text
project: DFM5
run id:  dfm8-xl-from-dfm6-dfm7-epoch5-clean
name:    DFM8-XL clean from DFM6-DFM7 epoch5
url:     https://wandb.ai/peter-sk-sdu/DFM5/runs/dfm8-xl-from-dfm6-dfm7-epoch5-clean
script:  scripts/backfill_dfm8_xl_clean_wandb.py
```

The script builds a deterministic payload from local audit files:

- `logs/dfm8/dfm8_xl_from_dfm6_dfm7_backfill_rows.jsonl`
- `logs/dfm8/dfm8_xl_from_dfm6_dfm7_tail_train_rows.jsonl`

It filters to canonical `train/*`, `eval/*`, `dfm_eval/*`, `euroeval/*`,
`headline_avg_v3/*`, and `suite_avg_v3/*` keys, dropping stale v2/v4/generic
average namespaces and `*/epoch_5` summary-helper keys. The source `epoch_5`
eval row, which had `train_step=0`, is remapped to the real resume step
`1229504`.

Validated payload:

```text
rows:                  200,652
eval-like rows:        25
v3 average rows:       25
train metric rows:     200,640
min/max payload step:  5 / 1,229,504
train metric max step: 1,229,485
missing eval steps:    none for 50K..1.2M
missing avg steps:     none for 50K..1.2M
non-v3 average keys:   none
payload:               logs/dfm8/dfm8_xl_clean_backfill_payload.jsonl
summary:               logs/dfm8/dfm8_xl_clean_backfill_summary.json
```

Remote checks after upload:

- W&B summary `_step=1229504`.
- Final `eval/MATH/acc=0.4178042`.
- Final `headline_avg_v3/danish=0.5907344435459122`.
- Final `suite_avg_v3/dfm=0.6061997587343233`.
- `eval/epoch=5`, `eval/train_step=1229504`, and corresponding v3 average
  epoch/train-step axes are present.
- Sampled train history reaches the sparse late tail: `train/loss` and
  `train/accuracy` through about `1.229M`, `bp_steps` through about `1.229M`.

The run config points future training to `data/sampled_dfm8`, checkpoints to
`checkpoints/dfm8/XL-from-dfm6-dfm7-epoch5`, and resumes from
`checkpoints/dfm7/XL-gas2-from-dfm6-epoch3` with
`resume_checkpoint_tag=epoch_5`, `resume_step=1229504`, `resume_epoch=5`.
Do not start this training until the DFM8 pre-training gate is complete:
accepted Danish OpenHermes rows must be generated/audited, integrated, and
`data/sampled_dfm8` resampled.

OpenHermes auto-start watcher, 2026-07-11. Confidence: high from local script
creation and tmux/log inspection. The user wants Danish OpenHermes generation
to start automatically only after the current DFM8 targeted synthetic
generation+audit finishes. A watcher was created and launched:

```text
script: scripts/watch_dfm8_synthetic_then_openhermes_da.sh
tmux:   hrm-0 window 5, openhermes-wait
log:    logs/dfm8_openhermes_after_targeted_synthetic_20260711T114345.log
```

The watcher waits for `data/dfm8_targeted_synthetic/generated` and
`data/dfm8_targeted_synthetic/audits` to both reach `512` shard files, requires
zero failed generate/audit queue jobs, then waits for the targeted synthetic
runner and ports `8500-8507` vLLM processes to exit before running:

```bash
CONCURRENCY=128 \
GPU_MEMORY_UTILIZATION=0.7 \
MAX_NUM_SEQS=128 \
bash dfm8_openhermes_da/scripts/run_openhermes_da_8gpu.sh
```

Initial watcher state at launch was `generated=422/512`, `audits=414/512`,
`generate_pending=90`, `generate_running=8`, and no failures.
