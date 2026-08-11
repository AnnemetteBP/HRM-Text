---
type: Policy Record
title: Controlled Transformation Data Gap
description: 'Part of Data Mix Policy: Controlled Transformation Data Gap.'
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
# Controlled Transformation Data Gap

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Recorded on 2026-06-04. Confidence: medium for causal attribution; high for
local smoke-test symptoms.

Smoke generations from the original Sapient L epoch-4 checkpoint and the DFM4
XL-DDP step-200000 EMA checkpoint show a specific weakness on controlled text
transformation tasks: exact sentence-count summarization, tense rewriting,
child-friendly simplification, numbered fact extraction, and non-copy rewriting.
The DFM4 checkpoint is more responsive than the original Sapient checkpoint on
some simple English prompts, but both still tend to copy input text or ignore
format constraints on longer transformation prompts.

This is not best treated as a generic "more tokens" problem. Current DFM4 data
already contains broad instruction data and summarization data, including
generated DFM4 summarization tasks from arXiv paper-to-abstract, GovReport,
WikiCatSum, and LAION Scientific-Summaries. Upsampling those can strengthen
summarization, but it will not by itself teach tense conversion, simplification,
exact extraction counts, or robust output-shape compliance.

Recommended remediation order:

- Audit current sampled/converted data for explicit transformation instructions
  with patterns such as `summarize`, `rewrite`, `simplify`, `past tense`,
  `extract`, `numbered`, `exactly`, and `one/two sentences`.
- Add curated public editing/transformation datasets if license and provenance
  are acceptable. Initial candidates to review are `grammarly/coedit` for
  grammar and text editing, `facebook/asset` for simplification seed material,
  and selected Super-NaturalInstructions/NIV2-style rewriting, extraction,
  infilling, and composition tasks. These should be capped and audited rather
  than blindly imported.
- Selectively allow safer Sapient FLAN/Tasksource transformation subsets only
  after source-level review. The broad FLAN/Tasksource deny policy remains the
  default.
- Generate synthetic transformation data from already approved sources
  (DynaWord, LexDK, approved DBC text, GovReport/WikiCatSum/arXiv-derived
  summarization sources, and other accepted corpora). Use programmatic checks
  where possible: sentence count, numbered-list count, length ratio, non-copy
  ratio, language ID, and simple format validation.

Synthetic transformation data should start as a controlled auxiliary component,
not a dominant replacement corpus. A practical first target is roughly 0.5-2B
effective tokens per epoch, then evaluate whether the lite smoke/eval metrics
move before scaling further.
