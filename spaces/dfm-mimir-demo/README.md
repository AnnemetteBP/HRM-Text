---
title: DFM Mimir
emoji: "🧠"
colorFrom: red
colorTo: yellow
sdk: gradio
sdk_version: 6.24.0
app_file: app.py
python_version: "3.12"
startup_duration_timeout: 30m
short_description: Chat with the bilingual Danish-English Mimir model
hf_oauth: true
hf_oauth_scopes:
  - gated-repos
models:
  - danish-foundation-models/DFM-Mimir
tags:
  - chat
  - danish
  - english
  - research
---

# DFM Mimir demo

Interactive Danish-English chat with
[`danish-foundation-models/DFM-Mimir`](https://huggingface.co/danish-foundation-models/DFM-Mimir),
an approximately 1.8-billion-parameter HRM-Text model with a 4,096-token
context window.

The demo uses the tokenizer's native chat template with thinking disabled and
runs the model in BF16 on Hugging Face ZeroGPU. Visitors sign in with Hugging
Face and must accept the model licence; their short-lived OAuth credential is
used to verify and load the gated model without a persistent service token.
Mimir is distributed under the
[MIMIR License v1.0](https://huggingface.co/danish-foundation-models/DFM-Mimir/blob/main/LICENSE)
for research use.

Mimir has not been specifically aligned for safety. Its responses may be
incorrect or biased, and users should not submit sensitive information.
