---
type: Runbook
title: DFM14 accepted CPU release and 900K handoff
description: Resumable CPU release, verified publication and sampling while XXL-wide continues DFM13.
status: draft
confidence: high
last_updated: 2026-10-09
tags: [dfm14, release, sampling, training]
---
# DFM14 CPU Release

**2026-10-09 version decision:** the native-reasoning repair described below
is now a [DFM15 addition](dfm15-plan.md), not a DFM14 update. DFM14's data,
training config and scheduler remain unchanged. Historical DFM14 staging paths
below describe the original build; the completed native stage is relocated to
`data/dfm15/native-reasoning-v2/sampled_dfm15`. Neither repair may be promoted
into live DFM14.

## Eval path recovery (2026-10-09)

The recent cross-machine pull imported `/work/mimir/HRM-Text` absolute paths
into the DFM14 task suite, task registry, and heldout manifest. At 900K,
Inspect failed before generation; retries repeatedly restarted vLLM and
reduced batch size despite `oom_0`. This was not a model or CUDA failure.
Localized these three configs to the existing `/work/dfm` files, verified
every selected/evidence file against its pinned SHA256, and constructed all
128 shards (32 tasks, 64,000 samples) on CPU. The preflight script now also
checks task-module and manifest paths from the actual launcher YAML.
Reset 82 affected failed/retrying rows under the existing plan lock with
attempt zero (original batch 64), preserving completed jobs and four unrelated
historical `valeu-da` failures. Resumed the existing persistent scheduler.
After cross-machine pulls, run `scripts.check_dfm14_eval_extension` using the
Inspect environment before launching these evaluations; config paths are
machine-local and must not be assumed portable.

## Native reasoning and direct-answer policy (2026-10-09)

User decision: the model must support both thinking and non-thinking modes.
Well-formed legacy reasoning examples must become Gemma-native reasoning,
not ordinary answer text with their delimiters removed. This supersedes the
plaintext-only repair policy below. Its staged v1 output must not be promoted.

- Preserve a well-formed trace in a structured reasoning field and its final
  answer separately; render the native thought channel with thinking enabled.
- Repair malformed boundaries on CPU only when the reasoning/final separation
  is unambiguous. Preserve content; do not invent missing answers or silently
  reinterpret quoted markup, code examples, or user text.
- If the reasoning cannot be recovered but an intact final answer can be
  identified, strip the reasoning and retain a non-thinking example.
- Otherwise quarantine the row with a reason for later repair, rather than
  inserting malformed thoughts or speculative answer boundaries into training.
- Keep ordinary instruction/chat and direct-answer supervision non-thinking.
  Do not equate all visible explanations with hidden reasoning or automatically
  duplicate every reasoning example into a direct-answer example.

Implementation requirements: per-example mode selection, structured conversion,
and opt-in native rendering for non-tool assistant reasoning (the shared live
template only renders structured reasoning for tool-call messages). Verify both
modes, multi-turn history, tools, target masking, truncation, and HF/inference
template parity before rebuilding and switching the live dataset. Reasoning
targets must have balanced channels and a retained final response after length
filtering. Record per-source converted/repaired/stripped/quarantined counts and
before/after evidence. Do not reuse flattened v1 text as conversion input: use
the immutable original examples, which retain the reasoning boundaries.

### Native CPU build launched (2026-10-09)

`python -u -m dfm14.build_native_reasoning --workers 16 --sample` stages the
replacement under `data/dfm14/native-reasoning-v2`, using immutable original
source arrays, not v1 outputs. Log: `logs/dfm14/native-reasoning-v2/build.log`.
It runs detached with nice 10, ionice best-effort priority 7, and OMP/MKL threads
1. No GPU generation/auditing or live training changes are involved.

The parser lives in `dfm14/native_reasoning.py`. A separate pinned template is
generated in the staging root: ordinary assistant reasoning is rendered only
with thinking enabled, while the shared template and existing exports remain
unchanged. Current-target reasoning is supervised after the model-turn prefix;
previous assistant thoughts are removed from history while their answers remain.
Modes are selected per example, not by blindly enabling thinking globally.

Explicit answer blocks and missing/duplicate thought openers have conservative
repairs. Nemotron-only handling recovers terminal action JSON incorrectly inside
thoughts, including a lost analysis-key prefix, only when the complete expected
JSON schema parses. Requested visible JSON analysis stays visible. No speculative
semantic repair or new GPU judgment is performed.

If reasoning plus final answer cannot fit 4097 tokens, drop the reasoning and
disable thinking for that example. If the complete answer still cannot fit,
quarantine the row; do not truncate a thought channel or its final answer.
Quarantined rows are removed from sampled selections, preserving the order and
repetitions of retained rows. Every source writes before/after evidence and
quarantine reasons; `repairs.json` summarizes source counts and epoch `repair.json`
reports sampled native-thinking occurrences and removed occurrences. Other
inherited sources are unchanged; no exhaustive absence-of-markup claim is made.

39 CPU tests passed, covering mode/template parity, prompt/target boundaries,
history, tool syntax, malformed cases, length limits, quarantine and sampled-row
redirection. This is not an end-to-end GPU inference validation. The build will
produce `sampled_dfm14/ready.json` only after full index validation. Promotion,
packed-step-budget adjustment, and a checkpoint-safe handoff remain separate.
Measure retained sampled exposure before claiming that mode balance is sufficient;
the intended learned behavior is explicit thinking-mode control, not autonomous
selection of when to reason.

### Native reasoning existed before this conversion

Read-only sample on 2026-10-09 of 10,000 randomly selected live DFM14 epoch_0
rows (NumPy seed 142026, without replacement) found 15 response targets with
`<|channel>thought` (0.15%) and zero prompts containing `<|think|>`.
Three inspected hits mapped through original DFM11 backing offsets to
`nemotron_agentic__data__interactive_agent.jsonl`, inherited from NVIDIA's
Nemotron Agentic corpus. One explicitly had a thought channel followed by a
native `get_product_details` tool call. This is evidence of prior native
reasoning exposure, not a full census or proof that all hits have that source.
The historical template renders tool-call reasoning regardless of the
`enable_thinking` switch, explaining the observed thought targets without
thinking-enabled prompts. Thus the new conversion expands and regularizes
mode-controlled reasoning; it does not introduce thought tokens for the first
time. Existing inherited tool-call examples are not changed by this scoped repair.

## CPU reasoning-wrapper repair (2026-10-08, superseded policy)

**Superseded 2026-10-09:** historical implementation below is not the approved
native-reasoning policy and its staged output is not approved for training.

At the user's request, `python -m dfm14.repair_reasoning --workers 16 --sample`
repairs the five inherited affected source families and the Norwegian stray
prompt delimiter identified below. The current staged policy keeps reasoning
as visible step-by-step text under DFM14's existing non-thinking contract;
it does not enable hidden thinking or insert `<|think|>` into assistant text.
Legacy think/answer serialization wrappers are removed deterministically.
Nested and orphan delimiters have explicit tests; ambiguous remaining markup
blocks publication. This is format repair, not a new semantic quality audit.

The job verifies affected token ranges against the frozen sampled corpus,
keeps originals immutable, writes replacement arrays and changed rendered-row
evidence, then builds a separate sample preserving row order, repetition and
unaffected examples. Changed rows are redirected to repaired token storage;
the old backing remains present but is no longer selected for those rows.
Lengths and per-epoch token totals are recalculated and fully bounds-checked.
No live path is replaced automatically: a checkpoint-safe switch and updated
packed-step budget are required before training uses the staged output.

- Work directory: `data/dfm14/reasoning-repair-v1`.
- Staged result: `data/dfm14/reasoning-repair-v1/sampled_dfm14`.
- Completion gate: `sampled_dfm14/ready.json`, status `validated_staged_not_promoted`.
- Log: `logs/dfm14/reasoning-marker-repair/build.log`.
- Tests: `tests/test_dfm14_reasoning_repair.py` (16 passing after malformed-tag cases).

The full pass also found meta-commentary referring to quoted think tags.
The repair modernizes recognized prose references to the word "reasoning",
preserving the actual solution; it does not erase arbitrary code examples.
An ordered one-shot continuation waits for the initial CPU pool to finish,
reuses completed parts, and retries failed/unfinished parts with these rules
before sampling. Its log is `logs/dfm14/reasoning-marker-repair/resume.log`.

The initial failed frozen-range comparison was a diagnostic's final-chunk
slice-length bug, not a corpus mismatch; it was fixed before rewriting data.

## Literal reasoning-marker audit (2026-10-08)

Read-only diagnostic `scripts/audit_dfm14_reasoning_markers.py` decoded 78,441
rows across 1,393 active source groups: DFM11 base (153 groups), corrected DFM12
(360), DFM13 (603), and DFM14 (277). Each group samples up to five parts and
20 random rows per part with a deterministic seed. DFM11 repeat-zero and
cap-zero routes are excluded. These are tokenized source-reservoir samples,
not a census or epoch-weighted prevalence estimate; rare leaks can be missed.

Confirmed assistant-target literal `<think>`/`</think>` occurrences:

| Source | Sample rows with target markers |
| --- | ---: |
| `allenai/big-reasoning-traces` | 100/100 |
| `allenai/open_math_2_50k_r1-original` | 20/20 |
| `allenai/verifiable-reasoning-filtered-gpt-41` | 99/100 |
| `allenai/verifiable-reasoning-filtered-o4-mini` | 22/40 |
| `nvidia/Nemotron-Terminal-Corpus`, local `nemotron_terminal_corpus_native__` / materialized `schneiderkamplab/dfm10-nemotron-terminal-sft` | 100/100 |

All five enter through the inherited DFM11 base. The Norwegian addition
`schneiderkamplab/dfm12-norwegian-magpie-qwen3-bokmaal` had a stray `</think>` in
one sampled prompt (1/20), not its supervised response. No matching markers
were found in the 23,940 sampled rows of the 277 DFM14 additions, or the
31,036 sampled DFM13 rows. This is not proof that those populations are clean.
The disabled composite `dfm_dyna_instruct/.../danish-verifiable-reasoning`
also contains tags, but is not an active exposure; the direct Synquid route
had zero hits in 20 samples. Repaired OpenMathInstruct2 and both modernized
OpenHermes routes had zero hits in 100 samples each.

Root cause: the Nemotron terminal converter preserves content verbatim; the
generic tokenizer also preserves message content. The shared Gemma template's
`strip_thinking` macro strips native channel spans, not plain `<think>` XML.
`enable_thinking=False` therefore does not sanitize these inherited targets.
DFM14's specific native-instruction adapter extracts leading think blocks and
rejects unconverted control markup, but it is not applied retroactively to
inherited arrays. Native `<|think|>` enables thinking in the system turn;
actual thought text uses channel delimiters, so replacing the literal XML tag
with `<|think|>` directly would not be a correct repair.

Evidence with source-part paths, row indices, decoded prefixes and excerpts:
`logs/dfm14/reasoning-marker-audit/source-sample.jsonl`.
No training datasets, conversions, or runtime settings were changed by this audit.

## 874K pause correction (2026-10-08)

The completed `ephemeral_step_874000` was preserved under
`checkpoints/dfm14/XXL-wide-paused-874000`. Launcher SIGINT left seven orphaned
NCCL workers spinning after the launcher exited. These exact training workers
were terminated; all eight GPUs then reported zero utilization and memory.
The scheduler remains stopped. The checkpoint-stop helper now snapshots child
process identities before interruption and waits for/terminates surviving
workers rather than treating launcher exit as sufficient proof of shutdown.

Later on 2026-10-08, resume was requested: the existing 900K training row was
reset to resume from the preserved 874K checkpoint, and the scheduler restarted.
At launch all eight GPUs had only about 8.5 GiB free; admission remains gated
on GPU availability, without terminating unrelated processes.

## Idle-gated resume (2026-10-07)

XXL-wide was stopped after preserving complete `ephemeral_step_873000` in
`checkpoints/dfm14/XXL-wide-paused-873000`. The existing scheduler is paused.
`scripts/resume_dfm14_after_idle.py` samples all eight GPU utilization values
every 10 seconds and requires 300 consecutive seconds of zero readings.
It then terminates only the snapshotted Mimir vLLM servers on ports 8200-8207
and their children, waits for GPUs to be empty, and updates the existing
900K training row to resume from the preserved 873K checkpoint.
Log: `logs/training/dfm14_XXL_wide/resume_after_idle.log`.
This is a one-shot operational watcher, not a general inactivity guarantee
between utilization samples. Replacement server processes are not targeted.

## Cross-machine inheritance mismatch (2026-10-07)

The initial remote DFM14 release inherited a smaller DFM13 population:
107,001,314,620 tokens rather than the active XL machine's 128,379,257,908.
Its 113.88B-token DFM14 sample was therefore not a complete successor.
**Superseded on 2026-10-07:** the reconciled release below replaces that sample.
Use `completion.json` with `inheritance_reconciled=true` and its authoritative
`inheritance-reconciliation/published.json`, not the old `release-v1/sampling.json`.

Local epoch-0 pointer-array totals (prompt plus target, including repeats):
DFM11=103215092251; DFM12=106800253588; DFM13=128379257908.
These are summed from `inst_len.npy` and `resp_len.npy`, not inferred from
token-store size or metadata `total_length`.

## Cross-machine XL Integration (2026-10-07)

The incoming main-branch DFM14 task registrations and local registrations use
the same paired-heldout reader and scorers; keep one implementation. Local
eval manifests relocate the pinned remote files to this machine without
changing their contents or selection. Population validation supports the
16 new, 48 non-Danish/non-English, and all 50 languages. The available-metric
policy is explicit; existing population metric bindings remain unchanged.

`dfm14.prepare_evals` prepares source heldouts on their owning machine;
`scripts/prepare_dfm14_eval_extension.py` imports those verified selections.
The local XL continuation is separate from `dfm14.continue_training`, which
targets the other machine's XXL-wide checkpoint and plan. Do not run that
XXL-wide publisher to continue XL. See the
[XL 3250K handoff](dfm14-xl-3250k-handoff.md) for the transfer-ready gate and
constant base LR of `3e-4`.

The owner authorized completion of the CPU-side release on 2026-10-07. All
source audits, the broad translation audit and synthetic generation/review
have finished. The eight owned shared Gemma servers were stopped via their
supervisor's `servers/stop.request`; unrelated processes were not terminated.

XXL-wide resumed from the fully verified `ephemeral_step_866500` in
`checkpoints/dfm13/XXL-wide-from-dfm11-epoch2`. The existing scheduler is
`logs/scheduler/dfm10_XL_epoch9_20260831`; training retains BP8, GAS4,
GBS262144, automatic module LRs with base 3e-4, FP32 FSDP parameters,
BF16 compute, no activation checkpointing and `fsdp_reshard_after_forward=false`.
W&B remains `DFM5/dfm10-xxl-wide`. Training advanced after restore at about
2.85 seconds per optimizer step.

## Boundary Safety

DFM13 runs to 900K. The successor depends on `xxlw-dfm14-ready-at-900000`,
a real checkpoint wait for the isolated DFM14 handoff view in
`data/dfm14/xxl-wide-handoff/resume`, tag `step_900000`. That view must not be created
until the dataset, uploads and resume cursor are verified. The DFM13 wrapper
also refuses training targets above 900K. Future plan commands still need the
DFM14 handoff update; merely completing the CPU release does not start DFM14.

## CPU Pipeline

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false \
  /home/ucloud/miniforge3/envs/hrm/bin/python -u -m dfm14.build --workers 16
```

Detached log: `logs/dfm14/cpu-release-v1.log`.
Progress and evidence: `data/dfm14/release-v1/`.
Packages: `exports_dfm14/`. Sample destination: `data/sampled_dfm14`.
Configuration: `config/data/dfm14.yaml`; source registry is written after
verified publication as `config/dfm14_sources.json`.

The pipeline verifies input/journal/receipt hashes, selects accept decisions
only, preserves legacy accepted synthetic slots, and keeps both directions of
accepted translation pairs. Repair requests, rejected rows and failed reviews
are not admitted. It reuses the published, train-only DaLA components and their
token arrays; inherited DFM13 data are not retokenized.

English repeats: two for the selected Smol constraints/rewrite/summarize and
SmolTalk2 components; one for Smol Magpie Ultra, OpenCoder and UltraChat.
Other new components default to one; inherited repeats remain unchanged.

New chats use the existing native Gemma tokenizer/template, disabled thinking,
and final-assistant supervision with complete untruncated history. Targets
over 4,096 tokens are explicitly counted as holds, not silently truncated.
This mirrors the final-target additions contract; it does not claim that all
audited conversations fit the current training context.

Normalized exact benchmark checks use the repository's eight-benchmark Mimir
manifest. Exact chat duplicates across additions are removed. Exact inherited
prompt/response token pairs are removed before sampling using a vectorized
shortlist followed by full token comparison. Neither check establishes semantic
or translated benchmark decontamination. Standalone uploaded packages may still
overlap inherited sources; the mixture, not the public source package, removes
that overlap.

HF nested columns (`messages_json`, `tools_json`, `provenance_json`, `audit_json`)
are lossless JSON strings to avoid incompatible Arrow tool schemas. Decode with
`json.loads`; do not train on serialized JSON. Source attribution and applicable
upstream/teacher conditions remain attached; no blanket permissive relicensing.

Three deterministic epoch sets are prepared over the three existing DFM13
epoch sets. Sampling metadata is published last after index bounds and token
count checks. A single-writer build lock and atomic stage receipts allow resume.
`completion.json` is written only after all HF packages have pinned revisions
and verified remote content hashes. Until then, DFM14 is **not ready**.

## Accepted Packaging Progress (2026-10-07)

All 31,789 input jobs passed receipt/native preparation. They contain 9,266,422
accepted source records, producing 12,907,279 eligible directional conversations
and 4,673,224,668 native prompt/target tokens before deduplication/repeats.
Held explicitly: 2,069 over-context targets and 55 exact benchmark matches.
Cross-addition chat deduplication removed 581 rows, leaving **12,906,698 rows
in 245 packages**. These figures exclude the already published DaLA components.
Packages exist locally; this snapshot does not claim all uploads or sampling
have finished.

Historical synthetic checks can contain successful check records, not only an
empty list; the release verifies their `passed=true` values. Older per-turn
reviews require every recorded criterion to pass. Knowledge-pilot rows lacking
an ID receive a stable job/slot ID, never a random ID. Language variants such
as `pt_pt` are preserved in row metadata and use hyphens in HF repository names.
Fifteen focused release/production/instruction tests pass.

The inherited three epoch pointer multisets differ. Exact overlap removal
therefore scans all three. Its shortlist probes tokens throughout the prompt
and response; template suffixes alone would produce excessive collisions for
DaLA/classification tasks. Only complete token equality excludes a target.

## Sampling Repair and Coverage (2026-10-07)

Superseded: the first release attempt passed filtered index arrays together
with the original full token store to the sampler. Its allocation assumes
complete original indices, so concatenation failed (189,570 source tokens
versus a 117,892-token destination). No source tokens were corrupted.

The fixed integration uses existing `selection_indices_path` support, with
unaltered original arrays and token stores. Retained row ordinals are recovered
from the completed deduplication outputs and all four index fields are checked
for exact equality. No new overlap scan, tokenization or audit is needed.
Seven focused tests pass, including a real sampler subprocess checking retained
token offsets. `min_resp_length=1` preserves valid short DaLA targets.

Overlap removal excluded 360,098 added prompt/response pairs. Every packaged
source retains rows. Additions contribute 6,879,561,807 tokens and 41,424,816
row occurrences per epoch after repeats. Sampling additions succeeded; merged
sampling and publication must still finish before declaring readiness.

`python -m dfm14.release_coverage` reconciles the pinned input inventory,
generation targets, eligible rows, package selections and upload receipts.
Reports: `data/dfm14/release-v1/coverage.json` and
`docs/reports/dfm14-release-coverage.md`.

Important shortfall: the English synthetic math pilot has zero accepted rows,
not a missing converter/export. Jobs finished with answer-contract errors.
Do not claim that all planned generation targets were achieved or admit failed
rows without a separate repair/review. Other English knowledge families and
all six families for each of the sixteen new languages have eligible data.

## Inheritance Discrepancy Discovered (2026-10-07)

The size comparison exposed an unresolved snapshot mismatch. The local XXL-wide
DFM13 was built from `data/dfm13_build/remote/sampled_dfm12`: 106,799,766,039
tokens/epoch, comprising DFM11 plus only 3,585,161,337 addition tokens. Its frozen
`data/dfm13_build/sources.json` has 13 additions, while the current checked-in
DFM13 registry has 312. The final remote authoritative composition files are
not present locally. The documented later XL DFM12 no-identity sample has
117,000,690,762 tokens, including 13,785,598,511 addition tokens.

Thus the apparent DFM12-to-DFM13 reduction is NOT established as an intentional
sampling reduction. It compares different release snapshots. The local DFM14
113,880,339,621-token sample inherits this older DFM13 snapshot. Earlier
mechanical readiness claims do not establish complete planned inheritance.
Keep the 900K handoff gated until authoritative membership is reconciled;
valid new package publication can proceed independently. Do not overwrite
the running DFM13 sample or claim all later DFM12/13 sources are included.

## Authorized Rebuild And Resume (2026-10-07)

The user stopped training and authorized rebuilding DFM12, DFM13 and DFM14,
then immediately resuming on DFM14. This supersedes the earlier 900K-only
handoff: the last complete checkpoint is `step_870000` in
`checkpoints/dfm13/XXL-wide-from-dfm11-epoch2`. Training and the scheduler were
stopped; unrelated package publication was allowed to finish.

The authoritative remote is reachable at `ucloud@ssh.cloud.sdu.dk:2850`, root
`/work/mimir/HRM-Text`. Its final composition pins **381 DFM12 components plus
603 approved DFM13 components**, with four explicit source-fidelity holds.
All thirteen additions in the frozen local DFM13 are covered. Importing the
remote sampled XL corpus directly would incorrectly enable XL identity repeats.
Instead, `python -m dfm14.reconcile_inheritance` rebuilds from local DFM11 and
the pinned tokenized composition, keeping all model identity components at
repeat 0. MATH repeat 5 and Setur/fo-instruct repeat 10 are retained.

Transferred 104,022,540,713 bytes, covering 1325 DFM12 and 7692 DFM13 tokenized
parts. Verified weighted additions: DFM12 48,859,993 rows / 13,785,598,511 tokens;
DFM13 80,662,659 rows / 11,170,372,396 tokens per epoch. Three index sets are
built at every level. DFM14 reuses accepted tokenized additions but recomputes
exact overlap against the corrected inheritance. No retokenization is required.

Build workspace: `data/dfm14/inheritance-reconciliation`; log:
`logs/dfm14/inheritance-rebuild.log`. Outputs stay isolated until full bounded
index scans, token totals, source counts and publication checks pass. Earlier
release readiness is marked `superseded_incomplete_inheritance`, not erased.

`python -m dfm14.continue_training watch` waits for validation, retains old
samples as recovery copies, and promotes the new samples using symlinks. It
uses a private hardlinked checkpoint copy with independent sidecar, resetting
only the dataset cursor to zero at dataset epoch index 2, preserving step
870000, optimizer/EMA, historical rewarm and current hyperparameters. The new
checkpoint directory is `checkpoints/dfm14/XXL-wide-from-dfm13-step870000`.
W&B remains `peter-sk-sdu/DFM5/dfm10-xxl-wide`; BP8, GAS4, GBS262144 and base
LR3e-4 with auto recurrence dividers remain unchanged.

Resume log: `logs/dfm14/rebuild-resume.log`. The watcher modifies the existing
`dfm10_XL_epoch9_20260831` plan under lock, replacing only obsolete pending
DFM13 continuation rows. It retains 50K evaluations, adds 32 new-language
DaLA/GEC tasks (four shards each), and keeps old suite averages separate from
new multilingual averages. CPU preflight verified 2000 unique samples per
task and 500 per shard. Epoch axes continue from the actual pre-switch row
fraction, not from a fabricated integer boundary. Exact remaining steps are
counted using the same multipack/GAS settings before launch.

Create `data/dfm14/inheritance-reconciliation/training/cancel` to cancel the
automatic continuation before launch. A failed rebuild never authorizes resume.
At documentation time rebuilding is active, not yet promoted or training.

### Duplicate Attribution From The First Build

The completed scan against the OLD 107B DFM13 sample removed 360,098 added
targets. Joining excluded token-index ordinals back to package row provenance
attributes 347,078 to `HuggingFaceTB/smoltalk`, 11,687 to
`CohereLabs/aya_dataset`, 545 to `IlyaGusev/saiga_scored`, and 788 to eleven
other upstream repositories. These are incoming-source attributions, not
identification of which inherited dataset contains the matching target.
Exact details: `data/dfm14/release-v1/duplicate-provenance.json`.
These counts must NOT be presented as the completed corrected-inheritance scan,
which was still running when this attribution was produced on 2026-10-07.

### Superseded: Inherited Duplicate Scan Disabled

Later on 2026-10-07 the user explicitly disabled the inherited-example scan.
The scan and resume watcher were stopped, and the rebuild restarted using the
already validated DFM12/DFM13 corpora. All accepted DFM14 additions are now
sampled with their configured repeats, without subtracting inherited matches.
`dfm14/selection.json` records `inherited_overlap_policy: keep_all`; sampler
rules use the original arrays without `selection_indices_path`. The earlier
completed duplicate counts remain historical evidence, not the new selection.
Existing package-level quality filters and prior cross-addition deduplication
are unchanged. Full index/token accounting validation and guarded automatic
training resume remain enabled. This supersedes the overlap-filtering steps
described above, not the source-level inheritance reconciliation.

The user additionally requires training to wait for free GPUs. The existing
all-GPU scheduler reservation requires at least178000MiB free per GPU. The
DFM14 segment wrapper now rechecks GPUs0-7 immediately before torchrun: all
eight must meet that threshold AND have no compute clients. It polls every120s,
fails closed on GPU-query errors, honors stop/cancel requests, and never kills
unrelated GPU processes. This covers external processes not tracked by the
scheduler, including small clients that would pass the memory-only threshold.

The corrected keep-all build subsequently passed validation and was promoted:
DFM14 has406830651rows/epoch,135548235716mean tokens/epoch, and three index sets.
Exact packing gives521204optimizer steps for one full pass with GBS262144/GAS4;
the resumed total is1391204from step870000. After a user-requested stop during
the initial launch (before any new checkpoint), the user authorized resume again.
The existing scheduler was restarted with the cancellation cleared and the
interrupted attempt reset. GPUs were occupied by unrelated clients at restart;
training waits for availability rather than terminating them. W&B/run settings
and the private step870000 resume checkpoint remain unchanged.
