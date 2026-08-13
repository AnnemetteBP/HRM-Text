---
type: Operational Record
title: 2026-06-12 Original Sapient L EuroEval
description: 'Part of Current State: 2026-06-12 Original Sapient L EuroEval.'
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
# 2026-06-12 Original Sapient L EuroEval

Part of [Current State](/pages/current-state.md).

Confidence: high for launch and process/log inspection; medium until all
EuroEval jobs finish and W&B sync is verified.

EuroEval was launched for the original Sapient L epoch checkpoints:

```text
checkpoints/original_sapient/L/fsdp2_epoch_{1,2,3,4}
checkpoints/original_sapient/L/carry_epoch_{1,2,3,4}.{0..7}.pt
```

Each checkpoint runs on one GPU:

```text
epoch_1 -> GPU4, port 9741
epoch_2 -> GPU5, port 9742
epoch_3 -> GPU6, port 9743
epoch_4 -> GPU7, port 9744
```

Command:

```bash
cd /work/dfm/HRM-Text
tmux new-session -d -s orig_sapient_l_euroeval \
  'cd /work/dfm/HRM-Text && scripts/run_original_sapient_l_euroeval_epochs.sh'
```

The run uses all Danish and English EuroEval tasks via
`EUROEVAL_LANGUAGES=da,en` and logs to W&B project
`Original Plus Mixed Danish Instruction Rich L`, run id `origLclean`, run name
`original-sapient-L-clean-history`. The x-axis metric is `euroeval/epoch`, with
values `1`, `2`, `3`, and `4`.

Important standard-settings note: the launch does not set
`EUROEVAL_FEW_SHOT`, `EUROEVAL_NUM_ITERATIONS`, or
`EUROEVAL_GENERATIVE_TYPE`; EuroEval therefore uses its upstream defaults.
Initial logs showed `Few-shot benchmarking` and `1/20 benchmarks`.

Operational note: EuroEval 17.3.0 refuses to import when top-level
`flash_attn` is discoverable. Because FA4 is installed for this repo,
`scripts/euroeval_api_no_flash_attn_guard.py` is used as `EUROEVAL_BIN` for
the EuroEval process only. The HRM OpenAI server process still sees FA4.

Primary local logs:

```text
logs/euroeval/original_sapient_L/launcher/status.log
logs/euroeval/original_sapient_L/epoch_{1,2,3,4}/server.log
logs/euroeval/original_sapient_L/epoch_{1,2,3,4}/euroeval.log
```

Status at about `2026-06-12T10:10+02:00`: all four EuroEval processes were
alive and GPUs 4-7 were active. Result rows written so far:

```text
epoch_1 -> 0 rows; still on AngryTweets (1/20)
epoch_2 -> 2 rows; last finished ScaLA-da
epoch_3 -> 2 rows; last finished ScaLA-da
epoch_4 -> 4 rows; last finished MultiWikiQA-da, then started Nordjylland News
```

Epoch 1 is behaving pathologically compared with later checkpoints. The
`epoch_1/euroeval.log` shows repeated batches where the first completion takes
about 80-90 seconds, and one AngryTweets validation pass reached only `145/157`
after about 28 minutes. The local server does not log generated text, so this
does not prove the content is meaningless, but it is strong evidence that
epoch 1 often fails to terminate with the expected short answer and runs near
the generation cap/EOA fallback. Confidence: high for timing/log state, medium
for the interpretation.

Superseded on `2026-06-12T10:22+02:00`: the initial EuroEval run was stopped
and all partial rows were invalidated because `scripts/hrm_openai_server.py`
ignored EuroEval/LiteLLM's `max_completion_tokens` request field. At stop time
the partial result row counts were:

```text
epoch_1 -> 1 row
epoch_2 -> 2 rows
epoch_3 -> 2 rows
epoch_4 -> 4 rows
```

Those rows may have been affected by over-long generations, so the full log
root was archived to avoid reusing old result files or generation caches:

```text
logs/euroeval/original_sapient_L_pre_max_completion_tokens_fix_20260612T102214+0200
```

EuroEval was restarted in tmux session `orig_sapient_l_euroeval` after the
server patch. Initial restarted logs show epoch 1 AngryTweets batches running
at roughly tens of examples per second instead of 80-90 second stalls, which is
consistent with EuroEval's per-task generation caps being honored. Confidence:
high for local process/log inspection.

Second restart on `2026-06-12T10:25+02:00`: the prior post-fix session had
already exited with status `143` for all four epochs and wrote zero corrected
result rows. Its log/cache root was archived before relaunch:

```text
logs/euroeval/original_sapient_L_aborted_restart_20260612T102521+0200
```

Fresh relaunch command used the existing epoch/GPU mapping in
`scripts/run_original_sapient_l_euroeval_epochs.sh`:

```text
epoch_1 -> GPU4, port 9741
epoch_2 -> GPU5, port 9742
epoch_3 -> GPU6, port 9743
epoch_4 -> GPU7, port 9744
```

Launcher status after restart:

```text
2026-06-12T10:25:29+02:00 START epoch_1 gpu_4 port_9741
2026-06-12T10:25:34+02:00 START epoch_2 gpu_5 port_9742
2026-06-12T10:25:39+02:00 START epoch_3 gpu_6 port_9743
2026-06-12T10:25:44+02:00 START epoch_4 gpu_7 port_9744
```

Local inspection confirmed all four `hrm_openai_server.py` processes were
running and serving requests; all four EuroEval client processes were also
alive. Result rows were still `0` for all epochs immediately after relaunch,
as expected during the first benchmark. Confidence: high.

Batch/concurrency restart on `2026-06-12T10:45+02:00`: the corrected bs4 run
had reached two result rows per epoch (`AngryTweets` and `ScaLA-da`) and was
archived before relaunching with larger local batching:

```text
logs/euroeval/original_sapient_L_corrected_bs4_partial_20260612T104523+0200
```

Relaunch environment:

```bash
EUROEVAL_BATCH_SIZE=32 EUROEVAL_MAX_CONCURRENT_CALLS=32
```

Launcher status:

```text
2026-06-12T10:45:23+02:00 START epoch_1 gpu_4 port_9741
2026-06-12T10:45:28+02:00 START epoch_2 gpu_5 port_9742
2026-06-12T10:45:33+02:00 START epoch_3 gpu_6 port_9743
2026-06-12T10:45:38+02:00 START epoch_4 gpu_7 port_9744
```

Local inspection confirmed all four HRM servers were launched with
`--batch-size 32`, and server logs showed `generation: 0/32` batches. GPU
memory increased from about 17-18 GB to about 71-72 GB per GPU, still well
within the 180 GB devices. Confidence: high.

Follow-up EuroEval queue launched on `2026-06-12T11:11+02:00` in tmux session
`queued_dfm_euroevals`. Confidence: high for local launch and status file.
