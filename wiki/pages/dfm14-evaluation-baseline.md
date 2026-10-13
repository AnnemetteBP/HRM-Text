---
type: Specification
title: DFM14 and DFM15 Evaluation Baseline
description: Required inherited benchmark coverage, publication rules and separately versioned additions.
status: stable
confidence: high
last_updated: 2026-10-12
tags: [evaluation, dfm14, dfm15, multilingual, scheduler]
---
# DFM14 and DFM15 Evaluation Baseline

## Required Coverage

DFM14 full evaluation checkpoints must run the complete inherited standard,
DFM and EuroEval suites, including all 50 languages with available tasks.
The 16 newly added languages supplement, rather than replace, the previous
34. Language coverage alone is not a task-coverage check.

The [exact task inventory](dfm14-evaluation-inventory.md) records names and
shard counts from the non-skipped XL campaign definitions inspected on
2026-10-10, plus the explicitly requested Andersen addition. It is a
versioned baseline, not a claim that both machines already satisfy it.

| Component | Required coverage |
|---|---|
| Standard | MATH, GSM8k, DROP, MMLU, HellaSwag, ARC, Winogrande, BoolQ |
| DFM | All inherited English/Danish knowledge, reasoning, code, summarization, translation and instruction-following tasks in the inventory |
| Multilingual DaLA/GEC | Historical heldouts plus the v2, DFM13 and DFM14 additions; retain distinct task identities |
| EuroEval | Full inherited dataset inventory, including earlier languages and the 16-language extension |
| Andersen modernization | Validation split only, 119 pairs, zero-shot; add to both machines |
| Long context | Separate capability suite when explicitly scheduled for a context-extension campaign; not silently inserted into standard/DFM averages |

Andersen uses `pairs_chunked_val.jsonl`, never the training or combined file.
Its local original is `/work/dfm/andersen/pairs_chunked_val.jsonl`; remote
deployments need an identical, hash-verified copy and a local path override.
Task implementation: `dfm-evals/dfm_evals/tasks/andersen_modernization.py`.
Keep its metrics supplemental unless a versioned average definition includes
them. VALEU is excluded from headline averages; existing historical results
are not deleted or reinterpreted.

## Protocol and Publication

The [training continuity policy](training-continuity.md) takes precedence over
campaign-wide postprocessing barriers: incomplete merges, averages and syncs
must not prevent the next training segment from resuming safely.

- Evaluate the same checkpoint weights/EMA mode with the intended native chat
  template, prompt, shot count, generation limits, scoring and pinned splits.
  A dataset name alone does not establish protocol parity.
- Preserve recorded heldout IDs and source hashes. Recover missing local
  inputs from pinned HF versions rather than sampling fresh test examples.
- Merge each task as soon as all its shards succeed; publish completed
  single-shard tasks and successful merges without waiting for the campaign.
- Never publish an incomplete shard set as a complete benchmark.
- Recompute averages from their explicit population manifests, not whichever
  metrics happen to be present. Expose missing contributors.
- Preserve existing versioned averages: headline/suite v3, semantic successors,
  wave34, DaLA-v2, Talemaader-v2, expanded DaLA-v2 and all-50 populations where
  defined by the campaign. Do not overwrite these with a different denominator.
- Log the exact checkpoint step and fractional epoch to the intended existing
  W&B run. Register metrics explicitly and finalize average values atomically.
- Exhausted eval failures may block their merge/average, but must not prevent
  training resuming once inference and owned servers have terminated safely.

The all-50 population definition is
`config/multilingual_headline_populations_dfm14.json`. Older populations
remain separately named comparisons, not substitutes for it.

## DFM15 Inheritance and Additions

DFM15 inherits **all** of this baseline. Its native-reasoning data changes do
not authorize benchmark removals, prompt changes, or replacement of old scores.
See the [DFM15 data plan](dfm15-plan.md).

Proposed supplementary diagnostics, not yet mandatory production tasks:

| Addition | Purpose |
|---|---|
| Paired thinking-on/off math and reasoning prompts | Measure correctness, final-answer extraction and the cost of thinking |
| Native channel/termination checks | Detect literal legacy think tags, leaked reasoning and missing final answers |
| Direct-answer instruction and formatting checks | Verify that enabling native reasoning does not force thinking everywhere |
| Multi-turn and native tool-call checks | Verify structured calls, supplied tools, tool results and subsequent answers |
| Matched multilingual reasoning probes | Compare new-language behavior without replacing pinned DaLA/GEC populations |

Run new protocols under separate names/prefixes with recorded mode and token
budgets. Establish a reference checkpoint before interpreting changes as gains.
Only add them to an average through a new explicit population/version.

## Cross-Machine Deployment

Git synchronizes code, submodule revisions and tracked configuration, **not**
ignored runtime plan TSVs, local SQLite databases, downloaded heldouts,
absolute machine paths or already running processes. A pull alone therefore
does not harmonize a campaign.

After changing the baseline, compare each upcoming checkpoint's task names,
shards, protocols, merge/publication jobs and average populations against this
inventory on both machines. Apply additions under the scheduler's admin lock,
preserving completed/running jobs. Validate the dependency graph and release
the lock. Do not replay completed evaluations simply to rename a plan.

Use the [shared scheduler runbook](model-architecture/request-shared-eval-scheduler.md)
for local-disk SQLite, persistent servers, 64 clients and server concurrency
1024. GPU utilization, batch sizes, judge reservations, environments and paths
remain machine/model-specific; benchmark parity does not require equal batches.

### Reconciliation status at documentation time

The 2026-10-10 comparison found the local XXL-wide campaign missing 243
EuroEval datasets and 40 historical DaLA/GEC tasks relative to the XL campaign.
The XL campaign lacked Andersen modernization. The local all-50 DaLA/GEC
extension is installed, but does not by itself resolve these other differences.
Full reconciliation remains an operational task; this document must not be
read as a completion receipt.

### 2026-10-12: Local XXL campaign reconciliation installed

The preceding deployment gap is **superseded for local checkpoints 1M and
later**, not for historical 950K results. Remote SSH moved to port **2546**.
The reference is its live SQLite campaign
`/tmp/dfm14-production-3383000/jobs.sqlite`, non-skipped
`dfm14-xl-step_3450000-*` definitions. Snapshot:
`logs/diagnostics/scheduler-parity-20261012/remote-jobs.json`.

The existing local authority `/tmp/dfm14-xxl-wide-production/jobs.sqlite` now
contains the full reference inventory for 1M, 1.05M, 1.1M, 1.15M, 1.2M,
1.25M, 1.3M, 1.35M and final 1,391,204. Each checkpoint has:

- 1,047 inference jobs: 85 standard, 667 DFM, 32 DFM IFEval, 263 EuroEval.
- 2,201 total checkpoint rows, including nine average jobs.
- 853 added rows: 243 EuroEval inference plus 243 merges; 160 historical
  DaLA/GEC shards plus 160 exports and 40 merges; seven additional averages.
- No missing remote inference task/shard identities. Local-only supplements
  remain Andersen modernization and VALEU-da/en; VALEU remains outside averages.

The nine average jobs cover original headline/suite v3, original multilingual,
semantic multilingual, semantic headline/suite, wave34 available populations,
DaLA-v2 populations, Talemaader-v2 successors, expanded DaLA-v2 headline/suite,
and DFM14 all-50 populations. Reference population files are byte-identical;
local artifact roots, W&B identity, step and fractional epoch are retained.
Average jobs depend on the same mapped result contributors as the XL campaign.
Model/batch/memory/judge settings are local, not copied from the smaller XL.

The original 1M inference campaign finished and training resumed while the
reconciliation was being prepared. Do not interrupt that resumed segment.
Its 403 missing inference jobs wait for `xxlw-dfm14-train-1050000`, then run
alongside the expanded 1.05M campaign. Both sets are included in the next
inference-only terminal gate. Exhausted failures and unfinished CPU publication
must not prevent training from continuing after GPU work terminates.

Reconciliation tooling:

- `scripts/prepare_eval_parity_assets.py`: copy and SHA-check exact historical
  test files and producer manifests, create local-path-only configs, retain
  unchanged sample selections, compare scoring implementations across machines.
- `scripts/harmonize_xxl_eval_campaign.py`: idempotent, admin-locked preserving
  SQLite import; no edits to active jobs or training commands; export TSV only
  through `SQLiteJobStore.export_tsv`, never `write_plan` on SQLite authority.
- Assets and receipts: `data/dfm14/evaluation/campaign-parity-20261012/`.
- Backup and deployment receipt: plan's `state.before-full-parity.sqlite` and
  `full-parity-receipt.json` under `logs/scheduler/dfm10_XL_epoch9_20260831/`.

EuroEval is pinned to **18.1.0** for added and pending jobs, matching the remote
installation. Already completed 1M base EuroEval jobs used 17.3.0 and are not
silently rerun or relabeled. Thus task coverage is harmonized, but historical
results are not a claim of identical dependency environments. Dependencies
were installed in a uv-isolated environment, not into production `hrm`.

Verification: all 160 historical DaLA/GEC shard constructors pass with 500
samples each and 2,000 unique samples per task; transferred source hashes and
all population registries validate. EuroEval 18.1.0's guarded CLI starts, and
all 261 reference EuroEval task names resolve in its installed registry.
119 scheduler/averaging tests pass, including idempotence, local model
identity/capacity, deferred supplementation, and inference-only training gates.
