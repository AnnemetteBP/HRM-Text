---
type: Runbook
title: Mimir HF Export Tokenizer Path
description: Recovery procedure for HF exports whose dataset metadata retains the retired /work/dfm tokenizer path.
tags: [evaluation, export, tokenizer, migration]
status: stable
last_updated: 2026-08-31
confidence: high
---
# Mimir HF Export Tokenizer Path

The DFM8 sampled-data metadata records the tokenizer as
`/work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json`. After migration to
`/work/mimir`, that path is absent and causes `conversion/convert_to_hf.py` to
fail before loading checkpoint weights.

The verified local replacement is:

```text
/work/mimir/brainsurgery/models/gemma4_31b
```

It was downloaded from `google/gemma-4-31B` and verified to have a `262144`
token vocabulary with `pad=0`, `eos=1`, and `bos=2`, matching DFM8 metadata.

Export scheduler rows on this filesystem must set:

```json
{"export_tokenizer_path": "/work/mimir/brainsurgery/models/gemma4_31b"}
```

`run_export_hf` passes this value to `conversion/convert_to_hf.py` as
`--tokenizer_path`. This explicit override is preferable to modifying immutable
checkpoint or sampled-corpus metadata and keeps older artifacts interpretable.

The DFM8 XXL step-200000 export failed six times on 2026-08-29 because the
override was absent. Its checkpoint itself was complete and valid; only the HF
conversion failed.

The campaign's terminal barrier intentionally permits later training to resume
after terminal eval failures. Consequently, the step-200000 to step-250000
training segment started after the failed export. Resetting the export makes
the 200K eval graph runnable again, but the GPU-backed full export waits until
training releases the GPUs. A config-only conversion verified the corrected
tokenizer and HF config before the row was reset.

## Step-250000 recurrence (2026-08-31)

The DFM8 XXL step-250000 export again exhausted six attempts even though its
plan row contained
`"export_tokenizer_path":"/work/mimir/brainsurgery/models/gemma4_31b"`.
The traceback shows `simple_inference_engine.inference_load_checkpoint()`
calling `AutoTokenizer.from_pretrained()` with the stale metadata value
`/work/dfm/brainsurgery/models/gemma4_31b/tokenizer.json`. The scheduler
override therefore did not reach or supersede tokenizer loading during this
conversion path. The checkpoint was complete and training correctly resumed
from `step_250000`; only the 250K export and dependent evaluations were left
unrun. Fix the conversion/load propagation before resetting this export row.

## Durable fix and 250K recovery

On 2026-08-31, tokenizer metadata generation was changed to store paths
relative to the repository root. DFM7/DFM8/DFM10 preparation now defaults to
`../brainsurgery/models/gemma4_31b/tokenizer.json`; newly generated tokenizer
metadata also records `tokenizer_path_base: repo_root`. The live
`data/sampled_dfm8/metadata.json` and DFM8 XXL checkpoint
`train_metadata.yaml` were repaired to the same portable value.

The immediate conversion defect was fixed separately:
`conversion/convert_to_hf.py` now passes its already-resolved tokenizer path
into `simple_inference_engine.inference_load_checkpoint()`, so checkpoint
loading cannot independently fall back to stale training metadata. The
regression test is `tests/test_hf_export_tokenizer_override.py`; it and the
campaign tests passed. A config-only conversion from `step_250000` also passed.

Training was stopped only after all eight DCP shards and metadata for
`ephemeral_step_252500` were complete and size-stable. The 250K export and its
full dependent evaluation graph were reset under the plan lock. The corrected
export succeeded and all eight GPUs entered evaluation. The remaining epoch-1
training row is pending behind `campaign-teardown-250000` with
`resume_from_tag=ephemeral_step_252500`, so it resumes automatically after the
terminal evaluation barrier even if an individual evaluation fails.
