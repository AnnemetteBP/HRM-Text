# DFM Mimir v1 Information for Downstream Integrators

**Status:** Draft  
**Audience:** Non-commercial research integrators under the MIMIR License

## Model Summary

DFM Mimir v1 is an approximately 1B-parameter HRM-Text causal text-generation
model trained from scratch for Danish and English. It supports general
instruction following, question answering, translation, summarisation,
mathematical reasoning, code generation, and structured tool-call generation,
with material capability variation between tasks.

## Intended and Acceptable Uses

Permitted uses are governed by the MIMIR License v1.0 and are limited to
non-commercial research use. The model is not approved for fully automated
decisions where qualified human judgment is legally required, unlawful
biometrics/surveillance, intentional serious unlawful harm, or unlawful
exploitation of children. A separate plain-language use policy remains pending.

## Technical Specifications

| Property | Value |
|---|---|
| Architecture | `HrmTextForCausalLM` / `model_type=hrm_text` |
| Parameters | Approximately 1B |
| Hidden size | 1,536 |
| H/L layers | 16 per stack (`32`, `half_layers=true`) |
| Attention heads | 12 |
| Context | 4,096 model tokens |
| Vocabulary | 262,144 |
| Input/output | Text / text |
| Special tokens | BOS `<bos>`, EOS `<turn|>`, PAD `<pad>` |
| Chat format | Gemma 4 native chat template distributed as `chat_template.jinja` |
| Weight format | safetensors, packed vLLM-compatible projections |

## Required Serving Semantics

1. Render conversational prompts with the distributed Gemma 4 chat template
   and an assistant generation prompt.
2. Stop generation on `<turn|>`.
3. Preserve HRM PrefixLM behavior. Serving engines that silently use ordinary
   causal attention may produce materially different or worse results.
4. Use an HRM-Text-capable Transformers/vLLM version. The current tested local
   reference has PyTorch 2.11.0, Transformers 5.12.1, Tokenizers 0.22.2, vLLM
   `0.23.1rc1.dev102+ga46abb7ae`, FlashAttention 4
   `4.0.0b14.dev5+g4178915.d20260520`, Safetensors 0.8.0, and Accelerate 1.13.0.
   See `legal/registers/current-serving-environment.csv`. Release-time
   environment attestation remains a human-required record. [HUMAN REQUIRED:
   LEG-023]
5. The production export uses packed `gqkv` and `gate_up` tensors for native
   vLLM. Generic Transformers implementations may expose split Q/K/V/gate
   modules but the validated loader maps the packed export.

## Integration Dependencies

- GPU and framework requirements depend on serving engine and requested
  context/batch size.
- FlashAttention-compatible PrefixLM support is required for production-equivalent
  serving.
- Do not assume generic OpenAI chat defaults match the distributed template.
- Freeze and disclose framework versions, attention backend, dtype, tokenizer
  hash, template hash, generation parameters, and model revision in evaluations.

The local release export is frozen in
`legal/registers/release-artifact-register.csv`. Its principal hashes are:

- `model.safetensors`: `8a83c8a0e6ad25b73c089c9c6f8b01969f1c6bd7db76a71ff85de861a95311a0`
- `tokenizer.json`: `12bac982b793c44b03d52a250a9f0d0b666813da566b910c24a6da0695fd11e6`
- `chat_template.jinja`: `33204f1acb5bd0002713e16a593847f24ceeafe711ed88bda2a352dc996a3373`

## Capability Evidence

The technical report contains benchmark results across Danish, English,
mathematics and code. Results use task-specific shot counts, greedy decoding,
one output token for multiple-choice tasks, and up to 2,048 output tokens for
non-MCQ tasks. Scores are not guarantees for downstream domains.

## Limitations and Foreseeable Misuse

- not specifically safety aligned;
- may produce false, biased, offensive, insecure, or legally problematic text;
- may reproduce or closely resemble training content;
- limited performance outside Danish and English;
- limited assistant behavior relative to larger frontier models;
- tool calls can be syntactically or semantically invalid and must not be
  executed without validation and least-privilege controls;
- code can be insecure or nonfunctional;
- mathematical reasoning and final-answer formatting can fail;
- benchmark behavior is sensitive to prompt/template and serving semantics.

Downstream systems must add domain evaluation, human oversight where required,
input/output safeguards, logging, access controls, tool validation, and a legal
assessment appropriate to their intended use.

## Training Data

The final DFM8 recipe contains 161 source groups and approximately 70.48B
sampled tokens/epoch across public, agreement-supplied, synthetic/audited,
translated, and derived data. Exact historical DFM6/DFM7/DFM8 source/task
exposure is attached to the legal dossier. See the technical report and the
approved public training-content summary when available.

## Support, Security, and Corrections

| Contact | Value |
|---|---|
| Technical integration | [OPEN: LEG-031] |
| Security/vulnerability reports | [OPEN: LEG-032] |
| Rights/privacy requests | [OPEN: LEG-019] |
| Version/correction notices | [OPEN: LEG-033] |
