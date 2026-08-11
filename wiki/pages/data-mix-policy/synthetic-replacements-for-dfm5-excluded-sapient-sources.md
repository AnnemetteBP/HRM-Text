---
type: Policy Record
title: Synthetic Replacements for DFM5-Excluded Sapient Sources
description: 'Part of Data Mix Policy: Synthetic Replacements for DFM5-Excluded Sapient
  Sources.'
tags:
- data
- licensing
- provenance
- privacy
status: stable
last_updated: 2026-06-17
confidence: high
part_of: /pages/data-mix-policy.md
---
# Synthetic Replacements for DFM5-Excluded Sapient Sources

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Added on 2026-06-12. Confidence: high for source identification,
initialization, and active launch; medium for final inclusion until generated
rows are inspected after the run finishes.

The 321 original Sapient source files excluded from DFM5 are not reintroduced
verbatim. Instead, the current experiment creates synthetic anonymized
replacement datasets under `synth/`, one folder per excluded source file. The
intent is to preserve broad task coverage while removing direct dependence on
the problematic original text.

Local source audit artifacts:

```text
logs/data_audits/dfm5_excluded_original_sapient_sources.tsv
logs/data_audits/dfm5_excluded_original_sapient_tasks.tsv
logs/data_audits/dfm5_excluded_original_sapient_tasks.summary.json
```

Per-row policy:

- generate a new anonymized `condition` / `instruction` / `response` row with
  Gemma 4 31B IT served by vLLM;
- judge the candidate with the same model;
- keep only rows where the judge accepts task preservation, PII replacement,
  low textual overlap, and useful training quality;
- reject rows with unchanged PII-like strings or high local 5-gram overlap.

The initialization command created all 321 per-source folders and manifests:

```bash
cd /work/dfm/HRM-Text
python scripts/synthesize_anonymized_sapient_exclusions.py --init-only
```

The 8-GPU run is managed in tmux session `sapient_anonymization_8gpu`.
Current active run after the high-priority/concurrency update:

```text
logs/sapient_anonymization_20260613T074509
```

Earlier log root `logs/sapient_anonymization_20260612T185643` records the
superseded failed launch where vLLM imported DeepGEMM and required `CUDA_HOME`.
The launcher now disables DeepGEMM for this run.

Resume correction, 2026-06-12: the initial sharded implementation appended all
workers for a source into the same `data/train.jsonl.gz`, which corrupted the
gzip stream. The corrupted early `Platypus_reclor` files were quarantined in:

```text
synth/Platypus_reclor.jsonl/corrupt_20260612T214749/
```

The active run now writes shard-specific files such as:

```text
synth/<source>/data/train.shard00000of00008.jsonl.gz
synth/<source>/rejected/rejected.shard00000of00008.jsonl.gz
```

Quality gate tightened on 2026-06-12: accepted rows require all judge booleans
to be true (`keep`, `substantially_different`, `pii_changed`,
`low_textual_overlap`, `task_preserved`, `quality_ok`) plus the local
5-gram/PII heuristic. A local audit before resuming found that all 469 already
accepted ReClor rows passed this stricter condition.

Priority narrowed on 2026-06-13: the active campaign no longer attempts all
321 excluded sources. It uses the explicit 40-file `high40` priority list:
ReClor/SciBench, QReCC dialogue QA, AESLC email summarization, iDebate opinion
abstracts, selected Niv2 summarization/NewsComm/MS MARCO/DialogRE tasks,
Tasksource sarcasm, and Tasksource ReClor. Huge WMT/translation and broad
review/sentiment/social sources are excluded from this generation campaign.
The active run uses concurrency `8` per GPU worker; vLLM logs show
`Running: 8 reqs` per GPU server.

Superseding runtime detail, 2026-06-13. Confidence: high. The active high40
campaign was restarted with `CONCURRENCY_PER_SHARD=128` and `MAX_NUM_SEQS=128`
after adding per-GPU vLLM/Triton/TorchInductor cache directories. A follow-on
`repeat30` priority set was added to
`scripts/synthesize_anonymized_sapient_exclusions.py` for 30 high-repeat-like
remaining sources: paper-review tasks 264/265/266, deceptive-opinion-spam
tasks 902/903, selected NewsComm translation tasks 1371/1373/1374/1375/1376/1377,
Rotten Tomatoes opinion abstracts, and Allegro review tasks 634/635, each in
fsopt/zsopt variants where present. The watcher command below waits for the
current high40 workers and vLLM servers on ports 8900-8907 to exit, then
launches the repeat30 run with the same 8-GPU settings:

```bash
cd /work/dfm/HRM-Text
tmux new-session -d -s sapient_anonymization_repeat30_after_high40 \
  'cd /work/dfm/HRM-Text && scripts/watch_and_run_sapient_repeat30.sh'
```

As of 2026-06-13 09:28 Europe/Berlin this watcher is active. A fresh
30-second measurement found high40 had `96,366` rows remaining and repeat30
has `77,464` rows, for `173,830` remaining rows total. At the measured
`1,836 rows/min` total throughput, the joint ETA was about `95 min`
(`1.6 h`). Confidence: high for row counts and local process state; medium for
ETA because source lengths and rejection retries vary.

Update, 2026-06-13 10:14 Europe/Berlin. Confidence: high. As high40 shards
finished on GPUs 3 and 4, those high40-owned vLLM servers were stopped and a
separate opportunistic repeat30 two-GPU run was launched in tmux session
`sapient_anonymization_repeat30_gpus34` via:

```bash
cd /work/dfm/HRM-Text
scripts/run_sapient_repeat30_opportunistic_gpus34.sh
```

This uses ports `8913` and `8914` and processes repeat30 shards `3/8` and
`4/8`. The full repeat30 watcher
`scripts/watch_and_run_sapient_repeat30.sh` was updated and restarted so it
waits for any opportunistic repeat30 workers/servers before launching the full
8-GPU repeat30 run.

Update, 2026-06-13 10:21 Europe/Berlin. Confidence: high. The coarse
all-at-once repeat30 watcher was superseded by per-GPU recovery/reuse logic.
Because the original high40 launcher owned and cleaned up its vLLM child
servers, stopping that launcher caused the remaining high40 workers/servers to
exit. The run is resumable from shard-specific accepted/rejected row IDs, so a
recovery chain was launched in tmux session
`sapient_anonymization_recover_high40_then_repeat30`:

```bash
cd /work/dfm/HRM-Text
scripts/run_high40_then_repeat30_remaining_gpus.sh
```

This starts vLLM servers on ports `8900`, `8901`, `8902`, `8905`, `8906`,
and `8907`, resumes high40 shards `0/8`, `1/8`, `2/8`, `5/8`, `6/8`,
and `7/8`, then runs the matching repeat30 shards on the same servers.
Repeat30 shards `3/8` and `4/8` continue in
`sapient_anonymization_repeat30_gpus34` on ports `8913` and `8914`.

Bug found and fixed, 2026-06-13. Confidence: high. The anonymization script's
Parquet iterator initially yielded row indices local to each PyArrow record
batch. Because the batch size is 2048, generated `source_row_id` values
repeated every 2048 rows for Parquet sources. This made resume accounting
incorrect for interrupted/restarted Parquet files: rows in later batches could
be counted as `skipped_existing` even though only an earlier batch-local row ID
was present. The code now uses a cumulative offset in
`iter_source_rows()` so future Parquet `source_row_id`s are global row indices.
Existing rows written before this fix may contain duplicate `source_row_id`
values for Parquet sources; affected missing/skipped row IDs cannot be
reliably reconstructed from those IDs alone. A diagnostic TSV was written to
`logs/data_audits/high40_missing_or_skipped_row_ids.tsv`, but it reflects the
old duplicate-ID limitation and should not be treated as exact provenance.

Clean rerun decision, 2026-06-13. Confidence: high. The current partial
repeat30 outputs were also started before the global Parquet row-index fix, so
they were not reliable for source-to-synthetic row mapping even though they had
no `skipped_existing` resume contamination. The decision is to rerun all
Parquet-based high40 sources and all repeat30 sources from scratch with the
patched script. Old outputs are quarantined, not deleted.

The clean rerun is managed by:

```bash
cd /work/dfm/HRM-Text
tmux new-session -d -s sapient_anonymization_clean_parquet_repeat30 \
  'cd /work/dfm/HRM-Text && scripts/rerun_high40_parquet_and_repeat30_clean.sh'
```

This writes task manifests:

```text
logs/data_audits/high40_parquet_sources_all.txt
logs/data_audits/repeat30_sources.txt
```

and then runs:

1. all high40 Parquet sources (`38` files);
2. validation for duplicate/missing IDs, skipped-existing counts, and 8 shard
   summaries;
3. all repeat30 sources (`30` files);
4. the same validation for repeat30.

The rerun started on 2026-06-13 at 10:56 Europe/Berlin in tmux session
`sapient_anonymization_clean_parquet_repeat30`. Initial log:
`logs/sapient_anonymization_clean_high40_parquet_repeat30_20260613T105618.log`.

High40 inclusion update, 2026-06-13. Confidence: high. The accepted rows from
the re-synthesized high40 campaign are now included in the DFM5 tokenized union
under a separate `synth_high40__` prefix. They are intentionally not linked
under original Sapient task prefixes, so sampling can cap/repeat generated
replacement data independently from original Sapient data.

The active tokenizer input tree is:

```text
data/synth_high40_sources/
```

It is built from accepted files only:

```text
synth/<source>/data/train.shard*.jsonl.gz
```

The tree builder merges the eight accepted shard files for each source into one
cleaned `train.jsonl.gz` per source, keeping only `condition`, `instruction`,
and `response`.

Superseded intermediate state. One high40 source initially had zero accepted
rows and was skipped:

```text
flan__niv2_fsopt_data__task1370_newscomm_classification.parquet
```

Inspection of that skipped source on 2026-06-13. Confidence: high. All `4,835`
rows were attempted, and each row reached the configured `3` attempts. The main
failure was the local 5-gram overlap heuristic rather than the LLM judge:
`heuristic_keep` failed on `14,468` attempts. The task is a language
classification task with a repeated option list and short multilingual snippets,
so many otherwise-valid rewrites still retained enough repeated prompt wording
or target text to exceed the overlap gate. The judge also flagged some copied
text (`1,430` attempt-level `copied_text` failures), but most judge records had
`primary_failure_type: none`. Operational failures were minor by comparison:
`11` no-JSON responses, `10` timeouts, and a few JSON parse errors.

Recovery update, 2026-06-13. Confidence: high. The overlap heuristic was fixed
to remove repeated enumerated label inventories before computing the local
5-gram overlap ratio while still recording raw overlap for audit. Existing
rejected attempts for the skipped high40 source were then reprocessed with:

```bash
cd /work/dfm/HRM-Text
python scripts/recover_synth_rejections_with_current_heuristic.py \
  flan__niv2_fsopt_data__task1370_newscomm_classification.parquet --force
```

This recovered `4,137` accepted rows and left `698` rows rejected. The high40
merged/tokenized source set now contains all `40` source files.

Commands that worked:

```bash
cd /work/dfm/HRM-Text
scripts/tokenize_synth_high40.sh
scripts/tokenize_synth_repeat30.sh
python scripts/build_tokenized_dfm5_tree.py --force
```

Resulting local counts:

```text
data/synth_high40_sources/manifest.json:
  source_count: 40
  linked_source_count: 40
  input_file_count: 320
  output_file_count: 40
  row_count: 190,464

data/tokenized_dfm5_synth_high40:
  tokenized source tasks: 40
  accepted samples: 190,464
  tokens: 63,956,698

data/synth_repeat30_sources/manifest.json:
  source_count: 30
  linked_source_count: 30
  input_file_count: 240
  output_file_count: 30
  row_count: 63,783

data/tokenized_dfm5_synth_repeat30:
  tokenized source tasks: 30
  accepted samples: 63,783
  tokens: 23,679,295

data/tokenized_dfm5/union_manifest.json:
  synth_high40_linked_tasks: 40
  synth_repeat30_linked_tasks: 30
  total_tasks: 13,360
```

Sampling policy in `data_io/prefix_config_dfm5.yaml`:

```yaml
- prefix: "synth_high40__"
  repeat: 1
- prefix: "synth_repeat30__"
  repeat: 1
```

Tokenizer bug fix discovered during this inclusion. Confidence: high. The
synthetic `.jsonl.gz` shard files can contain multiple gzip members because
some shards were appended/resumed. Python `gzip` reads these correctly, but the
Rust tokenizer previously used `flate2::read::GzDecoder`, which only read the
first gzip member. This made the first high40 tokenization produce only one
sample per shard (`312` samples total). The tokenizer now uses
`flate2::read::MultiGzDecoder`, and a smoke test on
`train.shard00000of00008.jsonl.gz` for `Platypus_reclor` produced `613`
samples instead of `1`.
