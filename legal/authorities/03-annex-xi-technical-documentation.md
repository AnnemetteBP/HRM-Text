# Annex XI Technical Documentation: DFM Mimir v1

**Status:** Draft  
**Classification:** Confidential; provide to competent authorities only through
the approved legal process  
**Model revision:** Hugging Face SHA `b121527524b6cfe0be14522cc9001ee6db036253`

## 1. General Description

| Annex XI field | Draft response / evidence |
|---|---|
| Intended tasks and integrations | General Danish and English text generation, instruction following, QA, dialogue, translation, summarisation, mathematical reasoning, source-code generation, and tool-call generation for non-commercial research. Intended integration classes require provider approval. [OPEN: LEG-021] |
| Acceptable-use policy | MIMIR License sections 5-8; a separate plain-language acceptable-use policy remains to be approved. [OPEN: LEG-022] |
| Release and distribution | Hugging Face gated repository created 2026-08-03; weights, configuration, tokenizer, chat template, model card and licence. Legal placement date unresolved. |
| Architecture and parameters | HRM-Text, approximately 1B parameters; hidden size 1,536; 32 configured layers with `half_layers=true` resulting in 16 layers per H/L stack; 12 heads; expansion 4; H cycles 2; L cycles 3; BP maximum 5; RoPE theta 10,000; pre-norm. |
| Modality and formats | Text input and text output. Gemma 4 chat template; 4,096-token context; vocabulary 262,144. Tool-call structure is represented in selected training data. |
| Licence | MIMIR License v1.0 - Research Model License. |

## 2. Development Process

### 2.1 Technical Integration Means

Native model architecture: `HrmTextForCausalLM`, `model_type=hrm_text`.
Production export uses packed vLLM-compatible attention and MLP projections.
The current tested serving environment and artifact hashes are frozen. The
historical release-time environment needs operator attestation or provider
approval of the current environment as the supported baseline. The model
requires correct PrefixLM semantics, Gemma 4 chat rendering, and
FlashAttention-compatible serving. See the downstream document. [HUMAN
REQUIRED: LEG-023]

### 2.2 Design and Training Specifications

| Item | Value |
|---|---|
| Objective | Causal language modelling over Gemma-native conversational/instruction sequences with HRM recurrence. |
| Optimizer | AdamW |
| Peak learning rate | `3e-4` |
| Warmup | 2,000 steps |
| LR minimum ratio | 1.0 (constant after warmup) |
| Betas | 0.9 / 0.95 |
| Weight decay | 0.1 |
| EMA | 0.9999; published model is EMA checkpoint [confirm release artifact]. |
| Global batch | 262,144 tokens |
| Gradient accumulation | 2 |
| Precision | bfloat16 forward/backward; fp32 FSDP parameter/gather precision as described in report. |
| Parallelism | FSDP on 8 NVIDIA B200 GPUs |
| Seed | 0 |
| Training steps | 1,650,000 |
| Training time | Less than 504.17 active accelerator hours from 1,650,000 steps at the reported average below 1.1 s/step. Checkpoint mtimes span at least 2026-06-20 (step 10,000) through 2026-07-21 (step 1,650,000), including interruptions and evaluation periods. Exact job-segment records require HPC/operator records. [HUMAN REQUIRED: LEG-024] |

The design rationale, assumptions, curriculum switches, BP-step schedule, and
optimization target need a signed architecture/training note. [OPEN: LEG-025]

### 2.3 Training, Testing, and Validation Data

The final DFM8 sampled recipe contains 161 source groups and 70,479,308,606
tokens/epoch. It is 68.62% English, 24.74% Danish, 6.54% bilingual Danish and
English, and 0.20% other. Forms include reformatted, curated/reformatted,
synthetic/audited, tool-call formatted, translated/audited,
agreement-supplied, and derived-task data.

The model was continued across DFM6, DFM7 and DFM8 recipes. Checkpoint sidecars
establish exact phase boundaries: DFM6 steps 0-720,083 (188,765,700,096 nominal
batch-token presentations), DFM7 steps 720,084-1,229,503 (133,541,396,480), and
DFM8 steps 1,229,504-1,649,999 (110,230,503,424). Sampled-index reconstruction
maps 1,350,991,478 consumed rows and 431,832,565,530 non-padding source tokens
to 31,868 phase/task exposure records. See `training-phase-register.csv` and
the `phase-*-exposure-register.csv` attachments. [RESOLVED ENGINEERING:
LEG-005]

Required attachments:

- complete source/version/legal-basis register;
- row and token counts before and after filtering;
- per-phase sampling indices and mixture configuration;
- source selection and allow/deny policy;
- synthetic generation/audit reports;
- PII, illegal-content, quality, deduplication and bias/source-unsuitability
  methods and results;
- training, validation and evaluation split controls and contamination checks;
- evaluation-dataset inventory and versions.

No dedicated validation corpus was used. The saved DFM8 XL configuration has
`data.validation_path: null`, `validation_interval: 0`, and
`validation_batches: 0`. Training health was monitored through training loss
and periodic benchmark evaluations; the published step-1,650,000 EMA checkpoint
was selected from periodic checkpoints rather than by held-out validation loss.
[RESOLVED ENGINEERING FACT: LEG-026]

### 2.4 Computational Resources

- 8 NVIDIA B200 GPUs with 180 GB HBM3e each.
- 1,650,000 optimizer steps at nominal 262,144 tokens/step.
- Engineering recurrence-aware upper bound: **`1.19e22` FLOPs**.
- The calculation counts multiply-add as two FLOPs, assumes five BP steps from
  the beginning, and upper-bounds attention with fully occupied 4,096-token
  blocks.

The arithmetic is reproduced in `legal/registers/compute-estimate.json`. This
is a conservative engineering estimate, not yet the approved regulatory
compute declaration. Independently review architecture coverage, embedding and
output head, recurrent virtual layers, backward multiplier, optimizer work,
partial contexts, actual BP schedule, and whether further-training phases or
failed/repeated steps are included. [OPEN: LEG-027]

### 2.5 Energy Consumption

No metered energy record has been located. The documented estimate in
[`05-energy-estimate.md`](05-energy-estimate.md) gives a GPU-only nameplate
upper bound of 4,033 kWh and a DGX-B200 whole-system analogue of 7,210 kWh.
Neither is actual consumption. Reconstruct, in descending evidence quality:

1. facility/job energy telemetry for the exact training allocations;
2. node/GPU power logs integrated over active time;
3. hardware power times measured utilization and wall time;
4. documented conservative estimate with assumptions, PUE treatment, and
   uncertainty interval.

Report accelerator energy separately from host/network/storage and facility
overhead. [OPEN: LEG-028]

## 3. Evaluation and Limitations

The technical report documents full-dataset evaluations across Danish,
English, mathematics and code benchmarks, greedy decoding, seed 4242, shot
counts, generation limits, and comparison models. The production release
evaluation comprises 39 registered task groups. Its plan, retained outputs,
configs, and current code inputs are SHA-256 frozen in
`evaluation-artifact-manifest.csv`; task-level result locations and completion
state are in `evaluation-register.csv`. An operator or release owner must
attest the exact July production code revisions because the current working
trees contain later changes. [HUMAN REQUIRED: LEG-029]

Known limitations include Danish/English language focus, weaker other-language
performance, limited assistant alignment, possible social biases, and no
specific safety alignment. Existing evidence and absent coverage are detailed
in `legal/controls/08-evaluation-and-safety-evidence.md`. An accountable human
owner must approve the threat model, thresholds, and release response before a
new safety campaign can be treated as complete. [HUMAN REQUIRED: LEG-030]

The Lex.dk exhaustive prefix probe found no exact 64-token extraction across
1,058,010 generations; maximum observed longest common prefix was 55 tokens in
a constrained mathematical formula. This is one source-specific memorisation
test, not a general privacy or copyright audit.

## 4. Systemic-Risk Section

Not applicable on present facts unless the Commission designates Mimir as a
GPAI model with systemic risk. Current compute is far below the `1e25`
presumption. Record and monitor reassessment triggers.
