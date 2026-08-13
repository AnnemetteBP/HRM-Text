---
type: Policy Record
title: DFM5 Non-Danish And Export Additions
description: 'Part of Data Mix Policy: DFM5 Non-Danish And Export Additions.'
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
# DFM5 Non-Danish And Export Additions

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Last updated: 2026-06-12
Confidence: high for implemented config/tree-builder changes; medium for token
targets until `data/show_analytics_dfm5.md` is generated.
Scope: DFM5 policy/config decision implemented locally in
`data_io/prefix_config_dfm5.yaml` and `scripts/build_tokenized_dfm5_tree.py`.

DFM5 also includes:

- Reduced Nemotron SFT: `nemotron_multilingual__`, `nemotron_swe__`,
  `nemotron_agentic__`, and `nemotron_instruction_reasoning_off__`, capped to
  target about `3.1B` tokens per epoch instead of the larger DFM4 exposure.
- DOLCI SFT at the DFM4 rate: `dolci_instruct_sft__`,
  `dolci_instruct_sft_no_tools__`, `dolci_instruct_sft_tool_use__`, and
  `dolci_instruct_sft_tool_use_sa__`.
- Reduced AllenAI/Tulu/reasoning/math/science plus extra `no_robots__`, capped
  to target about `3.1B` tokens per epoch for that family.
- DFM4 summarization tasks from `data/tokenized_dfm4_summarization`:
  `dfm4_arxiv_paper_summarization__`, `dfm4_govreport_summarization__`,
  `dfm4_wiki_cat_sum_summarization__`, and
  `dfm4_laion_scientific_summaries__`.
- Accepted-only export datasets from Common Pile and Danish DynaWord raw-task
  exports, plus accepted transformation exports:
  `common-pile-{denoising,paragraph-reordering,prefix-continuation,span-filling}`,
  `danish-dynaword-{denoising,paragraph-reordering,prefix-continuation,span-filling}`,
  and `transformations-{danish-danish,danish-english,english-danish,english-english}`.

The tokenized DFM5 tree builder was rebuilt on 2026-06-12 after export
tokenization and linked `4,891` kept Sapient tasks, `54` selected Danish mixed
tasks, `139` Nemotron/DOLCI/AllenAI/no_robots tasks, `4,019` DFM4
summarization tasks, and `4,187` accepted export tasks, with no missing kept
Sapient tasks. Total linked task dirs: `13,290`.

DFM5 sampling completed on 2026-06-12 with `epochs=5` and
`concat_workers=1`. Confidence: high. Outputs:

```text
sampled dataset: data/sampled_dfm5
analytics:       data/show_analytics_dfm5.md
stderr log:      logs/sample_dfm5.stderr.log
metadata.total_length: 39,298,245,221 tokens per epoch
```

Final high-level DFM5 sampled distribution per epoch:

| Bucket | Tokens/epoch | Share |
|---|---:|---:|
| Kept original Sapient | `13,682,970,219` | `34.82%` |
| Danish mixed additions | `9,454,480,428` | `24.06%` |
| AllenAI/Tulu/reasoning/no_robots | `5,294,402,580` | `13.47%` |
| Nemotron SFT | `3,752,921,296` | `9.55%` |
| DOLCI SFT | `3,158,545,564` | `8.04%` |
| DFM4 summarization | `1,842,578,300` | `4.69%` |
| Accepted Common Pile exports | `1,115,715,036` | `2.84%` |
| Accepted transformation exports | `696,139,171` | `1.77%` |
| Accepted Danish DynaWord exports | `300,492,627` | `0.76%` |

The 12 accepted export datasets contribute `2,112,346,834` sampled
tokens/epoch after context filtering/truncation. Danish mixed additions plus
accepted Danish DynaWord exports contribute `9,754,973,055` tokens/epoch
(`24.82%`), not counting Danish-English transformation exports or Danish rows
inside multilingual/non-Danish buckets.

DFM5 Lærebogen accounting, inspected locally on 2026-06-12. Confidence: high.
Only the `with_follow_ups` config of `danish-foundation-models/laerebogen` is
downloaded/used locally. It consists of seven Parquet shards with a `messages`
column and `1,294,336` conversation rows. Those rows contain `5,163,949`
assistant turns and `5,163,949` user turns, about `3.99` assistant turns per
conversation. The converter expands each assistant turn into one PrefixLM
training example, so the tokenized tree has `5,163,949` Lærebogen examples.
Superseded 2026-06-12: `data_io/prefix_config_dfm5.yaml` originally set
`laerebogen_with_followups__ repeat: 2`, which sampled `10,326,446`
Lærebogen examples per epoch and `5,126,425,326` covered tokens per epoch.
The repeat was removed on 2026-06-12, so the intended next DFM5 resample should
have about `2.563B` Lærebogen tokens/epoch instead. The current
`data/sampled_dfm5` still reflects the older `repeat: 2` run until it is
rebuilt.

DFM5 repeat audit on 2026-06-12. Confidence: high for current analytics. After
removing the Lærebogen repeat, the largest remaining repeat-driven expansions
are `lexdk__ repeat: 10` (`0.733B` tokens/epoch, saving `0.660B` if set to 1),
`oliverkinch_tidsskrift_dk_bt__ repeat: 10` (`0.482B`, saving `0.434B`),
`synquid_wiki_instruct_da__ repeat: 2` (`0.383B`, saving `0.191B`),
`oliverkinch_dynaword_bt__ repeat: 10` (`0.212B`, saving `0.191B`), and
`dfm4_wiki_cat_sum_summarization__ repeat: 2` (`0.228B`, saving `0.114B`).
All other active repeat rules save less than `0.1B` tokens/epoch if reduced to
one, except `synquid_danish_verifiable_reasoning__` at about `0.084B`.

Update 2026-06-12. Confidence: high. The largest repeat-driven Danish
additions were reduced before the next DFM5 resample:

```text
laerebogen_with_followups__: repeat 2 -> 1
lexdk__: repeat 10 -> 2
oliverkinch_tidsskrift_dk_bt__: repeat 10 -> 2
oliverkinch_dynaword_bt__: repeat 10 -> 2
synquid_danish_verifiable_reasoning__: repeat 10 -> 2
```

Expected reduction relative to the first DFM5 sample is roughly `3.3B`
tokens/epoch, dominated by Lærebogen (`~2.56B`), LexDK (`~0.59B`), and the two
Oliver Kinch backtranslation sources (`~0.56B` combined), with a small
Verifiable Reasoning reduction (`~0.075B`).

Reduced-repeat DFM5 resampling completed on 2026-06-12. Confidence: high.
Superseded on 2026-06-13 by the resample that also includes accepted
`synth_high40__` and `synth_repeat30__` replacement sources.

```text
sampled dataset: data/sampled_dfm5
analytics:       data/show_analytics_dfm5.md
stderr log:      logs/sample_dfm5.stderr.log
metadata.total_length: 35,518,233,884 tokens per epoch
```

Reduced-repeat DFM5 high-level distribution per epoch:

| Bucket | Tokens/epoch | Share |
|---|---:|---:|
| Kept original Sapient | `13,683,037,112` | `38.52%` |
| Danish mixed additions | `5,674,796,733` | `15.98%` |
| AllenAI/Tulu/reasoning/no_robots | `5,294,404,864` | `14.91%` |
| Nemotron SFT | `3,752,524,478` | `10.57%` |
| DOLCI SFT | `3,158,545,564` | `8.89%` |
| DFM4 summarization | `1,842,578,300` | `5.19%` |
| Accepted Common Pile exports | `1,115,715,036` | `3.14%` |
| Accepted transformation exports | `696,139,171` | `1.96%` |
| Accepted Danish DynaWord exports | `300,492,627` | `0.85%` |

Selected reduced Danish sources now contribute:

```text
laerebogen_with_followups:          2,563,212,663 tokens/epoch
lexdk:                                146,638,758 tokens/epoch
oliverkinch_tidsskrift_dk_bt:          96,377,264 tokens/epoch
oliverkinch_dynaword_bt:               42,450,474 tokens/epoch
synquid_danish_verifiable_reasoning:   18,643,694 tokens/epoch
```

DFM5 resampling with synthetic replacements completed on 2026-06-13.
Confidence: high. This is the current `data/sampled_dfm5` state.

```bash
cd /work/dfm/HRM-Text/data_io
ionice -c2 -n7 nice -n 10 python sample_tokenized.py \
  tokenized_path=../data/tokenized_dfm5 \
  output_path=../data/sampled_dfm5 \
  epochs=5 \
  concat_workers=1 \
  prefix_config_path=prefix_config_dfm5.yaml \
  > ../data/show_analytics_dfm5.md \
  2> ../logs/sample_dfm5.stderr.log
```

Outputs:

```text
sampled dataset: data/sampled_dfm5
analytics:       data/show_analytics_dfm5.md
stderr log:      logs/sample_dfm5.stderr.log
metadata.total_length: 35,605,979,095 tokens per epoch
sampled size:    821G
epoch dirs:      epoch_0 through epoch_4
```

The current resample adds accepted synthetic replacement data at one pass per
epoch:

```text
synth_high40:   63,956,698 tokens/epoch
synth_repeat30: 23,679,295 tokens/epoch
```

The total DFM5 epoch is therefore about `35.606B` tokens. At
`global_batch_size=196,608`, this is about `181,101` optimizer steps per epoch
and about `905,504` steps for the 5-epoch sampled dataset, before any final
partial-batch handling in the trainer.

Operational caveat from 2026-06-12: the current tool namespace temporarily lost
the normal `/work/dfm/HRM-Text` path while older processes still held the
checkout open via `/proc/<pid>/cwd`. A `WORKERS=2` tokenizer run using the
normal `/work` path failed with many `No such file or directory` reads once
that path disappeared. This was a mount/path-visibility issue, not evidence
that the accepted export files are broken; direct inspection through
`/proc/478730/cwd` still showed the audited files present and non-broken.

Dry build without the exported DynaWord tokenized tree, verified on 2026-06-12:

```text
sapient_linked_tasks:       4,891
danish_mixed_linked_tasks:     52
danish_export_linked_tasks:     0
total_tasks:                4,943
sapient_missing_tasks:         []
```

The export datasets are `messages` JSONL.GZ. The Rust tokenizer now supports
`.jsonl.gz` rows with a `messages` list and emits one `direct` row per assistant
turn. A one-shard smoke tokenization from
`export/danish-dynaword-paragraph-reordering` produced `tokens.npy` and all
index arrays successfully. Confidence: high.

Clarification, 2026-06-12. Confidence: high. The four exported Danish
DynaWord folders' current `data/*.jsonl.gz` files are not accepted-only
filtered outputs. They are deterministic generated export rows. The
`audit_full/audit.jsonl` and `audit_rebalance_*/audit.jsonl` files record
`keep`/`drop` decisions. To train only accepted rows, first run the export
folder's filter command to create an `audited/` tree and tokenize that filtered
tree instead. `scripts/tokenize_dfm5_danish_exports.sh` currently tokenizes the
`data/` subdirectories only; it avoids audit sidecar JSONL files but does not
apply audit decisions.
