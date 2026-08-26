---
type: Policy Record
title: Oliver Kinch Source Policy
description: 'Part of Data Mix Policy: Oliver Kinch Source Policy.'
tags:
- data
- licensing
- provenance
- privacy
status: stable
last_updated: 2026-08-17
confidence: high
part_of: /pages/data-mix-policy.md
---
# Oliver Kinch Source Policy

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Reviewed on 2026-05-21 from Hugging Face dataset metadata, cards, and sample schemas.

## DFM contributor status

Update, 2026-08-17: the project owner confirmed that both Oliver Kinch and
Synquid work as part of the DFM project. Their authored dataset contributions
(including transformations, synthetic generations, labels, metadata, and
instruction wrappers) are therefore authorized DFM contributions. This does
not replace provenance review for retained upstream text, prompts, or
conversations.

Consequently, an Oliver/Synquid repository does not need Article 3 merely
because its added transformation layer lacks a separate public licence. Article
3 remains relevant only where an incorporated upstream component is not
otherwise covered. Current examples are Synquid's retained DOLCI puzzle prompts
and WildChat conversations/prompts.

Include:

- Public Danish backtranslation/instruction datasets where targets come from CC-BY, EU legal, DST, DOAB, university portal, tidsskrift.dk, or DynaWord-style public provenance.
- Public Danish QA from Wikipedia-derived `multi-wiki-qa-high-quality-subset`.
- Danish translation pairs from `machine-translation-da-en`, `machine-translation-da-uk`, and `machine-translation-da-ar`, with sampling caps because `da-en` is much larger than the other additions.

Exclude by default:

- Raw Oliver Kinch document corpora such as `danish_wikipedia`, `eur-lex`, `tidsskrift-dk`, `tidsskrift-dk-en`, `danmarks-statistik`, `danish-university-portals`, `doab-da`, and `dst-table-prompts`; the current plan allows only Danish DynaWord as raw continuation data.
- `oliverkinch/dsk-bt`; the card says it is derived from non-public internal DSK material and is not intended for public redistribution.
- `oliverkinch/da-bird`; useful as an evaluation/text-to-SQL benchmark, but its Harbor task layout and CC-BY-SA inherited BIRD tasks make it a poor fit for the current mixed training corpus.
- `oliverkinch/dynaword-no-bt`; Norwegian rather than Danish.
- Small/no-license synthetic/demo datasets (`life-in-the-uk-multiple-choice`, `synthetic-qa`, `synthetic-qa-context-qa`, `mt_da_uk`) unless separately justified.

Confidence: medium for source-card safety; high for local manifest/converter support after `py_compile` and downloader dry-run.
