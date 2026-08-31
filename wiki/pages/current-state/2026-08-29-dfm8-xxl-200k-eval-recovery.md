---
type: Runbook
title: DFM8 XXL 200K Eval Recovery
description: Verified pause, export, full evaluation, and resume sequence for the DFM8 XXL campaign at step 200K.
tags: [training, evaluation, checkpoint, scheduler, wandb]
status: stable
last_updated: 2026-08-29
confidence: high
---
# DFM8 XXL 200K Eval Recovery

The DFM8 XXL campaign was paused after the complete
`ephemeral_step_201000` checkpoint. Completeness was verified from the JSON
sidecar, DCP `.metadata`, and all eight rank shards before signaling only the
training `torchrun` process.

The step-200000 EMA HF export then completed at:

```text
exports/dfm8_XXL_1epoch_step200000_ema_hf
```

It contains a 7.5 GB `model.safetensors`, the Gemma 4 tokenizer, and a validated
HRM HF config. The full 200K evaluation completed with 187 runnable jobs done,
`valeu-da` intentionally skipped, no failed jobs, all merges done, and headline
averages logged to `DFM5/40j5y877`. The average logger wrote 67 keys and the
report regenerated `docs/dfm5.md`.

Training resumed toward step 250000 from:

```text
resume_checkpoint_tag=ephemeral_step_201000
```

The scheduler row uses
`logs/training/dfm8_XXL_1epoch/step_201000_to_250000` and retains the original
optimizer, EMA, data cursor, and W&B run.

## Recovery Issues

The migrated node lacked the evaluator's local NordjyllandNews parquet. The
source was restored from
`danish-foundation-models/danish-dynaword:data/nordjyllandnews/data.parquet`
and exposed at the established evaluator path
`data/downloads/datasets/danish_dynaword/data/nordjyllandnews/nordjyllandnews.parquet`.
It contains 75,215 rows, of which 37,522 have the expected summarization-pair
format. All eight NordjyllandNews shards then succeeded on retry.

The cluster worker also exposed a same-process race in `atomic_json`: heartbeat
and assignment threads used the same PID-derived temporary filename. One
`os.replace` could therefore remove the other thread's source file. Atomic JSON
writes now use a unique temporary file per call, fsync it, and replace the
target. A concurrent 100-write regression test covers the failure.

W&B eval finalization advanced the run's internal history step to 201031 before
resumed training logged steps 201005 through 201030. W&B rejected those few
training points as non-monotonic. Training and checkpoint state were unaffected;
normal logging resumed at step 201035. Future pause/eval/resume orchestration
should avoid advancing the shared run history beyond the checkpoint step before
training resumes, or use explicitly defined metric step axes that do not rely
on W&B's internal row step.
