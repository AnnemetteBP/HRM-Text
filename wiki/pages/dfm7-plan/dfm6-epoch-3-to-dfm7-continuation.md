---
type: Plan Record
title: DFM6 Epoch-3 To DFM7 Continuation
description: 'Part of DFM7 Plan: DFM6 Epoch-3 To DFM7 Continuation.'
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
# DFM6 Epoch-3 To DFM7 Continuation

Part of [DFM7 Plan](/pages/dfm7-plan.md).

DFM6 XL-GAS2 to DFM7 splice plan, 2026-06-30. Confidence: high for checkpoint
metadata, resume semantics, and the prepared W&B backfill from local/API
inspection.

Verified checkpoint state:

- `checkpoints/dfm6/XL-gas2/checkpoint_state_epoch_3.json` records
  `step=720084`, `epoch=3`, `batch_in_epoch=0`, `batch_in_epoch_exact=true`,
  `global_batch_size=262144`, `gradient_accumulation_steps=2`, and
  `data_path=data/sampled_dfm6`.
- `checkpoints/dfm6/XL-gas2/train_metadata.yaml` uses the Gemma4 tokenizer
  and chat template: `/work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json`
  and `data_io/chat_templates/gemma4_native_chat.jinja`.
- Superseded 2026-07-01: `data/sampled_dfm7_next/metadata.json` was an earlier
  DFM7 sample. The corrected canonical sample is now
  `data/sampled_dfm7/metadata.json` with `total_length=66657336296`.

Resume behavior:

- In `pretrain.py`, resuming from `resume_checkpoint_tag=epoch_3` sets
  `start_epoch=4`, `skip_batches=0`, and preserves the checkpoint step from the
  sidecar. The dataset epoch is then set to `start_epoch - 1`, so using
  `data=dfm7` will start at DFM7's fourth epoch stream while keeping the global
  training step at `720084`.
- Keeping `epochs=5` means the continuation will run epochs 4 and 5 only. To
  train five full DFM7 epochs after the three DFM6 epochs, use a different
  explicit plan; do not overload this splice command.

Recommended W&B policy:

- A new clean W&B run was prepared:
  `peter-sk-sdu/DFM5/dfm6-dfm7-xl-gas2`
  (`DFM6-DFM7-XL-gas2`). It should be used for the DFM6-to-DFM7 splice instead
  of mutating the original `dfm6-XL-gas2` run. The original training source was
  `peter-sk-sdu/DFM5/39ht9plp`.
- Backfill policy, verified 2026-06-30: use DFM6 training rows from
  `peter-sk-sdu/DFM5/39ht9plp`, but do not use eval rows from that run. Use
  eval rows up to and including step 700000 from
  `peter-sk-sdu/DFM5/dfm6-xl-gas2-300k-stopfix-clean-20260624`.
- The prepared backfill used 144,028 W&B history rows, reached last training
  row step 720080, and merged eval-like rows at steps
  50000, 100000, 150000, 200000, 250000, 300000, 350000, 400000, 450000,
  500000, 550000, 600000, 650000, and 700000 from the clean stopfix eval run.
  Superseded 2026-07-01: the first backfill config pointed at
  `data/sampled_dfm7_next`. The helper and training config now point at
  `data/sampled_dfm7`.
- Before resuming training, verify the W&B run still has no newer live rows.
  Then start the DFM7 continuation into that same run id. This keeps the
  dashboard continuous and avoids having to append old rows after newer live
  training rows.
- If backfilling after resume is unavoidable, log historical eval rows without
  an explicit W&B `_step` and use explicit `eval/train_step`, `dfm_eval/train_step`,
  `euroeval/train_step`, and `*/epoch` axes. This is workable, but previous
  runs showed that late backfills and summary updates are easier to get wrong.

Continuation command template:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 torchrun --nproc_per_node=8 pretrain.py \
  data=dfm7 \
  arch/size@arch=XL \
  lr=3e-4 \
  global_batch_size=262144 \
  gradient_accumulation_steps=2 \
  epochs=5 \
  distributed_strategy=fsdp \
  checkpoint_format=sharded \
  fsdp_params_precision=fp32 \
  fwd_bwd_dtype=bfloat16 \
  accelerator_type=sm100 \
  checkpoint_interval=1 \
  checkpoint_step_interval=10000 \
  ephemeral_checkpoint_step_interval=500 \
  checkpoint_path=checkpoints/dfm7/XL-gas2-from-dfm6-epoch3 \
  resume_checkpoint_path=checkpoints/dfm6/XL-gas2 \
  resume_checkpoint_tag=epoch_3 \
  upcast_optimizer_state_on_resume=false \
  reset_ema_on_resume=false \
  project_name=DFM5 \
  run_name=DFM6-DFM7-XL-gas2 \
  wandb_run_id=dfm6-dfm7-xl-gas2 \
  wandb_resume=allow
```

Use the old `wandb_run_id=39ht9plp` only if the deliberate choice is to
continue the original DFM6 W&B run despite the data mix changing mid-run.

Resume after interrupted DFM6-DFM7 training, 2026-07-01. Confidence: high from
local checkpoint sidecars and `pretrain.py` resume-code inspection.

- The latest available DFM7 splice checkpoint after the interrupted run is
  `checkpoints/dfm7/XL-gas2-from-dfm6-epoch3/checkpoint_state_ephemeral_step_772000.json`.
  It records `step=772000`, `epoch=4`, `batch_in_epoch=103832`, and
  `gradient_accumulation_steps=2`.
- `pretrain.py::resolve_resume_state()` uses the sidecar for `step`, `epoch`,
  and batch/row-cursor position. It does not use the sidecar `data_path` as the
  runtime dataset path; the active Hydra `data=dfm7` config supplies
  `data/sampled_dfm7`.
- Because the canonical DFM7 sample was rebuilt after this checkpoint, resuming
  from `ephemeral_step_772000` continues the model weights and global step while
  using the rebuilt DFM7 stream from the saved batch position in epoch 4. To
  replay corrected DFM7 from the beginning of the splice instead, resume from
  `checkpoints/dfm6/XL-gas2` `epoch_3` instead of the DFM7 ephemeral checkpoint.
- An eval scheduler may still be waiting for future DFM7 checkpoints; stop or
  pause it before resuming if the next training checkpoint should not trigger
  full-GPU evaluations.
- Eval scheduler monitor update, 2026-07-01. Confidence: high from local
  one-shot monitor tests. `python -m eval_scheduler monitor` remains plain text
  by default. Add `--rich` for an optional Rich table/live display with summary
  counts, per-GPU memory/utilization, active task progress/ETA, next-ready jobs,
  and blocked pending jobs. Use `--once --rich` for a static snapshot.
- Rich monitor refinement, 2026-07-01. Confidence: high from local tests with
  different `COLUMNS`/`LINES` values and live monitor restart in tmux
  `hrm-0:5`. The Rich monitor now uses the terminal size on each refresh,
  renders the status block as one compact line, keeps each GPU on a single row,
  and truncates `Next ready` / `Blocked pending` tables to the available height
  with an explicit `... N more` final row when not all rows fit. Follow-up in
  the same session: the height allocator now reassigns unused rows from an
  empty/small queue section to the other queue section, so a waiting plan with
  no ready rows can show more blocked rows instead of leaving blank vertical
  space.
- Rich monitor non-GPU running rows, 2026-07-01. Confidence: high from local
  one-shot render and tmux monitor restart. The Rich monitor now uses one
  combined `Running jobs` table. GPU-bound rows are labeled `GPU0`, `GPU1`,
  etc.; running jobs without a GPU assignment, such as checkpoint waits,
  exports, merges, averages, and report jobs, are labeled `CPU`. This makes
  all-current-wait states visible without spending vertical space on a separate
  `Other running` box.
