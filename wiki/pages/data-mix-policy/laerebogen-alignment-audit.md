---
type: Analysis
title: Laerebogen Random Alignment Audit
description: Reproducible manual review of question-answer alignment and conversation coherence in ten converted Laerebogen examples.
tags: [datasets, danish, laerebogen, quality, alignment]
status: draft
last_updated: 2026-08-26
confidence: medium
---
# Laerebogen Random Alignment Audit

## Scope and method

On 2026-08-26, ten rows were sampled uniformly without replacement from the
5,163,949 converted assistant-turn examples in
`data/converted_sources/laerebogen_with_followups/with_follow_ups`. These are
the actual PrefixLM instruction/response pairs produced from the
`with_follow_ups` configuration: prior turns are serialized into the
instruction, and the response is the next assistant turn. Python
`random.Random(20260826).sample(range(5163949), 10)` selected global indices:

```text
385159, 617014, 1064393, 1291993, 1722483,
2597279, 3980211, 4290774, 4457657, 5067903
```

This is a small diagnostic sample, not a population estimate. Review separates
alignment of the response with the latest user request from coherence of the
entire serialized conversation.

## Findings

| # | Global index | Latest Q/A | Whole conversation | Assessment |
|---:|---:|---|---|---|
| 1 | 385159 | aligned | coherent | Appropriate formal rewrite of an informal job-application sentence. |
| 2 | 617014 | aligned | coherent | Directly answers where to store recovery codes. Advice to keep codes in a bag is weaker than best security practice but not a topic mismatch. |
| 3 | 1064393 | aligned | coherent | Adds responsibility and initiative as requested, but invents a specific display redesign and resulting sales increase that the user never supplied. |
| 4 | 1291993 | aligned | coherent | Answers the status request, but invents a live repair state and ETA. This is acceptable only if the exchange is understood as drafting/role-play. |
| 5 | 1722483 | partial | coherent | Addresses which animals can inhabit fresh and marine water, but gives materially questionable taxonomy/ecology: it names `braskhaj` rather than a freshwater-tolerant shark such as `tyrehaj`, and overstates the lake/sea classification. |
| 6 | 2597279 | aligned | incoherent | Correctly answers the latest yoghurt substitution question, but the serialized history begins with an unrelated table-tennis request before abruptly switching to yoghurt. |
| 7 | 3980211 | misaligned | incoherent | The latest question follows a Danish real-estate answer, while the response discusses Shakespeare and H. C. Andersen. It appears to rely on missing context from another conversation. |
| 8 | 4290774 | aligned | coherent | Concise and directly responsive, despite the deliberately odd premise of missing one's own birthday party. |
| 9 | 4457657 | aligned | incoherent | Answers the latest bicycle-chain question, but the preceding turn is an unrelated police-trust survey. The ruler threshold is also technically imprecise and the answer contains a typo. |
| 10 | 5067903 | aligned | incoherent | Answers the latest green-bond question, and it follows the immediately preceding energy-renovation turn, but the conversation begins with an unrelated crime-analysis exchange. Some financial mechanisms are asserted without support. |

## Interpretation

- Latest-turn topical alignment: **8/10 aligned, 1/10 partial, 1/10
  misaligned**. Counting the factually flawed but topical row gives 9/10
  topical relevance.
- Whole-conversation coherence: **6/10 coherent and 4/10 incoherent**.
- At least one row is a clear target mismatch. Three additional rows preserve
  a relevant latest-turn pair but contain unrelated earlier turns, which
  teaches abrupt topic transitions as if they were a coherent dialogue.
- Separate quality risks include invented biographical/operational facts,
  unsafe or weak advice, and factual errors. Alignment-only filtering would
  not catch these.

The observed failure modes justify a larger stratified audit before changing
the complete source. A useful next pass should separately estimate
latest-turn mismatch, cross-topic history splicing, unsupported personal or
operational claims, and factual correctness.
