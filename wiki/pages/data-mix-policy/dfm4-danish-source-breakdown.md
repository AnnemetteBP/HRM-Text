---
type: Policy Record
title: DFM4 Danish Source Breakdown
description: 'Part of Data Mix Policy: DFM4 Danish Source Breakdown.'
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
# DFM4 Danish Source Breakdown

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Last updated: 2026-06-12
Confidence: high
Scope: DFM4 sampled data analytics from `data/show_analytics_dfm4.md`.

`data/show_analytics_dfm4.md` reports `360,035,447,845` covered tokens across
five sampled epochs, or `72,007,089,569` tokens per epoch. Danish-specific
sources in DFM4 account for about `134,864,875,503` covered tokens across five
epochs, or `26,972,975,101` tokens per epoch (`37.46%` of DFM4).

Category totals:

| Category | Tokens/epoch | Five-epoch covered tokens | Share of DFM4 |
|---|---:|---:|---:|
| DynaWord self-supervised tasks | `14.063B` | `70.317B` | `19.53%` |
| Danish instruction/reference/chat | `6.842B` | `34.210B` | `9.50%` |
| Raw Danish continuation | `2.814B` | `14.070B` | `3.91%` |
| Translation | `1.725B` | `8.625B` | `2.40%` |
| Oliver Kinch Danish BT/instruction/reference | `0.887B` | `4.437B` | `1.23%` |
| DynaWord paragraph reordering | `0.641B` | `3.205B` | `0.89%` |

Largest individual Danish sources/tasks by per-epoch tokens:

| Source/task | Category | Tokens/epoch |
|---|---|---:|
| `laerebogen_with_followups` | Danish instruction/reference/chat | `5.126B` |
| `danish_dynaword` | Raw Danish continuation | `2.814B` |
| `dfm2_dynaword_denoising` / `v2` | DynaWord self-supervised tasks | `1.457B` each |
| `dfm2_dynaword_span_fill_v1..v6` | DynaWord self-supervised tasks | about `1.418B` each |
| `dfm2_dynaword_prefix_continuation` / `v2` | DynaWord self-supervised tasks | `1.320B` each |
| `opus` | Translation | `1.032B` |
| `lexdk` | Danish instruction/reference/chat | `0.733B` |
| `dfm4_dynaword_paragraph_reorder` | DynaWord paragraph reordering | `0.641B` |
| `oliverkinch_tidsskrift_dk_bt` | Oliver Kinch Danish BT/instruction/reference | `0.482B` |
| `dbc` | Danish instruction/reference/chat | `0.405B` |
| `synquid_wiki_instruct_da` | Danish instruction/reference/chat | `0.383B` |
| `oliverkinch_machine_translation_da_en` | Translation | `0.315B` |
| `oliverkinch_dynaword_bt` | Oliver Kinch Danish BT/instruction/reference | `0.212B` |
| `oliverkinch_machine_translation_da_ar` | Translation | `0.162B` |
| `synquid_translation_100k` | Translation | `0.108B` |
| `oliverkinch_machine_translation_da_uk` | Translation | `0.101B` |
| `synquid_danish_verifiable_reasoning` | Danish instruction/reference/chat | `0.093B` |
| `synquid_wildchat_100k_qwen_messages` | Danish instruction/reference/chat | `0.086B` |
| `oliverkinch_dst_table_prompts_bt` | Oliver Kinch Danish BT/instruction/reference | `0.055B` |
| `oliverkinch_multi_wiki_qa_high_quality` | Oliver Kinch Danish BT/instruction/reference | `0.048B` |
| `oliverkinch_danish_university_portals_bt` | Oliver Kinch Danish BT/instruction/reference | `0.027B` |
| `oliverkinch_danmarks_statistik_bt` | Oliver Kinch Danish BT/instruction/reference | `0.023B` |
| `oliverkinch_eur_lex_bt` | Oliver Kinch Danish BT/instruction/reference | `0.020B` |
| `oliverkinch_instruct_bt` | Oliver Kinch Danish BT/instruction/reference | `0.017B` |
| `synquid_ifbench_train` | Danish instruction/reference/chat | `0.015B` |
| `synquid_mt_da_deepseek` | Translation | `0.007B` |
| `oliverkinch_eur_lex_sum_instruct` | Oliver Kinch Danish BT/instruction/reference | `0.002B` |
| `oliverkinch_doab_da_bt` | Oliver Kinch Danish BT/instruction/reference | `0.001B` |
