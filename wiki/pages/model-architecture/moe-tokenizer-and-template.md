---
type: Decision
title: HRM-MoE Tokenizer and Chat Template
description: Pinned OpenEuroLLM tokenizer, repository-owned ChatML format, and tied-embedding contract for from-scratch HRM-MoE training.
tags: [architecture, hrm, moe, tokenizer, embeddings, chat-template]
status: stable
last_updated: 2026-09-03
confidence: high
part_of: /pages/model-architecture.md
sources:
  - id: openeurollm-tokenizer-128k-v2
    resource: https://huggingface.co/openeurollm/tokenizer-128k-v2
    title: OpenEuroLLM Tokenizer v2 (128k)
  - id: tying
    resource: https://arxiv.org/abs/1608.05859
    title: Using the Output Embedding to Improve Language Models
---
# HRM-MoE Tokenizer and Chat Template

## Settled contract

The primary from-scratch HRM-MoE tokenizer is
`openeurollm/tokenizer-128k-v2`, pinned to immutable revision
`5c1fc6c70779ec84580c2a68d75c6b569b3381f5`. Its vocabulary has 131,072
entries, identity normalization, byte fallback, and fixed core IDs `<unk>` 0,
`<bos>` 1, `<eos>` 2, and `<pad>` 3. The tokenizer card reports coverage of 36
European languages plus code, math, chat, and PDF text; its comparative
measurements are upstream evidence rather than a replacement for a local
corpus-weighted fertility audit.[^openeurollm-tokenizer-128k-v2]

The Sapient tokenizer and the DFM-Mimir/Gemma chat template are not part of
this new model contract. A Gemma tokenizer may later be retained as a measured
control, but it is not the primary training representation. A custom balanced
64k tokenizer remains a possible challenger only after the primary pipeline is
working.

## Chat serialization

The canonical format is the repository-owned
`evaluation/chat_templates/hrm_moe_chatml.jinja`. It emits exactly one BOS,
uses atomic `<|im_start|>` and `<|im_end|>` boundaries with explicit role
names, opens an assistant turn for generation, and terminates complete training
conversations with EOS. The model is trained and evaluated with this same
template; no upstream tokenizer template is inherited implicitly.

The pilot builder validates vocabulary size, fixed core token IDs, and atomic
ChatML markers before reading data. It stores a local tokenizer snapshot,
immutable Hub revision, template path, and template SHA-256 in the generated
dataset metadata. Existing output directories remain fail-closed and are never
overwritten.

## Embedding geometry

The HRM-MoE configuration ties the input embedding table to the output
projection.[^tying] The input path retains the existing runtime embedding
scale, while both paths share one initialized parameter and one accumulated
gradient. Other HRM configurations remain untied unless they explicitly set
`tie_word_embeddings: true`.

At XL width 1,536, the tied 131,072-entry table contains 201,326,592
parameters. Under the current single-exit E4 MoE topology, this reduces the
planned model from the former large-vocabulary geometry to approximately
1,239,422,976 parameters. This count is architectural bookkeeping, not a
quality or throughput claim.

## Validation gates

Before production tokenization, verify the pinned snapshot against a frozen
Danish/English/code/math sample and record fertility, byte fallback incidence,
round-trip fidelity, special-token atomicity, and rendered length. Before a
long MoE run, require the template prefix test, shared-storage embedding test,
one-step backward test, and a real-data B200 smoke. Tokenizer and template are
then frozen for the run; changing either creates a new dataset and model
identity rather than modifying an existing output.

The live data path was exercised on 2026-09-03 with a small sample from each
of the Danish, math, and code streams. Nine rows produced 4,058 train tokens,
all index and token bounds validated, and the saved tokenizer/template snapshot
matched the pinned contract. This verifies the preparation interface and source
schemas; it is not a model-quality result.

[^openeurollm-tokenizer-128k-v2]: OpenEuroLLM tokenizer model card and file metadata, inspected 2026-09-03.
[^tying]: Press and Wolf, 2016.
