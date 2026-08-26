# DFM9 Tulu 3 SFT Mixture Component Audit

Status: completed engineering/legal triage for the current academic,
non-commercial scientific-research project; not legal advice and not a blanket
commercial-use clearance.

## Scope and inventory

DFM9 samples `allenai/tulu-3-sft-mixture` with the policy in
`data_io/prefix_config_dfm9.yaml`. The local six Parquet shards contain
**939,343 rows and 19 distinct `source` labels**. The upstream card says
939,344 samples and enumerates 18 components. The local rows differ in two
auditable respects:

1. OpenAssistant contributes 7,131 local rows rather than the card's 7,132.
2. The rows contain 50,000 `tulu_v3.9_open_math_2_gsm8k_50k` examples that
   are not included in the card's prose component list.

The machine-readable row inventory and decision for every label is
`legal/registers/dfm9-tulu3-mixture-component-audit.csv`. The legal exposure
register attributes approximately **1.571B sampled tokens per epoch** to this
effective source. Component token allocation is not asserted because
multi-turn conversations expand into multiple training instances and the
sampler drops or truncates over-context examples; upstream row counts remain
exact.

## Rights result

The mixture-level ODC-By licence does not independently license every retained
prompt. After component decomposition:

- Fifteen source families already have direct/open, non-commercial, express
  training-permission, agreement, or previously audited generated-layer bases.
- CoCoNot is an Ai2-created contextual-noncompliance dataset released under
  ODC-By/Impact-LR terms. Its training responses are model generated. It is
  cleared under the publisher's stated terms and Responsible Use conditions.
- WildJailbreak is expressly described as a synthetic Ai2 safety-training
  dataset generated with GPT-4, GPT-3.5, Mixtral, and WildTeaming. It is
  released under ODC-By with Ai2 Responsible Use access conditions and is
  cleared under those terms.
- FLAN v2 Converted is an Ai2 conversion of an OpenOrca reproduction of FLAN.
  The 89,982-row release does not retain task-level licence metadata. The
  initial audit used Article 3 for uncovered upstream task expression.
- SciRIFF's task/schema layer is ODC-By. The retained 10,000-row subset spans
  approximately 39 scientific NLP task families and can reproduce portions of
  scientific papers. The initial audit used Article 3 for uncovered scholarly
  expression.

**Superseding project-owner decision, 2026-08-17:** FLAN v2 Converted and
SciRIFF now use Article 4 / Danish section 11 b for uncovered retained source
expression. Direct terms still control where captured. Article 3 is not relied
on for either component. This decision treats lawful access and absence of an
effective rights reservation as satisfied for the current project, while
retaining partial task/document provenance and incomplete acquisition-time
reservation evidence as caveats.

Therefore the effective Tulu 3 mixture is **cleared**, with direct component
terms plus Article 4 for uncovered FLAN v2 and SciRIFF expression. It no
longer relies on Article 3. Attribution, non-commercial restrictions,
Responsible Use conditions, third-party model-output terms, and the factual
conditions for Article 4 remain applicable.

## Primary evidence

- Tulu 3 mixture card: <https://huggingface.co/datasets/allenai/tulu-3-sft-mixture>
- CoCoNot card: <https://huggingface.co/datasets/allenai/coconot>
- WildJailbreak card: <https://huggingface.co/datasets/allenai/wildjailbreak>
- SciRIFF card: <https://huggingface.co/datasets/allenai/SciRIFF>
- FLAN v2 Converted card: <https://huggingface.co/datasets/ai2-adapt-dev/flan_v2_converted>
- Existing persona-family audit:
  `legal/reports/dfm9-tulu3-persona-family-audit.md`
