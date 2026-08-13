---
type: Operational Record
title: 2026-06-09 Posttrain Generated Dataset Size
description: 'Part of Current State: 2026-06-09 Posttrain Generated Dataset Size.'
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
# 2026-06-09 Posttrain Generated Dataset Size

Part of [Current State](/pages/current-state.md).

Confidence: high for local byte counts; medium for final-size extrapolation.

During the post-training transform/refine generation-to-1M run,
`data/generated_posttrain_transform_refine` contained `938` JSONL files totaling
`4,715,088,900` bytes (`4.391 GiB`) at about `934,065` generated rows counted by
the progress script. Scaling linearly gives an expected final generated JSONL
size around `5.0e9` bytes (`4.7 GiB`) for one million rows, before any separate
regeneration output. The missing-request shard tree
`data/synthetic_request_shards_posttrain_transform_refine_v3_missing` was about
`2.4G` on disk.

Token estimate, 2026-06-09. Confidence: medium-high for sampled tokenizer
measurement; medium for final extrapolation. A random sample of `20,001`
generated JSONL rows (`19,029` accepted) tokenized with
`data_io/trained_tokenizers/bpe/tokenizer.json`, using only the fields that
`convert-generated` keeps (`instruction` and `response`) plus a small special
token overhead, averaged `823` tokens per accepted row. That implies about
`0.45B` tokens for a `550k` accepted-row tranche and about `0.82B` tokens for a
`1M` accepted-row generated set before sampling repeats. The current
`prefix_config_posttrain_transform_refine.yaml` repeats synthetic prefixes
`20x`, so sampled per-epoch synthetic token contribution can be much larger
than the raw unique-token count unless caps/repeats are adjusted.

Generation wrapper bug, 2026-06-09. Confidence: high for local process
inspection. `scripts/run_posttrain_synthetic_generation_vllm.sh` originally
used a bare `wait` after launching both vLLM servers and shard workers. With
`STOP_SERVERS_ON_EXIT=0`, phase 1 of
`scripts/run_posttrain_transform_refine_to_1m_vllm.sh` finished all `550/550`
missing shards but remained stuck because the bare `wait` also waited for the
long-lived vLLM server processes. The script was patched to collect worker PIDs
and wait only for those worker PIDs. Existing already-running instances that
entered the old bare `wait` remain stuck until manually advanced or restarted.

Recovery action, 2026-06-09. Confidence: high for local launch output. The
stale phase-1 wrapper PIDs were stopped after confirming all `550/550` missing
generation shards were complete and failed count was zero. The eight existing
vLLM teacher servers on ports `8100`-`8107` were kept alive. A recovery script
was added at `scripts/resume_posttrain_transform_refine_to_1m_after_generation.sh`
to run phases 2-4 directly against the completed generated root. It was launched
in tmux window `posttrain_to_1m:3`, log
`logs/posttrain_transform_refine_to_1m_resume_20260609T083026.log`, and started
eight `audit-generated` processes under audit root
`logs/posttrain_transform_refine_generation/audits_to_1m_resume_20260609T083026`.

Recovery monitor, 2026-06-09. Confidence: high for local tmux and monitor
output. A clean per-GPU monitor was added at
`scripts/monitor_posttrain_to_1m_recovery.py` and launched in tmux window
`hrm-1:7`. It tracks the active audit root, per-GPU audited rows/current file,
aggregate row rate, audit ETA, and GPU memory/utilization. The English-source
audit denominator is `500,000` generated rows: GPU row targets are
`65000, 64000, 62000, 60000, 61000, 61000, 63000, 64000` for GPUs 0-7. At
`2026-06-09 08:34:01 CEST`, the audit had written `19,866/500,000` rows
(`3.97%`) at about `92.7` rows/s, with an audit ETA of about `86.3` minutes.

Posttrain 1M recovery completion, 2026-06-09. Confidence: high for local queue
and process inspection. The recovery completed the final regeneration phase:
`318/318` regeneration shards were done, `0` failed, and regenerated outputs
were written to `data/generated_posttrain_transform_refine_regen_from_audit`.
The final phase had `3,829` regeneration rows. After completion, the eight
Gemma/vLLM teacher servers on ports `8100`-`8107` were terminated with
`SIGTERM`; `nvidia-smi` then reported `0 MiB` used on GPUs 0-7.

DFM4 XL-DDP step 700K lite eval launch, 2026-06-09. Confidence: high for local
tmux and scheduler logs. `scripts/run_dfm4_xl_ddp_lite_eval_700k.sh` launches
the `step_700000` no-EMA lite eval followed by the EMA lite eval, both syncing
to W&B run `dfm4xlddpclean` in project
`Original Plus Mixed Danish Instruction Rich L`. The x-axis value is
`1.9112836727227056`, computed from `700000 / (1831230 / 5)`. The active tmux
session is `dfm4_lite_eval_700k`; pane 1 runs the launcher and pane 2 runs
`scripts/watch_multi_checkpoint_eval_progress.py` for the no-EMA log roots.
Initial no-EMA telemetry showed `GSM8k` at batch size `128` OOMed with
`peak_used_mib=181576`, then succeeded at batch size `64` with
`peak_used_mib=151090`.

Follow-up status, 2026-06-09. Confidence: high for local tmux/status logs. The
`step_700000` no-EMA lite eval completed successfully and final merge ended
with `status_0` at `2026-06-09T21:01:12+02:00`. The five HRM server-backed DFM
tasks that OOM-looped at batch size `64` were retried at batch size `32` and
finished successfully: `piqa`, `danish_citizen_tests`, `gec_dala`,
`multi_wiki_qa`, and `dala`. The EMA half did not start in that tmux run: after
the no-EMA finish, the launcher exited with `unexpected EOF while looking for
matching '"'`, likely because the script was edited while the shell was still
reading it. The on-disk launcher validates with `bash -n` after the edit. At
inspection time, the DFM4 XL-DDP training run had resumed from `step_700000`
and was occupying all eight GPUs; no EMA lite eval scheduler/status file existed
under `logs/eval/dfm4_XL_ddp_ema_lite_700k_20260609`.

EMA low-headroom launch, 2026-06-09. Confidence: high for local command and
initial monitor output. After explicit no-EMA final merge/resync completed with
`FINAL_MERGE_END`, the `step_700000` EMA lite eval was launched while training
was active, using the earlier low-headroom pattern:

```text
LOG_ROOT_BASE=logs/eval/dfm4_XL_ddp_ema_lite_700k_20260609_lowbs
DFM_LOG_ROOT_BASE=logs/dfm_evals/dfm4_XL_ddp_ema_lite_700k_20260609_lowbs
GPUS=0,3,2
STANDARD_BATCH_SIZE=1
DFM_BATCH_SIZE=1
IFEVAL_BATCH_SIZE=1
NO_EMA=0
EVAL_PREFIX=lite_eval_ema
DFM_EVAL_PREFIX=lite_dfm_eval_ema
```

The run is in tmux session `dfm4_lite_eval_700k_ema_lowbs`. Initial active
jobs were IFEval-DA on GPU0, MATH on GPU3, and GSM8k on GPU2. At
`2026-06-09T21:58:59`, GSM8k had progressed to `71/165`, MATH had loaded, and
IFEval-DA had started; GPU2 had only about `123 MiB` free, so this remains a
tight low-headroom run.
