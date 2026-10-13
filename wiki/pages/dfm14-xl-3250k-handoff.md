---
type: Runbook
title: DFM14 XL Handoff at 3250K
description: Verified-transfer and exact-packing gate for one DFM14 epoch on the original XL run.
status: stable
confidence: high
last_updated: 2026-10-09
tags: [dfm14, training, xl, handoff]
---
# DFM14 XL Handoff at 3250K

## Scheduler Feeding Investigation (2026-10-09)

At 3350K the live plan contains about 30738 rows. Queue scans rebuilt the
entire dependency index for every pending row (about 12000 times); measuring
just that redundant construction took 14 seconds. Reuse a single index and
dependency-failure cache per immutable scan. Claim-time validation and plan
locking remain unchanged. Short EuroEval tasks also restart their CPU clients
and proxies, so persistent vLLM alone does not eliminate task-turnover gaps.
All 58 scheduler tests pass. The optimized scan profiled at 1.206 seconds
(1.046 seconds parsing the 102 MB plan; 0.150 seconds dependency checks).
A graceful runner restart applies this optimization without resetting completed
evaluations. A separate remaining bottleneck is that `run_euroeval_openai`
holds the GPU worker through CPU-only `log_euroeval_to_wandb.py` completion;
live kpwr-ner and llmzszl jobs were observed in that phase.

Resolved later the same day: persistent-runner startup splits pending vLLM
EuroEval rows into GPU inference and `merge_euroeval` CPU publication. The
original job ID belongs to publication, preserving all downstream dependencies.
Completed/running/failed rows are not rewritten. Migration is idempotent and
backs up the plan under its lock. CPU publication retries do not repeat GPU
inference; batched IFEval retains its `wandb_metrics.json` output name. All68
scheduler tests pass. Per-pass EuroEval CPU preparation remains separate from
this fix; benchmark prompts/scoring/pass counts are unchanged.
The live restart at20:07 split2447 pending rows and resumed the same campaign.

Follow-up during the DFM phase: EEE export of Inspect logs was also holding GPU
slots. Pending vLLM DFM shards now retain their original IDs as CPU
`export_dfm_results` rows after inference, with the inference endpoint recorded
as provenance only (the exporter does not require the server). Launch claims
and completion updates are batched into locked read/write transactions instead
of serially rewriting the102MB plan per GPU. Claim-time dependency revalidation
remains intact; completion states are persisted before dispatching dependants. All71 tests
pass. This does not eliminate Inspect/EuroEval process initialization or the
CPU preparation between benchmark passes; full GPU saturation is not promised.
Live evidence: all eight GPU jobs launched at20:15:21; Finnish DaLA CPU exports
completed successfully at20:17:30 and20:17:36 while other GPU jobs ran.

The Rich monitor was restored in shared tmux window7 (`eval-monitor`) at20:32,
refreshing every30 seconds. Monitor ready/blocked scans now also reuse snapshot
dependency indexes and failure caches, avoiding the same quadratic scan delay.

## Corrected Population Baseline (2026-10-08)

The original DFM14 3250K average retained epoch 10.609039833146502. The DFM13
segment finalizer updated only its own job-ID prefix, missing the later-added
DFM14 rows. The actual checkpoint epoch is 10.812711203938841, as recorded in
the export and EuroEval artifacts. Epoch validation therefore correctly omitted
240 available metrics from the 50-language average; weakening validation would
hide this error.

Recomputation at the actual epoch gives all-language 0.5954273687057958
(396/396 metrics), multilingual 0.5896957685334531 (357/357), and new-language
0.39119770480387983 (32/32). DFM14 population IDs now use `_v2`; `_v1` is
superseded because it contains an already-published point at the wrong epoch.
Shared config generation preserves this version for future preparation.

`scripts/schedule_dfm14_average_correction.py` queues the corrected baseline
after the running 3300K training segment and before its evaluations, preserving
exclusive W&B writes. Receipt and complete local preview are under
`data/dfm14/average-epoch-correction-3250k/`. Future DFM14 segment finalization
already selects all rows by boundary rather than a job-ID prefix, including the
new average rows. No GPU evaluations or training restarts are required.

## Readiness Gate Repair (2026-10-08)

Transfer verification and exact packing completed (final step 3768319), followed
by the 3250K evaluations and averages. The handoff wait then failed with
`KeyError: 'plan_dir'` because the gate constructor omitted required scheduler
metadata. Added the plan directory and a regression test invoking the real wait
handler. Reset only the failed gate after checking its isolated checkpoint;
preserved completed evaluations. The installed wrapper pin was refreshed only
for this reviewed change; backups and evidence are in `gate-plan-dir-fix.json`
and `installed.before-gate-plan-dir-fix.json` under the control directory.

## Policy

The owner authorized switching after step3250000. Current DFM13 training
through3250 remains unchanged. Continue the same XL optimizer/EMA and W&B run
`dfm8-xl-from-dfm6-dfm7-epoch5-clean-full`, projectDFM5.

- Exactly one DFM14 pass: sampled epoch0, resume metadata epoch1/row0.
- Superseded (2026-10-09): constant base LR3e-4 throughout the epoch.
  Superseded schedule: base LR3e-4 until step3650000, cosine decay to1e-5
  at3750000, then hold1e-5 through3768319 (18319 final steps).
  `lr_auto=true` preserves module scaling; no warmup or rewarm.
  Windowed cosine uses `lr_min_ratio=1/30` and clamps after its end.

### Earlier Cooldown Approved 2026-10-10

The user moved the cosine start to **3500000**, keeping its end at **3750000**:
base LR3e-4 until3500K, cosine decay to1e-5 over250K steps, then hold1e-5
through3768319. `lr_auto` and recurrence dividers are unchanged. The launcher
and pending training definitions in the authoritative SQLite plan use this
schedule; the already running segment is unchanged and ends before3500K.
- XL, GAS2, global batch262144; no optimizer-step advance at handoff.
- `data=dfm14`, target-only; pin `config/data/dfm14.yaml`.
- Output: `checkpoints/dfm14/XL-from-dfm13-step3250000`.
- Private resume sidecar; immutable tensor hardlinks preserve optimizer/EMA.

The explicit DFM14 config supersedes the initial DFM13-config/path override.
The incoming `dfm14/continue_training.py` is the other-machine XXL-wide
step870000/epoch2/GAS4 workflow; do not use its publication or scheduler-launch
path for this XL run.

## Readiness And Scheduling

Control root: `data/dfm14/xl-from-dfm13-step3250000`.
Transfer readiness: `data/sampled_dfm14/local-transfer-verified.json`, from
`ssh.cloud.sdu.dk:6768`, corrected remote
`/work/dfm/HRM-Text/data/dfm14/inheritance-reconciliation/sampled_dfm14/`.

Epoch0 contains135548772522 sampled tokens and406830651 rows; metadata's
total is a three-epoch average. Identity repeat0 follows the corrected-sample
authorization. Evidence covers transfer checksum, bounds and length checks,
not an independent full token-store hash.

The live readiness gate is installed on all eight old future training rows.
It preserves the3250 new-average dependency and all current training/eval rows.
Exact packing uses the production sampler:16384 tokens/rank/microbatch,
8 ranks, GAS2. `packing.json` records dropped sampler/accumulation tails.
No final optimizer boundary is guessed before this count completes.

The watcher clones the latest3250 coverage under PlanLock, including all32
new tasks (128 shards), the50-language average and existing averages, at every
future boundary including final. Obsolete unstarted rows become explicitly
superseded SKIPPED records; DONE history is retained. New terminal barriers
and teardowns are fresh and permit cleanup after eval failure. Following
training still requires successful preceding evaluations and averages.

Display eval epoch equals finalized3250 eval epoch plus DFM14 row fraction.
Training W&B metrics use `train/step` and a monotonic history offset; they do
not emit per-step `epoch`. Loader/checkpoint/local-diagnostic epoch1 is not a
fractional training-chart metric. No shared training logger was changed.

## Operation

CPU preparer137254 waits for transfer, then publishes `prepared.json`.
Handoff watcher147723 waits for that receipt, installs the exact schedule,
then publishes the isolated resume gate. Transfer131758 remains untouched.
Current identities/log paths are authoritative in `prepare-launch.json`
and `watch-launch.json`; do not launch duplicates.

```bash
# From the repository root, using /home/ucloud/miniforge3/envs/hrm/bin/python:
python -m scripts.prepare_dfm14_xl_handoff --watch
python -m scripts.schedule_dfm14_xl_handoff preview
python -m scripts.schedule_dfm14_xl_handoff arm
python -m scripts.schedule_dfm14_xl_handoff watch
```

The gate is already armed; these are recovery interfaces, not rerun commands.
No scheduler/server restart is performed by either watcher.

## Evidence

### GPU Idle Diagnosis, 2026-10-09

Read-only inspection of the live3350K campaign found request starvation and
per-task overhead, not simply misleading instantaneous utilization readings.
Across45 GPU job transitions in a ten-minute window, END-to-next-START delay
averaged9.7s (median10s, maximum14s). Five inspected EuroEval tasks then took
17.6-18.9s from START to their first proxy request. Winogrande-sr's request
span was only18.1s, so fixed overhead is material for these small tasks.

A further30 one-second utilization/Prometheus samples showed GPUs1,2,4 at
zero utilization with zero running and queued requests throughout; other
GPUs were actively processing. Peak observed KV occupancy was35.7%, and
active request maxima were64 or less despite server max-num-seqs1024.
This is not evidence that larger server capacity is needed. Client startup,
per-pass preparation and dispatch delays must be addressed first.

There was also a concrete startup failure: mmlu-sk on GPU4 at20:47:43 failed
to bind proxy port39690 (address already in use). The proxy exited, but
start_native_proxy's readiness loop does not poll the child and can wait
the full120s. Port probing does not reserve the socket. Recommended fixes:
process-aware readiness and atomic socket ownership; reuse compatible
proxies/HTTP clients; reduce full-plan transaction overhead; preprepare
clients or overlap preparation with current inference. The proxy currently
constructs an AsyncClient per request and performs synchronous tokenization
and logging inside its async handler; their individual costs were not profiled.
No live processes, plan rows, evaluation semantics or settings were changed
during this diagnosis.

Implemented follow-up: native proxies inherit a bound listening socket from
the scheduler (no probe/close/rebind race). Readiness checks child exit and
expected model identity. The proxy keeps one lifespan-scoped HTTP client with
connection reuse, and logs preparation_seconds without changing requests.
Regression coverage includes socket ownership, immediate child-exit detection,
HTTP payload preservation and client shutdown; a real CPU-only inherited-socket
proxy smoke passed. The scheduler drained active shards and restarted at
21:00:34 using runner-proxy-fix-20261009.log; no active shard was killed.

A further locked-file snapshot optimization avoids reparsing an unchanged
plan between completion, readiness and claim operations. It invalidates on
inode/size/mtime/ctime changes, including external edits, with regression
coverage. Initially staged for the next launch; superseded later on2026-10-09
by deployment with the atomic dispatch change below. Persistent proxy reuse across tasks and overlapping
client preparation remain follow-up work; no measured overall speedup is
claimed yet. Focused scheduler/proxy suite:84 passed.

The follow-up dispatch change combines completed-state updates and successor
claims into a single locked plan transaction and atomic write. Dependency
checks see the completed states before selecting successors. Stop requests
still publish completions but prevent new claims. Unchanged plans are reused
under the file lock; external edits invalidate the snapshot. Regression tests
cover same-transaction dependency release and one-write publication, plus the
existing execution/dependency suite. Deployment drains active shards first;
log: runner-atomic-dispatch-20261009.log in the campaign directory.
Verified after deployment: the first eight replacement transitions took
3-5s (mean4.125s, median4s), versus the preceding ten-minute sample's
mean9.7s/median10s/max14s. This is a small live sample, not a whole-campaign
benchmark. On a copied full plan, cached readiness scanning took0.065s
versus1.103s cold; claiming12 jobs plus atomic writing took1.118s.
All75 scheduler tests passed. Client startup still adds separate overhead;
this change reduces the dispatch gap, not all idle time.

Receipts in the control root: `armed.json`, `gate-verified.json`,
`approved-pin-refresh.json`, `ready-gated-verified.json`, and plan backups.
The pin-refresh receipt binds the current approved registry hash to the parent
eval-extension installation; earlier stale pins are superseded. Source pins
are checked again before successor installation. Config/population ownership
remains with the parent.

Verification:44 focused handoff/eval tests passed, including Hydra settings,
full final-boundary coverage and failure-safe cleanup. Actual average commands
were captured without execution. [DFM14 plan](dfm14-plan.md);
[DFM13 handoff](dfm13-xl-3150k-handoff.md).
