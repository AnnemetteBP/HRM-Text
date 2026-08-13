---
type: Plan Record
title: Sampling Status
description: 'Part of DFM6 Plan: Sampling Status.'
tags:
- dfm6
- data
- training
- evaluation
status: stable
last_updated: 2026-06-28
confidence: high
part_of: /pages/dfm6-plan.md
---
# Sampling Status

Part of [DFM6 Plan](/pages/dfm6-plan.md).

Update 2026-06-20. Confidence: high from local command output.

The DFM6 tokenized union was rebuilt from
`data/tokenized_dfm6_direct_jinja` into `data/tokenized_dfm6` after fixing
`scripts/build_tokenized_dfm6_tree.py` to strip the raw
`export-upload__` prefix for selected uploaded datasets. The rebuilt union
contains:

- `6,456` selected task directories;
- `4,891` allowed Sapient task directories, with no missing allowed Sapient
  tasks;
- all `70` `sapient-synth-*` synthetic replacement datasets;
- all `12` Common Pile, Danish DynaWord, and `transformations-*` derived
  upload dataset families;
- `1,427` selected upload-derived task directories.

The prefix audit was written to `logs/dfm6_prefix_audit_latest.json`. The only
zero configured prefixes were stale `synth_high40__`/`synth_repeat30__` names
and `allenai_code_meta_reasoning__`, which remains a known raw-text converter
gap rather than an intentional DFM6 exclusion.

Five-epoch sampling was launched in tmux session `dfm6_sample_5epochs`:

```bash
cd /work/dfm/HRM-Text/data_io
/home/ucloud/miniforge3/envs/hrm/bin/python sample_tokenized.py \
  tokenized_path=/work/dfm/HRM-Text/data/tokenized_dfm6 \
  output_path=/work/dfm/HRM-Text/data/sampled_dfm6 \
  prefix_config_path=/work/dfm/HRM-Text/data_io/prefix_config_dfm6.yaml \
  epochs=5 \
  concat_workers=1
```

Log: `logs/dfm6_sample_5epochs_20260620_100332.log`.

At launch-time monitoring, token concatenation completed and wrote
`data/sampled_dfm6/tokens.npy` at about `756G`. The process then entered
`Generating epoch indices: 0/5`; no epoch directories had been written yet.

Completion and validation update, 2026-06-20. Confidence: high from local
validation, decoding, and FSDP smoke output.

Superseded by the corrected-cap update below: the first DFM6 sample completed
successfully but accidentally used uncapped default exposure for shared
Sapient-style prefixes such as broad `flan__` and `SYNTH__`. It reported
`98,533,525,792` tokens per epoch and was used to validate the Gemma template
and sampler path, but should not be used for DFM6 training.

Corrected-cap sampling completed successfully into `data/sampled_dfm6` after
the DFM6 policy was clarified:

- DFM6 inherits DFM5 caps/repeats for every shared prefix unless
  `data_io/prefix_config_dfm6.yaml` explicitly overrides that prefix for a
  deliberate DFM6 upscale.
- Broad Sapient `flan__`, `SYNTH__`, `tasksource__`, and related original
  prefixes now use inherited DFM5 caps/repeats.
- `nemotron_swe__` is explicitly excluded with `max_per_file: 0` for the
  current sample. The huge `nemotron_swe__data__swe.jsonl` artifact has no
  usable rows at 4k context under the current PrefixLM truncation rule because
  its prompts are too long; it should only be revisited through a dedicated
  conversion/windowing path.
- The 756G `tokens.npy` backing store was reused with
  `sample_tokenized.py reuse_tokens=true`; only epoch indices and metadata were
  regenerated.

Corrected sample:

- `metadata.json` reports `max_seq_len: 4097`,
  `tokenizer_info.vocab_size: 262144`, and
  `total_length: 56,257,414,878` tokens per epoch.
- Total 5-epoch sampled exposure is about `281.29B` tokens.
- The backing `tokens.npy` has shape `(202,740,907,136,)`, dtype `int32`,
  about `756G` on disk.
- Each of `epoch_0` through `epoch_4` has
  `190,531,808` rows and the four expected index arrays.
- A 5,000-row-per-epoch bounds sample verified positive prompt lengths,
  response lengths at least 2, and in-bounds prompt/response spans.

Decoded task-level examples from `data/tokenized_dfm6` confirmed Gemma chat
template rendering:

- flat Sapient rows decode as `<bos><|turn>user ... <|turn>model` plus a
  supervised response ending in `<turn|>`;
- Common Pile and Danish DynaWord derived rows decode as normal user/model
  chat turns;
- Nemotron Agentic/SWE rows include Gemma tool/thought/tool-call tokens such as
  `<|channel>thought`, `<|tool_call>`, and `<|tool_response>`.

Smoke datasets were built from real sampled DFM6 rows:

- `data/sampled_dfm6_smoke`: `2,048` rows and `566,220` tokens for dataloader
  validation.
- `data/sampled_dfm6_train_smoke`: `49` rows and `14,375` tokens for a tiny
  training smoke.

The dataloader smoke passed with `target_only: true`, vocab size `262144`,
shifted max sequence length `4096`, packed 4096-token batches, and masked
prompt labels with supervised assistant-response labels.

A direct non-distributed `distributed_strategy=none` train smoke failed because
that path leaves FA4 inputs in FP32, while FA4 requires FP16/BF16/FP8. This is
not the intended training path for DFM6. The intended FSDP path was then tested
successfully:

```bash
cd /work/dfm/HRM-Text
CUDA_VISIBLE_DEVICES=0 WANDB_MODE=offline \
WANDB_DIR=/work/dfm/HRM-Text/logs/wandb_smoke_dfm6_xxs_fsdp \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/ucloud/miniforge3/envs/hrm/bin/torchrun --nproc_per_node=1 pretrain.py \
  data=dfm6 \
  data.path=data/sampled_dfm6_train_smoke \
  arch/size@arch=XXS \
  epochs=1 \
  global_batch_size=4096 \
  gradient_accumulation_steps=1 \
  accelerator_type=sm100 \
  distributed_strategy=fsdp \
  fsdp_params_precision=fp32 \
  compile_train_batch=false \
  log_interval=1 \
  checkpoint_path=checkpoints/smoke/dfm6_xxs_fsdp_train_smoke \
  project_name='DFM6 Smoke' \
  run_name='dfm6-xxs-fsdp-train-smoke' \
  hydra.run.dir=.
```

Result: `3/3` optimizer steps completed, W&B offline run wrote finite training
losses, and the run checkpointed to
`checkpoints/smoke/dfm6_xxs_fsdp_train_smoke`.

Corrected approximate mutually exclusive token allocation per epoch, computed
from the actual tokenized tree and `prefix_config_dfm6.yaml` after
sampler-style truncation/cap/repeat logic:

| Bucket | Tokens / epoch | Share | Rows / epoch | Notes |
|---|---:|---:|---:|---|
| English/general/other | `16.08B` | `28.6%` | not recomputed in final audit | capped Sapient FLAN/SYNTH plus DOLCI no-tools, Common Pile, Tulu SFT, transformations |
| Code/math/tool/reasoning | `24.07B` | `42.8%` | not recomputed in final audit | Nemotron Agentic/reasoning-off, OpenMath/ACE/OpenThoughts, DOLCI tool-use, AllenAI, Sapient math/reasoning |
| Danish-language sources | `16.11B` | `28.6%` | not recomputed in final audit | Laerebogen, OPUS, Danish DynaWord, transformations, Wiki Instruct DA, DBC/LexDK/Oliver Kinch/Synquid |

The allocation sum differs from `metadata.total_length` by only about
`184K` tokens due to expected-row averaging for capped random subsets. Danish
math/reasoning/tool rows are counted in the code/math/tool/reasoning bucket
when they match that bucket first.

DFM5 comparison, computed on 2026-06-20 with the same mutually exclusive bucket
rules from `data/tokenized_dfm5`, `data_io/prefix_config_dfm5.yaml`, and
`data/sampled_dfm5/metadata.json`. Confidence: high for the local computation;
medium for semantic bucket labels because they are filename/prefix heuristics.

DFM5 metadata reports `35,605,979,095` tokens per epoch. The bucket estimate
sums to `35,606,064,216`, within about `85K` tokens of metadata:

| Bucket | DFM5 tokens / epoch | DFM5 share | DFM6 tokens / epoch | DFM6 share |
|---|---:|---:|---:|---:|
| English/general/other | `16.85B` | `47.3%` | `64.78B` | `65.7%` |
| Code/math/tool/reasoning | `12.36B` | `34.7%` | `25.87B` | `26.3%` |
| Danish-language sources | `6.40B` | `18.0%` | `7.88B` | `8.0%` |

Interpretation: DFM6 is much larger per epoch than DFM5, so English/general
and code/math/tool/reasoning both increase substantially in absolute tokens.
Danish also increases in absolute tokens, but its share drops because DFM6 adds
and upscales much more English/general and tool/code/math data. Token counts
are not perfectly tokenizer-comparable because DFM5 uses the HRM 65k tokenizer
and DFM6 uses the Gemma 262k tokenizer.

DFM5-superset audit update, 2026-06-20:

The current `data/tokenized_dfm6` / `data/sampled_dfm6` artifact is not yet a
strict source-level superset of DFM5. The issue is implementation coverage, not
a new data-policy exclusion, except for the separate deliberate
`nemotron_swe__` cap of zero.

Verified local findings:

- `dolci_instruct_sft`, `nemotron_multilingual`,
  `allenai_tulu_v2_sft_mixture`, `allenai_tulu_v2_sft_long_mixture`,
  `allenai_verifiable_reasoning_gpt41`,
  `allenai_verifiable_reasoning_o4mini`, `allenai_sciriff_train_mix`,
  `allenai_if_sft_verified`, and `allenai_tulu_3_personas_algebra` are present
  under `data/downloads/datasets`, `data/filtered_sources`, and
  `data/converted_sources`, but have zero corresponding task dirs in
  `data/tokenized_dfm6_direct_jinja`. They were omitted from
  `scripts/build_dfm6_chat_source_tree.py`.
- DFM4 summarization sources are present in the raw DFM6 Jinja-tokenized tree
  as `converted_sources_dfm4_summarization__dfm4_*`, but
  `scripts/build_tokenized_dfm6_tree.py` does not select or strip that wrapper
  prefix, so the sampled DFM6 union sees zero `dfm4_*_summarization__` rows.
- Row comparison after sampler-style filtering/caps/repeats:
  DFM5 has `92,418,825` rows per epoch; current DFM6 has `190,531,808` rows
  per epoch. Missing DFM5 categories in current DFM6 include
  `dolci_instruct_sft` (`2,453,517` DFM5 rows/epoch),
  `dfm4_laion_scientific_summaries` (`2,288,807`),
  `allenai_tulu_v2_sft_mixture` (`748,824`),
  `allenai_tulu_v2_sft_long_mixture` (`532,023`),
  `nemotron_multilingual` (`396,000`),
  `dfm4_wiki_cat_sum_summarization` (`307,822`),
  `allenai_verifiable_reasoning_gpt41` (`284,811`),
  `dfm4_arxiv_paper_summarization` (`213,354`),
  `allenai_verifiable_reasoning_o4mini` (`172,000`),
  `allenai_sciriff_train_mix` (`117,983`),
  `allenai_if_sft_verified` (`31,733`),
  `allenai_tulu_3_personas_algebra` (`20,000`), and
  `dfm4_govreport_summarization` (`8,304`).
- Old DFM5 synthetic placeholder categories `synth_high40` and
  `synth_repeat30` are absent by those exact names, but DFM6 contains the
  renamed `sapient-synth-*` export datasets. That is a naming migration, not
  necessarily content loss.

Confidence: high for the local counts and path checks; medium for treating the
omissions as accidental until the source-builder intent is patched and audited.

DFM6 superset-fix token estimate update, 2026-06-20:

Supersedes the earlier pre-fix DFM6 distribution estimate above for planning
purposes. After adding the missing DFM5 source families to
`scripts/build_dfm6_chat_source_tree.py` and `scripts/build_tokenized_dfm6_tree.py`,
the in-progress raw Gemma/Jinja tokenized tree had `10,521` completed metadata
files. Applying `data_io/prefix_config_dfm6.yaml` with sampler-style filtering,
4097-token context truncation, caps, and repeats estimated `61.58B` tokens per
epoch before the two remaining tail files finish.

Provisional high-level distribution from completed files:

| Bucket | Tokens / epoch | Share |
|---|---:|---:|
| Code/math/tool/reasoning | `23.54B` | `38.2%` |
| English/general/other | `21.81B` | `35.4%` |
| Danish-language sources | `16.23B` | `26.4%` |

This is above the intended 2026-06-20 rebalance target of roughly `56B` tokens
per epoch (`16B` English/general/other, `24B` code/math/tool/reasoning, `16B`
Danish-language). Danish and code/math/tool/reasoning are close to target, but
English/general/other is roughly `5.8B` over target before the final tail files.
The final sampled artifact should therefore be audited after resampling, and a
follow-up cap pass is likely needed if the 56B target should be held tightly.

Confidence: high for the local tokenized metadata computation; medium for the
semantic bucket labels because they are prefix-based.
