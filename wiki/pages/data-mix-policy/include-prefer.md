---
type: Policy Record
title: Include / Prefer
description: 'Part of Data Mix Policy: Include / Prefer.'
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
# Include / Prefer

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Academic/non-commercial use permits CC-BY-NC sources, but provenance and GDPR/PII concerns still matter.

Good instruction/reasoning sources:

- Sapient non-denied cleaned sources
- `synquid/danish-verifiable-reasoning`
- `synquid/translation-100k`
- `synquid/ifbench-train`
- Oliver Kinch Danish instruction/backtranslation, QA, summarization, and translation sources with public/OPUS provenance:
  - `oliverkinch/instruct-bt` is now approved for the DFM mix after row-level
    access and schema verification on 2026-05-27.
  - Added open sources: `multi-wiki-qa-high-quality-subset`, `eur-lex-sum-instruct`, `machine-translation-da-{en,uk,ar}`, `danmarks-statistik-bt`, `tidsskrift-dk-bt`, `doab-da-bt`, `danish-university-portals-bt`, `eur-lex-bt`, `dynaword-bt`, and `dst-table-prompts-bt`.
- AllenAI Dolci SFT variants
- AllenAI Tulu SFT/persona/reasoning variants
- Nemotron instruction/SWE/terminal/agentic/multilingual, capped by objective
- DynaWord as the only raw continuation source
- Local DBC/LexDK/OPUS instruction-style additions under `data/downloads/datasets`: DBC abstracts/reviews/Faktalink/Forfatterweb, LexDK articles, and OPUS Danish-English translation shards when both language sides are present. These are converted to supervised bibliographic/article-writing/translation tasks, not empty-instruction raw continuation.

Gated sources not downloaded in the earlier `--exclude-gated` run, but intended
for the DFM mix once explicitly downloaded with an authorized token:

- `danish-foundation-models/laerebogen`
- `synquid/wiki-instruct-da`
- `oliverkinch/instruct-bt`
- `synquid/mt-da-deepseek`
- `synquid/wildchat-100k-qwen-messages`, tightly capped because it is generated
  answers to WildChat prompts.
