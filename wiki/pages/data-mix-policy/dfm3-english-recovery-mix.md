---
type: Policy Record
title: DFM3 English Recovery Mix
description: 'Part of Data Mix Policy: DFM3 English Recovery Mix.'
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
# DFM3 English Recovery Mix

Part of [Data Mix Policy](/pages/data-mix-policy.md).

Decision recorded on 2026-05-31. Confidence: high for local repo
implementation and Common Pile inventory dry-run; medium for final token
proportions until DFM3 is downloaded/tokenized/sampled and
`data/show_analytics_dfm3.md` is inspected.

DFM3 is the combined remediation run:

- Base: DFM2.
- Add selected Common Pile raw text with DFM2-style objectives using
  `X ~= 2.8B` covered tokens per epoch, matching the DFM2 DynaWord direct
  slice.
- Add another approximate `14B` covered tokens per epoch by raising caps for
  already approved English/multilingual instruction data most likely to help
  English factual, commonsense, and reading-comprehension evals.

Common Pile raw-objective target:

- `1X` direct continuation.
- `1X` prefix continuation, with 25-75% prefix.
- `1X` denoising, with about 10% word corruption.
- `3X` span filling, implemented as three span-fill variants.

Not included in DFM3: paragraph reordering. The DFM2 and DFM3 generators only
emit direct continuation, prefix continuation, denoising, and span-filling
families. A safe follow-up is an additive DFM4-style task source that samples
multi-paragraph documents from both DynaWord and selected Common Pile, shuffles
paragraph order while preserving paragraph contents, and asks the model to
restore the original order. Use response text as the original correctly ordered
document rather than only an index sequence, so target-only training still
teaches fluent reconstruction. Confidence: high for current absence; medium for
the proposed mix until implemented and sampled.

Summarization follow-up candidates:

- Already included/local instruction-style summarization includes DBC abstracts
  and the Oliver Kinch Danish EUR-Lex summarization manifest entry.
- Common Pile `arxiv_abstracts_filtered` contains standalone abstracts, while
  `arxiv_papers_filtered` contains full paper text with abstract-like sections.
  These can be paired by arXiv id or section-extracted to create paper-to-
  abstract summarization tasks, subject to per-record license filtering.
- Common Pile `pubmed_filtered` contains full PubMed Central article text with
  license metadata and can often support article-to-abstract or intro/body-to-
  abstract tasks if an abstract section can be extracted robustly.
- Common Pile `uspto_filtered` has patent text where early summary/object
  sections may be extractable, but this is weaker and noisier than arXiv/PubMed.
- External HF candidates that need explicit license/provenance checks before
  inclusion: `ccdv/pubmed-summarization`, `ccdv/govreport-summarization`,
  `billsum`/`FiscalNote/billsum`, `allenai/multi_lexsum`, `bigbio/multi_xscience`,
  and `laion/Scientific-Summaries`. Avoid news-web summarization corpora such as
  CNN/DailyMail, XSum, and Multi-News by default because they are more likely to
  reintroduce copyrighted-news risk. Confidence: medium.
