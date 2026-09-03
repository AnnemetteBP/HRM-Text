---
type: Plan
title: Multilingual Long-Context Transfer Research Plan
description: Controlled experiments for positional robustness and cross-language transfer in Danish-centred MiMir models.
tags: [architecture, data, long-context, multilingual, danish, evaluation]
status: draft
last_updated: 2026-09-01
confidence: medium
part_of: /pages/model-architecture.md
sources:
  - id: lost-in-middle
    resource: https://arxiv.org/abs/2307.03172
    title: "Lost in the Middle: How Language Models Use Long Contexts"
  - id: lost-at-birth
    resource: https://arxiv.org/abs/2603.10123
    title: "Lost in the Middle at Birth: An Exact Theory of Transformer Position Bias"
  - id: multilinguality-curse
    resource: https://aclanthology.org/2024.emnlp-main.236/
    title: "When Is Multilinguality a Curse?"
---
# Multilingual Long-Context Transfer Research Plan

## Current boundary

MiMir's current H and L levels both operate on full token-sequence tensors with
dense attention. The proposed local-L/global-H and sparse-H roles are not yet
implemented. The labels H and L therefore do not currently demonstrate that H
has learned language-independent reasoning or that L has learned local syntax.

Sparse attention addresses computational cost, not automatically effective
context use. A router can make middle-context failures worse by failing to
select the relevant block. The 2026 *Lost in the Middle at Birth* paper argues
that a U-shaped influence profile exists in causal residual Transformers at
initialization, but it is a single-author theory preprint and should be treated
as a testable hypothesis rather than an established MiMir diagnosis.

## Coupled evaluation matrix

Create controlled examples at 16K, 32K, and 60K/64K. Place required evidence
at 5%, 25%, 50%, 75%, and 95% of the rendered token sequence. Test single
retrieval, multiple retrieval, aggregation, and multi-hop reasoning; a needle
test alone is insufficient. Cross the position experiment with:

- Danish query, Danish evidence, Danish answer;
- English query/evidence and English answer as the retained-capability control;
- Danish query and answer with Swedish, Norwegian, or English evidence;
- mixed-language distractors, including closely related Scandinavian text;
- native-authored natural documents as well as synthetic controlled facts.

Report an accuracy-by-position curve, middle-to-edge gap, task score, rendered
token length, and language condition. For sparse variants also report router
recall: whether every gold evidence block was selected at each H application.

## Transfer experiment

Do not infer transfer from a single multilingual final run. Hold total tokens,
Danish tokens, context-length distribution, source quality, and optimization
steps fixed. Compare a Danish-English baseline with separate runs that replace
an equal generic-data budget with one added language at a time. Start with
Swedish and Norwegian Bokmål, then test a more distant Germanic control and a
non-Germanic control.

For each source-language addition, measure the change in Danish, English, and
source-language results. This produces a directed transfer matrix rather than
assuming linguistic similarity is always beneficial. Track tokenizer fertility,
held-out native-text loss, instruction following, reasoning, code/math,
cross-lingual retrieval, code-switching, and negative interference. Similarity,
shared script/subwords, domain, data quality, and task alignment are competing
explanations and must not be changed simultaneously.

Use native-authored corpora for language quality. Parallel or comparable
documents may be included as an explicit alignment lane, but direct English
translations must not stand in for native Danish, Swedish, or Norwegian.

## Architecture gates

1. Establish dense-attention positional and language-transfer baselines.
2. Train with uniformly randomized evidence positions and evaluate whether the
   middle-to-edge gap changes without an architecture modification.
3. At up to 32K, test the proposed L sliding-window/H full-attention path
   against the otherwise matched dense model.
4. At 60K/64K and beyond, test MoBA-style H attention against full H attention;
   gate it on multi-hop/aggregation quality and router recall, not throughput
   or needle retrieval alone.
5. Only if mixture experiments show capacity interference, test modular
   language adapters or experts. A plausible HRM experiment is shared H plus
   language-conditioned L, but this is a hypothesis requiring ablation and not
   a property of the current model.

