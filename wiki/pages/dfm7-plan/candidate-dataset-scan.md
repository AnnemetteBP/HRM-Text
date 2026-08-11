---
type: Plan Record
title: Candidate Dataset Scan
description: 'Part of DFM7 Plan: Candidate Dataset Scan.'
tags:
- dfm7
- data
- training
- evaluation
status: stable
last_updated: 2026-07-02
confidence: medium
part_of: /pages/dfm7-plan.md
---
# Candidate Dataset Scan

Part of [DFM7 Plan](/pages/dfm7-plan.md).

HF namespace scan, 2026-06-30. Confidence: medium from Hugging Face API
metadata/cards and local DFM6 prefix/download manifest comparison. Scanned:
`danish-foundation-models`, `synquid`, `oliverkinch`, and `schneiderkamplab`.
Avoid double-adding datasets already present in DFM6 unless the candidate is a
clear expanded replacement.

Current DFM6 already covers these families from the scanned namespaces:

- `danish-foundation-models/danish-dynaword` via raw/derived DynaWord and
  DynaWord transformation datasets.
- `danish-foundation-models/laerebogen`.
- `synquid/wiki-instruct-da`, `synquid/danish-verifiable-reasoning`,
  `synquid/translation-100k`, `synquid/ifbench-train`,
  `synquid/mt-da-deepseek`, and `synquid/wildchat-100k-qwen-messages`.
- `oliverkinch/instruct-bt`, `oliverkinch/multi-wiki-qa-high-quality-subset`,
  `oliverkinch/*-bt`, `oliverkinch/machine-translation-da-*`, and
  `oliverkinch/eur-lex-sum-instruct`.
- `schneiderkamplab/common-pile-*`, `schneiderkamplab/danish-dynaword-*`,
  `schneiderkamplab/transformations-*`, and `schneiderkamplab/sapient-synth-*`.

High-priority DFM7 candidates:

| Dataset | Category | DFM6 status | DFM7 recommendation |
| --- | --- | --- | --- |
| `danish-foundation-models/dfm-dyna-instruct` | Mixed Danish/English SFT, code, tool-use, refusals | Partly overlaps DFM6; also has new `agentic-code-sft-mix-v1`, `when2call`, `da-refusals`, and `apertus-sft-mixture` | Use as the canonical expanded DFM instruction source if possible, but avoid double-counting existing constituents. Either replace the overlapping individual DFM6/Synquid sources with this collection pinned to a revision, or import only new configs. |
| `synquid/agentic-code-sft-mix-v1` | English code, agentic coding, tool-use | New; also a constituent of `dfm-dyna-instruct` | Include if not using full `dfm-dyna-instruct`. Strong target for code/tool gaps. Card reports `24,192` rows, filtered from NVIDIA code/SWE/OpenCode sources, with `messages`, optional `tools`, and metadata. License metadata is `other`; constituent license review needed. |
| `oliverkinch/danish-qa` | Danish QA/instruction | New | Include after schema/sample inspection. Large relative to other Oliver Danish additions (`100K<n<1M`), CC-BY-4.0 metadata, likely useful for Danish factual QA. |
| `oliverkinch/danish-summarization` | Danish summarization | New | Include, capped. It contains `eur_lex` and `nordjylland` configs; Nordjylland is large. On 2026-06-30 the DFM7 planning decision changed to not treat provenance review as a blocker for this source. |
| `oliverkinch/da-instruct-dynaword`, `oliverkinch/da-instruct-dynaword-hq`, `oliverkinch/da-instruct-dynaword-contemporary`, and `oliverkinch/da-instruct-dynaword-contemporary-hq` | Danish DynaWord instruction/backtranslation | New/expanded relative to `dynaword-bt` | Include all four for breadth, with de-duplication/caps as needed. Supersedes the earlier narrower recommendation to prefer only HQ variants. |
| `oliverkinch/autodata-da-sft` | Danish synthetic SFT from DynaWord/autodata | New | Include small capped slice after sample inspection; license metadata is `other`. |
| `danish-foundation-models/danish-wildchat4.8M` | Large Danish translated WildChat | Expanded replacement for the capped `synquid/wildchat-100k-qwen-messages` idea | Include as the expanded WildChat source for DFM7, replacing the narrow 100k WildChat source if used. Supersedes the earlier privacy/provenance-blocker stance for this planning pass. |
| `danish-foundation-models/ai-arenaen-conversations` / `ai_arena_udtraek` | Danish human conversation/preference data | New | Include as Danish dialogue/alignment data. Supersedes the earlier review-only stance for this planning pass. |
| `danish-foundation-models/multilingual-gsm-symbolic` | Math/reasoning, multilingual | New | Use as eval or seed/source inspiration. Do not train on Danish test splits if used for evaluation. English train splits may be usable; Danish appears benchmark-like rather than train-oriented. |
| `danish-foundation-models/kaenguruen` | Danish math competition MCQ | New | Include for DFM7 training by current policy decision. Convert to explicit Danish MCQ instruction rows preserving choices and target letter. Also keep as a separate eval, but mark DFM7 scores as non-held-out if trained on it. |

Medium/conditional candidates:

- `kobprof/skolegpt-instruct`: Danish instruction SFT from a quality-filtered
  translated OpenOrca subset plus SkoleGPT survey instructions. Consider for
  the next DFM7 rebuild or DFM8, especially if we want more school/education
  and Danish instruction-following coverage. It is probably worth integrating
  with a cap after schema/license/sample inspection, but the expected marginal
  value is lower if the active mix already contains substantial OpenOrca-like
  translated instruction data. Confidence: medium from the public dataset/GitHub
  description, not yet from local rows.
- `oliverkinch/danish-personas`: useful as synthetic persona/control data, but
  not direct instruction supervision unless used to generate dialogue/task
  variants.
- `oliverkinch/eur-lex-sum`, `dst-table-prompts`, `danmarks-statistik`,
  `tidsskrift-dk`, `tidsskrift-dk-en`, and `danish-university-portals`: raw or
  narrow task sources already partly represented by BT/instruct derivatives.
  Prefer using existing instruction derivatives unless DFM7 adds a conversion
  pass for summarization/QA/table reasoning.
- `danish-foundation-models/croco-munin-apertus-8b-da` and `*-gold`:
  preference pairs, not SFT. Useful only if DFM7 includes DPO/preference
  training.
- `schneiderkamplab/DA-Refusals`: include as a small safety/refusal slice if
  not already pulled through `dfm-dyna-instruct`; adult/NSFW tags require
  safety handling.

Likely exclude from training:

- Superseded 2026-06-30: earlier notes excluded
  `danish-foundation-models/kaenguruen` because its access form contains a
  no-training confirmation. Current DFM7 policy decision is to include
  Kaenguruen for training.
- `danish-foundation-models/ifeval-da`, `global-piqa-da`, `linguistic-quality`,
  `synquid/gsm8k-da`, `synquid/wmt24pp`, `schneiderkamplab/SDU-Daisy`,
  `schneiderkamplab/danish-tool-calling-benchmark`, and `oliverkinch/da-bird`:
  better treated as eval/diagnostic or synthetic-data seed material, not direct
  training data, to avoid benchmark contamination.
- `danish-foundation-models/danish-gigaword` and `oliverkinch/danish_wikipedia`:
  raw continuation corpora. Use only if DFM7 explicitly adds raw continuation or
  a conversion/audit pipeline; otherwise prefer instruction/summarization/QA
  derivatives.
- `synquid/wildchat-100k-qwen`: superseded by
  `synquid/wildchat-100k-qwen-messages`, already used in DFM6.

Operational notes:

- If `dfm-dyna-instruct` is used, pin a revision and import by `source`/`task`
  so overlapping DFM6 constituents can be de-duplicated.
- Superseded 2026-06-30: earlier notes required row-level provenance/PII review
  for WildChat/AI Arena before inclusion. Current DFM7 planning says not to use
  provenance as a blocker for these sources; still de-duplicate and cap by
  sampling policy.
- For math, keep benchmark-like datasets out of training unless they provide a
  documented train split that is not part of our eval suite.
