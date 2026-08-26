# DFM9 Apertus SFT Component Audit

Status: evidence-based engineering/legal triage, not legal advice or a
commercial-use clearance. Audit date: 2026-08-17.

## Scope and result

DFM9 receives approximately 3.034B tokens per epoch from the Apertus component
inside `danish-foundation-models/dfm-dyna-instruct`. The DFM copy repackages
`swiss-ai/apertus-sft-mixture`; the upstream mixture has an ODC-By database
layer and, in the locally reconstructed dependency DAG, draws from Tulu 3,
SmolTalk2, and EuroBlocks.

The component is **cleared for the current academic/non-commercial
scientific-research training purpose, with partial provenance completeness**.
The former five aggregate boundaries have now been decomposed. SmolTalk itself
needs Article 3 only through its LongAlign imports. OpenHermes uses direct
component terms plus the project-owner Article 4 decision for four uncovered
families. Mixture-of-Thoughts uses direct/per-sample terms plus the recorded
residual-risk acceptance without Article 3. LongAlign has eleven reviewable
content groups. EuroBlocks separates 5,169 rows with full seed documents from
134,819 seed-derived rows.

Superseding review status, 2026-08-18: project-owner decisions MAN-017 and
MAN-018 approve the LongAlign and EuroBlocks Article 3 boundaries for the
current academic/non-commercial scientific-research purpose. Their provenance
remains partial, and raw redistribution/nonresearch use remains uncleared.

This is not a blanket finding that Apertus or every component is open licensed
or suitable for general commercial reuse. Article 3 reliance requires lawful
access, a scientific-research purpose, appropriate security, and purpose-bound
retention. Source notices and model acceptable-use terms remain applicable.

## Component decisions

| Source boundary | Result for current use | Basis and remaining qualification |
|---|---|---|
| `declare-lab/HarmfulQA` | Direct, complete | Apache-2.0 ChatGPT-distilled safety release. EuroBlocks' multilingual refusal layer additionally follows Llama terms. |
| EuroBlocks Llama-generated families | Cleared, partial | EuroBlocks identifies Llama 3.1 terms. Article 3 applies only to uncovered retained annealing-seed expression. |
| `Magpie-Llama-3.1-Pro-300K-Filtered` | Direct, complete | From-scratch Magpie prompts/responses under Meta Llama 3.1 Community License. |
| `Magpie-Llama-3.1-Pro-DPO-100K-v0.1` | Direct, complete | Magpie-generated prompt/preference records under Meta Llama 3.1 terms. |
| `Magpie-Reasoning-V1-150K` | Direct for current scope, complete | Synthetic Qwen prompts and Llama responses under the stated Llama, Qwen, and CC-BY-NC-4.0 terms. |
| `NousResearch/hermes-function-calling-v1` | Direct, complete | Apache-2.0 synthetic tool-use release. |
| `nvidia/Nemotron-SFT-OpenCode-v1` | Direct, complete | CC-BY-4.0; NVIDIA describes synthetic questions/skills and trajectories and expressly permits commercial/non-commercial use. |
| `nvidia/Nemotron-SFT-SWE-v2` | Direct, partial | CC-BY-4.0 and expressly intended for SFT; retained repository/code material follows listed Apache/MIT/BSD notices, whose source-level mapping remains partial. |
| `nvidia/OpenCodeInstruct` | Direct, complete | CC-BY-4.0 synthetic code instructions; NVIDIA expressly permits model training. |
| `open-r1/s1K-1.1` | Direct, complete | Formatting derivative of the MIT-licensed `simplescaling/s1K-1.1`. |
| `HuggingFaceTB/smoltalk` | Cleared, decomposed | Eleven subsets have direct/current-scope terms; MetaMath/NuminaMath retain source notices; OpenHermes imports now use the recorded Article 4 decision and only LongAlign descendants use Article 3. See `dfm9-smoltalk-component-audit.md`. |
| `open-r1/Mixture-of-Thoughts` | Cleared, decomposed | 93,733 math, about 83,100 code, and 172,514 science rows are separated. Residual risk was accepted without Article 3 reliance; complete competition editorials remain the highest raw-data and memorisation-test risk. See `dfm9-mot-copyright-risk.md`. |
| `teknium/OpenHermes-2.5` | Cleared, decomposed | All 1,001,551 rows map to 19 blocks. Direct/current-scope terms cover most; Article 4 was selected for four narrow residual families. See `dfm9-openhermes-component-audit.md`. |
| `THUDM/LongAlign-10k` (now `zai-org`) | Cleared, grouped partial | 90.5% of rows were assigned to ten content groups and 939 remain mixed; Article 3 remains the current-use basis pending document-level provenance. See `dfm9-longalign-euroblocks-boundary-audit.md`. |

## Relation to FLAN v2 and SciRIFF

The Tulu 3 branch inside Apertus was separately audited. The initial audit
used Article 3 only for uncovered FLAN v2 and SciRIFF source expression. A
superseding project-owner decision on 2026-08-17 assigns Article 4 / Danish
section 11 b to those uncovered layers; direct terms continue to control where
captured. Tulu 3 no longer relies on Article 3. Task/document provenance and
acquisition-time reservation evidence remain partial.

## Evidence reviewed

- Official Hugging Face cards for Apertus SFT, SmolTalk/SmolTalk2,
  EuroBlocks, HarmfulQA, Magpie, Hermes Function Calling, NVIDIA OpenCode/SWE,
  Open R1, OpenHermes, and LongAlign.
- `legal/reports/dfm9-tulu3-mixture-audit.md`.
- The declarative source graph in `legal/specs/dfm9-source-dag/`.

## Remaining work

1. Reconstruct document-level URLs, authors, terms, and acquisition evidence
   for LongAlign, starting with books/publisher rows and 939 unclassified rows.
2. Recover CoT Alpaca and Caseus source evidence if possible.
3. Preserve and audit per-sample NVIDIA science licences and compare MoT
   editorial-conditioned generations against source editorials.
4. Identify the EuroLLM annealing seed corpus/revision and source-level terms.
5. Reassess every Article 3-dependent layer before commercial training,
   source-record redistribution, or a materially different research purpose.
