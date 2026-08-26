---
type: Analysis
title: DFM9 Article 3 Boundary Accounting
description: Narrow component estimate, top-level provenance triage, and manual-decision counterfactual for DFM9.
tags: [dfm9, copyright, legal, tdm, datasets]
status: draft
last_updated: 2026-08-18
confidence: medium
---
# DFM9 Article 3 Boundary Accounting

This page refines the aggregate result in
[DFM9 Copyright and EU TDM Review](dfm9-copyright-tdm-review.md). It is
engineering/legal triage for the current academic/non-commercial
scientific-research purpose, not legal advice or commercial-use clearance.

## Top-Level-Only Provenance

Eleven effective datasets, totalling 4,971,000,960 tokens per epoch, currently
have only a top-level provenance declaration.

Four require decomposition because the operative source bases differ:

- `common-pile/arxiv_papers_filtered`: group CC BY, CC BY-SA, and CC0 rows by
  retained per-record licence.
- `oliverkinch/danish-summarization`: separate EUR-Lex from
  Nordjylland/DynaWord.
- `oliverkinch/instruct-bt`: separate six DynaWord/open-public subsets from
  three agreement-backed subsets, retaining each agreement subset.
- `schneiderkamplab/opus-da-en-permissive`: retain each OPUS source corpus and
  its licence/notice obligations.

`allenai/big-reasoning-traces` should also be decomposed into GeneralThought,
OpenThoughts, and OpenR1-Math for licence/notice and reproducibility accounting,
although all three currently produce the same permissive clearance headline.

The remaining six are homogeneous for this copyright audit and do not need a
split: `allenai/RLVR-MATH`, `ccdv/govreport-summarization`,
`danish-foundation-models/ai_arena_udtraek`,
`oliverkinch/danish-university-portals-bt`, `oliverkinch/eur-lex-bt`, and
`oliverkinch/eur-lex-sum-instruct`. Privacy or attribution strata can still be
retained without turning them into separate legal-basis nodes.

## Narrow Boundary

The 25,608,805,741.2-token headline is whole-aggregate accounting: if any
component of an effective dataset uses Article 3, all sampled tokens from that
effective dataset are counted. It is not an estimate of Article-3-dependent
expression.

The current narrow estimate is **414,056,526 tokens per epoch**, or **0.518%
of DFM9**:

| Boundary | Estimated sampled tokens/epoch | Method |
|---|---:|---|
| Sapient Tasksource residual | 69,758,538.8 | Exact sampled accounting for 84 residual files under MAN-020. |
| RLVE prompt-expression boundary | 160,437,653 | Apply each RLVE dataset's actual DFM9 sampling ratio to close/constrained, expressive, unavailable-source, and unmatched prompt bins. |
| LongAlign and EuroBlocks in DFM Dyna/Apertus | 183,860,334.5 | Gemma-4-template measurement found 167,379,533 LongAlign tokens and 55,864,889 boundary EuroBlocks tokens before sampling. Scale their 223,244,422-token sum by the Apertus ratio 3,033,512,464 / 3,683,310,696. |

The Sapient figure is exact. RLVE and Apertus are proportional estimates
because aggregate epoch indices do not retain component labels. Exact
reconstruction would require mapping every sampled sequence to its original
component row.

## Without Manual Decisions

Removing a manual decision strictly makes the affected source unresolved; it
does not automatically make Article 3 available or approved. For conservative
risk-envelope planning, substituting Article 3 as the fallback would add **74
effective datasets / 12,340,154,859 tokens per epoch**. Together with the
current four, this yields **78 effective datasets / 37,948,960,600.2 aggregate
tokens per epoch (47.47% of DFM9)**.

The 74 additions are 62 MAN-021 Sapient synthetic derivatives, three DOLCI
aggregates, three MAN-022 ShareGPT mixtures, two WildChat descendants, two
OpenHermes derivatives, and two FLAN-v2/SciRIFF descendants. Decisions nested
inside Sapient or DFM Dyna do not increase the effective-dataset count because
those aggregates already contain an Article 3 dependency; they would enlarge
the narrow component boundary instead.

Across all decisions, including those nested in already-Article-3 aggregates
and eight MAN-021 datasets with an independent direct basis, the deduplicated
manual-decision footprint is 86 effective datasets / 37,985,808,862.2 tokens
per epoch. The decision-by-dataset table is in
`legal/reports/dfm9-manual-acceptances-and-overrides.md`.

The reproducible detailed tables and qualifications are in
`legal/reports/dfm9-audit-status-2026-08-18.md`.
