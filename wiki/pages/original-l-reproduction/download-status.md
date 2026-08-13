---
type: Experiment Record
title: Download Status
description: 'Part of Original L Reproduction: Download Status.'
tags:
- reproduction
- sapient
- training
- evaluation
status: stable
last_updated: 2026-05-27
confidence: high
part_of: /pages/original-l-reproduction.md
---
# Download Status

Part of [Original L Reproduction](/pages/original-l-reproduction.md).

On 2026-05-25, Hugging Face metadata for `sapientinc/HRM-Text-data-io-cleaned-20260515` showed `5,213` files matching the original Sapient allow patterns, with total size about `347.79 GB` / `323.90 GiB`. The current checkout resumed this download into:

```text
data/downloads/datasets/sapient_cleaned
```

The downloader was restarted with one worker as a soft bandwidth limiter:

```bash
conda run -n hrm python scripts/download_training_datasets.py --groups sapient --download --max-workers 1
```

This is not a hard bytes-per-second cap; it only limits concurrent Hugging Face transfers. Verified local progress after restart: the partial tree moved from about `30G` to `31G`, while incomplete cache files dropped from `30` to `21`, so the one-worker resume path is working. Confidence: high.

Status, 2026-05-26: the resumed download completed locally. Verification commands reported:

```text
du -sh data/downloads/datasets/sapient_cleaned                           -> 324G
find data/downloads/datasets/sapient_cleaned -name "*.incomplete" | wc -l -> 0
find data/downloads/datasets/sapient_cleaned/data \
     data/downloads/datasets/sapient_cleaned/data_clustered -type f | wc -l -> 5212
```

The downloader's own final summary reported `325.9 GB`, `5222 files`, and scanned `5213` selected Hugging Face files. Confidence: high.

MPS branch partial-data note, 2026-05-25: after stopping a still-running background Sapient downloader, the local partial tree in `/Users/petersk/Nobackup/HRM-Text-mps/data/downloads/datasets/sapient_cleaned` contained `490` completed `.parquet`/`.jsonl` inputs under the original Sapient data roots and `1` incomplete Hugging Face cache file. The completed inputs were tokenized separately into:

```text
data/tokenized_original_sapient_partial
```

Verified output: `490` tokenized metadata files, about `83G` on disk. A final tokenizer validation scan reported `Processing 0 files on 11 threads...`. This is not the full original Sapient reproduction dataset; it is a partial snapshot of the completed files available after the interrupted download. Confidence: high.

The tokenizer was run from the repo root with the already-built release binary:

```bash
cd /Users/petersk/Nobackup/HRM-Text-mps
data_io/tokenizer/target/release/tokenizer \
  data/downloads/datasets/sapient_cleaned/data_clustered \
  data/downloads/datasets/sapient_cleaned/data \
  --tokenizer-path data_io/trained_tokenizers/bpe/tokenizer.json \
  -o data/tokenized_original_sapient_partial \
  --workers 12
```

Operational note: the tokenizer is resumable for completed outputs. Restarting the same command with a higher worker count skipped directories that already had matching metadata and reported only the remaining files. On the M2 Max machine, the 12-worker run used about `6.1G` RSS during the large pass and completed the partial 490-file set. Confidence: high.

Small smoke sample built from three completed tokenized SYNTH shards:

```text
Tokenized subset view: data/tokenized_original_sapient_partial_smoke
Sampled smoke data:   data/sampled_original_sapient_partial_smoke
```

Sampler command:

```bash
cd /Users/petersk/Nobackup/HRM-Text-mps/data_io
conda run -n hrm python sample_tokenized.py \
  tokenized_path=../data/tokenized_original_sapient_partial_smoke \
  output_path=../data/sampled_original_sapient_partial_smoke \
  epochs=1 \
  concat_workers=2
```

Verified smoke sample metadata: `max_seq_len=4097`, `total_length=21,359,878`, output size about `519M`. The sampler covered `60,000` rows from `SYNTH__synth_175.parquet`, `SYNTH__synth_176.parquet`, and `SYNTH__synth_230.parquet`. Confidence: high.

MPS smoke training against that sampled dataset passed two steps outside the sandbox:

```bash
cd /Users/petersk/Nobackup/HRM-Text-mps
conda run -n hrm python scripts/debug_nan_training_step.py \
  --steps 2 \
  --override data.path=data/sampled_original_sapient_partial_smoke \
  --override accelerator_type=mps \
  --override compile_train_batch=false \
  --override fwd_bwd_dtype=float32 \
  --override global_batch_size=64 \
  --override epochs=1 \
  --override lr_warmup_steps=1 \
  --override ema=null \
  --override arch.n_layers=2 \
  --override arch.hidden_size=64 \
  --override arch.num_heads=4 \
  --override arch.expansion=2 \
  --override arch.half_layers=false \
  --override arch.H_cycles=1 \
  --override arch.L_cycles=1 \
  --override +arch.bp_min_steps=1 \
  --override arch.bp_max_steps=1
```

Result: both steps had finite loss, metrics, gradients, parameters, and post-optimizer parameters. Confidence: high.
