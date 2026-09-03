---
type: Plan
title: Mixture-of-Experts HRM Experiment Plan
description: A recurrence-aware, compute-controlled path from the current dense HRM to sparse feedforward experts and later attention, embedding, normalization, and parallelism experiments.
tags: [architecture, hrm, moe, attention, embeddings, normalization, distributed]
status: draft
last_updated: 2026-09-03
confidence: medium
part_of: /pages/model-architecture.md
sources:
  - id: moeut
    resource: https://arxiv.org/abs/2405.16039
    title: "MoEUT: Mixture-of-Experts Universal Transformers"
  - id: olmoe
    resource: https://arxiv.org/abs/2409.02060
    title: "OLMoE: Open Mixture-of-Experts Language Models"
  - id: megablocks
    resource: https://arxiv.org/abs/2211.15841
    title: "MegaBlocks: Efficient Sparse Training with Mixture-of-Experts"
  - id: deepseek-moe
    resource: https://arxiv.org/abs/2401.06066
    title: "DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models"
  - id: gqa
    resource: https://arxiv.org/abs/2305.13245
    title: "GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints"
  - id: moba
    resource: https://arxiv.org/abs/2502.13189
    title: "MoBA: Mixture of Block Attention for Long-Context LLMs"
  - id: nsa
    resource: https://arxiv.org/abs/2502.11089
    title: "Native Sparse Attention: Hardware-Aligned and Natively Trainable Sparse Attention"
  - id: mla
    resource: https://arxiv.org/abs/2405.04434
    title: "DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model"
  - id: olmo2
    resource: https://arxiv.org/abs/2501.00656
    title: "2 OLMo 2 Furious"
  - id: tying
    resource: https://arxiv.org/abs/1608.05859
    title: "Using the Output Embedding to Improve Language Models"
  - id: adaptive-inputs
    resource: https://arxiv.org/abs/1809.10853
    title: "Adaptive Input Representations for Neural Language Modeling"
  - id: mixture-recursions
    resource: https://arxiv.org/abs/2507.10524
    title: "Mixture-of-Recursions: Learning Dynamic Recursive Depths for Adaptive Token-Level Computation"
  - id: palm
    resource: https://arxiv.org/abs/2204.02311
    title: "PaLM: Scaling Language Modeling with Pathways"
  - id: huginn
    resource: https://arxiv.org/abs/2502.05171
    title: "Scaling up Test-Time Compute with Latent Reasoning: A Recurrent Depth Approach"
  - id: mixture-depths
    resource: https://arxiv.org/abs/2404.02258
    title: "Mixture-of-Depths: Dynamically Allocating Compute in Transformer-Based Language Models"
  - id: multi-token
    resource: https://arxiv.org/abs/2404.19737
    title: "Better & Faster Large Language Models via Multi-token Prediction"
  - id: retrieval-attention
    resource: https://arxiv.org/abs/2409.10516
    title: "RetrievalAttention: Accelerating Long-Context LLM Inference via Vector Retrieval"
  - id: demix
    resource: https://arxiv.org/abs/2108.05036
    title: "DEMix Layers: Disentangling Domains for Modular Language Modeling"
  - id: local-ablation-results
    resource: ../../../private/ablation_results.tex
    title: "Planned HRM Ablations and Completed Schedule Results"
  - id: local-mech-interp-results
    resource: ../../../private/UPLOAD_RESULTS_TO_OVERLEAF/results.tex
    title: "Results for Recurrent Computation in Hierarchical Language Models"
  - id: local-big-dc
    resource: ../../../private/The big-DC MoE LLM design.pdf
    title: "The big-DC MoE LLM design"
---
# Mixture-of-Experts HRM Experiment Plan

## Evidence-integrated revision (2026-09-02)

The completed local ablations and exploratory mechanistic results supersede
the initial seam-only recommendation to route every fourth H feedforward. That
older placement is retained below as historical context.

The 17-run XXS schedule sweep uses one run per configuration, BP5, identical
reported parameters and token budget, and finds that L-heavy schedules have
lower validation loss at every matched recurrent depth. At D=8, H1/L7 reaches
`1.69501`, H2/L3 `1.71218`, and H4/L1 `1.84127`. At D=10, H1/L9 reaches
`1.69205`, H2/L4 `1.70130`, and H5/L1 `2.03663`.[^local-ablation-results]
This is consistent descriptive evidence for useful repeated L computation,
but it has no seed-level uncertainty, uses a truncated gradient horizon, and
couples the H/L allocation. It does not justify changing the MoE baseline away
from H2/L3.

The separate downstream table favors the native H2/L3 schedule as the safest
reference. H1/L3 broadly degenerates, while H3/L3 retains substantial
multiple-choice scores but nearly collapses on GSM8K and GEC-DaLA. The table's
checkpoint/training provenance, evaluator invalid rates, and macro-versus-micro
MMLU labels must be resolved before using it as a trained-schedule ranking.
Until then, do not select schedules by teacher-forced validation or
multiple-choice accuracy alone.[^local-ablation-results]

The mechanistic evidence nominates a more specific MoE site. Attention-write
sensitivity is concentrated near stack entry, whereas MLP-write sensitivity is
concentrated at the last physical block, especially the final L execution for
HRM-Text and final H execution for DFM-Mimir. Late HRM-Text L MLP writes add
positive target-logit evidence, and persistent L or joint-state patches have
larger effects than persistent H-only patches. Conversely, freezing H causes
the larger immediate correct-log-probability loss, and one-time H patches are
high impact.[^local-mech-interp-results]

The revised default is therefore:

```yaml
H_cycles: 2
L_cycles: 3
moe_level: L
moe_layer_selection: [last]
num_experts: 4
top_k: 1
expert_intermediate_size: dense_intermediate_size
dispatch: reference_dropless
router_dtype: float32
```

`last` means relative stack exit: index 2 at XXS after `half_layers`, index 3
at S, and index 15 for the 16-layer XL stacks. H remains dense in the primary
row. A matched `H[last]` row is obligatory counterevidence, followed by
`L[last]+H[last]` if either single-level row is credible. Because the site maps
are exploratory and not multiplicity-corrected, the winning level must also be
compared with a parameter-matched stack-entry placement.

The router remains cycle-agnostic initially: the hidden state itself is the
phase signal. Telemetry is cycle-resolved. Add explicit recurrent-step
conditioning only if routes fail to distinguish useful phases or become
unstable; this prevents a phase embedding from becoming an unmeasured
confound.

## Big-DC proposal audit and HRM boundary (2026-09-02)

The eight-page big-DC document is not an implementable or empirically
validated model specification. It is a 19-point co-design agenda spanning a
model, custom interconnect, asynchronous serving, storage, retrieval, and
data-centre placement. The author explicitly states that the combined system
has not been built. It supplies no hidden width, expert count, top-k, capacity
policy, router loss, normalization, activation, embedding, positional scheme,
optimizer, data mixture, or evaluation result.[^local-big-dc]

Consequently, any current toy should be called a **big-DC-inspired model-core
instantiation**, with a versioned decision ledger, rather than an exact
reproduction. For each of the 19 points, the ledger must say `implemented`,
`simulated`, `deferred`, or `not applicable`, and record every choice that the
document leaves open. No matching toy implementation is present in this
checkout as of this audit. The closest existing comparator is the Universal
Transformer baseline, which repeats an entire dense Transformer stack for four
fixed cycles; it does not have an expert-rich single middle layer, adaptive
depth, the proposed cache policy, parallel attention/feedforward, or the two
latent streams.

| Proposal component | Relation to current HRM | Experimental treatment |
|---|---|---|
| A few entry/exit layers around one middle layer repeated roughly 128 times, with almost all experts in that middle layer | Shares depth recurrence, but replaces HRM's two states, two separately parameterized stacks, and nested `L...L -> H` schedule | Treat as a one-state recurrent-MoE comparator. Wholesale replacement is no longer HRM. |
| Parallel attention and feedforward branches | Current blocks are serial attention then SwiGLU; the feedforward therefore sees the attention update | Test first as a dense block ablation, then cross it with only the winning MoE core. It is a function change, not a latency-only refactor. |
| Token-adaptive middle-layer iterations | HRM uses fixed H2/L3 calls; truncated BP changes gradients, not forward depth | Begin with fixed depth and full-BPTT tiny controls. Later use fixed-maximum masked halting; rank-local variable loops are unsafe with current collectives. |
| Local access to prior recurrent caches and global access only to final recurrent states | Every current H/L call has a distinct full cache | Test fixed L-local/H-global and the reverse-role control before dynamic final-state caches. The PDF itself identifies causal serialization problems. |
| Two per-token latent streams with shared weights, only one attention-visible and the other prediction-specific | These are not HRM's H and L states: both HRM states participate in attention and use different weights | If tested, add the prediction lane around final H as a separate objective; do not rename the existing hierarchy. |
| Train-native multi-token/speculative prediction | Absent from the current objective | Test a multi-token head independently after the core comparison; serving speed also requires a measured verifier/acceptance path. |
| Indexed long-range attention and per-iteration knowledge retrieval | Absent; materially changes cache, kernels, data, and serving | Long-context research track only, after static local/block sparsity and retrieval-quality oracles. |
| 50% structured weight sparsity, FP4, 64-device expert tensor parallelism, Clos/multicast, pooled asynchronous serving, and tiny-HBM nodes | Mostly orthogonal hardware/runtime hypotheses; current FSDP is not expert parallelism | Do not include in the model-quality toy. Benchmark or simulate each only on hardware where the claimed sparsity and traffic reductions are realizable. |
| Embedding, normalization, and activation | The document makes no choice | It provides no evidence against the current scaled token embedding, RMSNorm, or SwiGLU. Keep them fixed in the comparator and use the independent lanes below. |

The safest hybrid preserves `z_H`, `z_L`, and the nested schedule while placing
sparse feedforward experts at evidence-nominated H/L sites. A separately
shared middle block inside each of the H and L stacks is still recognizably
hierarchical. Collapsing both into one recurrent state or reinterpreting H/L as
the context/prediction streams is not.

Published evidence supports individual hypotheses, not the whole bundle.
PaLM reported about a 15% training-speed improvement from a parallel
attention/feedforward formulation, with a small quality cost in its 8B
ablation and no detected loss at 62B; that is a throughput prior, not evidence
of toy-scale or HRM quality superiority.[^palm] MoEUT is the closest direct
recurrent-MoE precedent, but its strongest result used two alternating shared
layer groups rather than one fully shared layer, downstream gains were much
smaller than perplexity gains, and its reported implementation remained slower
than its dense FlashAttention comparator.[^moeut] Huginn supports fixed
recurrent-depth test-time scaling but also shows sensitivity to initialization,
normalization, and repeated input injection.[^huginn] No cited primary result
establishes the 19-point big-DC combination as jointly optimal.

### Fair comparison geometry

The apparent `128` coincidence must not obscure a parameter mismatch. XL HRM
has 16 distinct H blocks and 16 distinct L blocks, called 32 and 96 times
respectively: 32 physical parameter sets produce 128 block applications. The
existing Universal Transformer also produces 128 applications as a 32-block
group repeated four times. The document's example instead uses one middle
layer about 128 times and proposes about 128 times as many experts as a normal
layer.[^local-big-dc]

A 128-expert middle feedforward is therefore comparable in feedforward
capacity to a conventional 128-untied-layer model, not to HRM's 32 physical
feedforwards. Before allocating entry and exit layers, a parameter-matched XL
HRM comparator would have roughly 32 expert-equivalent feedforwards; the
literal virtual-depth-capacity row would have roughly 128 and about four times
as many feedforward parameter sets. At XXS the analogous counts are 6 physical
blocks, 24 applications, and either roughly 6 or 24 expert-equivalent sets.
XXS vocabulary matrices dominate the total parameter count, so report
non-vocabulary-core parameters separately and move architectural conclusions
to at least B scale.

Run two explicit budget regimes instead of calling one fair by default:

1. **HRM-budget:** matched active block applications/FLOPs, non-vocabulary
   parameters, training tokens, and BP horizon.
2. **Virtual-depth-capacity:** the larger expert bank proposed by the document,
   compared against a correspondingly parameter-rich untied or wider baseline.

The claim that one tied middle layer can perfectly simulate arbitrary untied
depth also needs a testable mechanism. Step-conditioned routing can select
different feedforward experts, but shared attention and normalization still do
not reproduce arbitrary layer-specific attention/norm parameters. Report a
step-blind router and an explicit step-conditioned control, and verify that
every expert receives task gradients under truncated BP. An expert used only
in detached early iterations otherwise cannot learn the claimed virtual layer.

### Core identity experiment

Use fixed recurrence, serial attention/feedforward, current RMSNorm/SwiGLU,
and the current embedding first. The minimum informative comparison is:

| Row | State/weight topology | Feedforward | Question |
|---|---|---|---|
| H-Dense | Current two-state H2/L3 HRM | Dense | Reproducible reference |
| U-Dense | Existing one-state group-recurrent Universal Transformer | Dense | Does the H/L hierarchy help at matched block applications? |
| R1-Dense | One-state, single-middle-block recurrence with declared entry/exit layers | Dense | What is the cost of extreme depth sharing before experts compensate for it? |
| R1-MoE-P | Same R1 graph, HRM-budget expert bank | Sparse | Does conditional feedforward capacity recover the shared-middle model fairly? |
| R1-MoE-V | Same R1 graph, virtual-depth-capacity expert bank | Sparse | Does the larger PDF-style capacity buy a better quality/compute point? |
| H-MoE | H2/L3 with the reference final-L MoE and required final-H control | Sparse | Does MoE help while preserving the tested hierarchy? |

Only after these rows resolve state topology and conditional capacity should
the best H and R1 variants be crossed with parallel attention/feedforward.
Dynamic depth, hybrid caches, multi-token prediction, structured sparsity,
indexed attention, and retrieval are later, independently gated experiments.

## Domain coverage and expert-specialization guardrail

The completed schedule and mechanistic studies provide priors about the tested
checkpoints and tasks; they do not establish the best architecture across
specialized domains, and they do not establish that a routed expert should be
a human-readable domain expert. Experts may instead specialize by token
identity, language, syntax, sequence position, H/L level, physical layer, or
recurrent phase. The first E4/top-1 model is an integration test, not an
adequate test of broad domain specialization.

Separate two questions that ordinary aggregate benchmarks conflate:

1. **Quality:** does a row improve held-out likelihood, generation validity,
   task scores, and worst-domain performance at its declared budget?
2. **Specialization:** are route differences stable, generalize to unseen
   sources within a domain, and causally necessary for the domain-specific
   gain?

Use a router-blind, source-labeled probe corpus with equal valid-token budgets
for at least Danish general text, English general text, multilingual text,
code, mathematics/formal reasoning, science/technical text, legal/government
text, and dialogue/instruction data. Add long-context retrieval and
summarization as a length axis rather than allowing length to masquerade as a
domain. Keep a natural-mixture view as a second report; equalized probes reveal
specialization, whereas natural weights estimate deployment quality.

For each domain and each `(level, physical layer, recurrent call)`, report
held-out NLL plus bits per byte or character, router entropy, expert fractions,
load CV, dead experts, route persistence/churn, conditional mutual information
or a held-out domain-from-route classifier, and pairwise route-distribution
divergence. Control or stratify by token identity/frequency, tokenizer
fertility, position, context length, source collection, and supervised versus
prefix tokens.

Routing correlation is not sufficient. Build the domain-by-expert causal loss
matrix by zeroing an expert, forcing a matched-load alternative, and swapping
routes within and across domains. A credible specialist produces a selective
loss or task-quality deficit that repeats across seeds and held-out sources;
high domain predictability without a selective intervention effect is merely
a routing signature. Include mixture-shift and leave-one-source-out probes to
distinguish general specialization from source memorization.

The existing standard and Danish/English evaluation suites remain useful for
quality, but their aggregate scores cannot substitute for this token-aligned
router study. Architecture decisions should use a Pareto report containing
mean and worst-domain quality, total and active parameters, active FLOPs,
tokens/s, memory/KV use, router balance, route churn, and uncertainty across
seeds.

The currently completed architecture table is narrower still: its downstream
columns are ARC-C, MMLU, GSM8K, HellaSwag, and GEC-DaLA, and it demonstrates
that acceptable multiple-choice scores can coexist with failed open
generation.[^local-ablation-results] The tracked `dfm9_mini` configuration
reports its aggregate size but not a domain allocation, and the referenced
data-IO submodule is not initialized in this checkout. Do not infer the mini
mixture from the much larger full-DFM9 source inventory.

Training batches currently expose token, label, position, and sequence
structure but no source/task/domain identity. Phase-one domain analysis must
therefore use eval-time controlled labels. Adding provenance to future batches
is a separate implementation, privacy, and storage decision; until then,
clusters discovered on unlabeled training samples are not named domain
experts.

A low-cost first routing panel is about 384 controlled prompts:

- 192 prompts from 6 content domains x 16 matched semantic items x Danish and
  English, using one short-answer template and matched length bins;
- 64 same-content prompts varying operation or format only;
- 64 same-content prompts spread across four context-length bins;
- 64 paraphrase and translation controls.

Candidate domains are general factual, humanities/history, mathematics,
natural/biomedical science, law/government, and computing. The existing
matched 26-language MKQA cohort can follow as a language-only panel. Bootstrap
by semantic item and compare conditioned mutual information and route
similarity to shuffled-factor nulls. A specialization claim requires the
factor signal to survive language/format/length controls, repeat across seeds
and checkpoints, and produce a selective causal loss under expert ablation or
rerouting.

For adaptive depth, Mixture-of-Depths is the clean first published comparator:
it keeps a fixed token capacity per sparse block, required interleaved full
blocks, and needs a causal router predictor for autoregressive inference.[^mixture-depths]
Multi-token prediction should remain an independent head/loss axis; published
natural-language effects are mixed and four-token prediction is not uniformly
better, so begin with two.[^multi-token] RetrievalAttention is useful as an
indexed-KV inference comparator, not evidence for the PDF's full trainable
indexed-attention architecture.[^retrieval-attention] If the scientific target
is explicitly human-defined domain experts rather than emergent routing,
include a separately labelled DEMix-style oracle/control rather than judging a
latent router against an unstated semantic expectation.[^demix]

## Decision summary

The first implementation should change only selected feedforward blocks in the
existing two-level HRM. It should not combine MoE, sparse attention, a new
normalization scheme, a new tokenizer, and a new activation in one run. The
recommended ladder is:

1. Freeze a versioned big-DC toy decision ledger and audit the actual toy path;
   do not call it exact while the PDF's missing choices remain implicit.
2. Add routing instrumentation to unchanged dense HRM and Universal
   Transformer baselines.
3. Build a deterministic, dropless reference MoE in the final physical L
   feedforward while preserving the H2/L3 schedule.
4. Reuse the validated MoE primitive in the one-state R1 comparator under both
   HRM-budget and virtual-depth-capacity regimes.
5. Establish a grouped-GEMM implementation and run matched final-H,
   final-H-plus-L, and stack-entry placement controls.
6. Run the controlled routing panel and causal expert interventions alongside
   the ordinary quality suite.
7. Test weight tying and the BPTT schedule independently, then use any saved
   vocabulary parameters to fund conditional experts in a budget-matched run.
8. Test normalization, H/L fusion, and parallel attention/feedforward one at a
   time before crossing winners.
9. Add GQA, then native local-window attention, then static block sparsity;
   learned MoBA/NSA-style routing comes only after the mask and serving
   semantics are validated.

The architectural north star is a recurrent group of several distinct
physical layers, with selected fine-grained feedforward experts and explicit
recurrence-call telemetry. This is closer to MoEUT's successful shared-depth
design than a single repeated expert layer, while preserving HRM's separate H
and L state paths.[^moeut]

## Additive reference implementation status (2026-09-02)

The correctness-first HRM MoE path is implemented entirely in new files; the
existing dense Transformer, HRM, LM head, training loop, and configurations
remain unchanged:

- `models/moe.py` contains a serial Transformer stack with MoE only at explicit
  physical-layer indices, an eager dropless token-choice dispatcher, FP32
  router logits/probabilities/losses, selected-probability or renormalized
  top-k weighting, and functional auxiliary outputs.
- `models/baselines/hrm_moe_nocarry_bp_warmup.py` preserves the two-state
  H2/L3 schedule and truncated-BP allocation. It aggregates routing without
  mutable module state and exposes a static label for every
  `(level, recurrent call, physical layer)` router invocation.
- `models/moe_lm_head.py` combines token CE with call-averaged balance and
  router-z losses. It logs pooled and call-resolved expert loads and mean route
  probabilities, plus whether each call was inside the active gradient
  horizon.
- `config/arch/net/hrm_moe.yaml` selects only the final physical L
  feedforward, E=4/top-1, selected-probability weighting, balance coefficient
  `0.01`, and z-loss coefficient `0.001`. H remains dense.
- `tests/test_hrm_moe.py` covers E=1 dense-SwiGLU forward/gradient parity,
  padding exclusion, top-1 task gradients to the router, H2/L3 call counts,
  per-call traces, auxiliary objective plumbing, negative layer indices,
  BP-warmup endpoints, compiler entry, activation-checkpoint discovery/replay,
  and end-to-end packed backward.

The eager dispatcher is deliberately marked compiler-disabled. A compiled
caller works, but this implementation loops over experts and is not throughput
evidence. Because `MoETransformerBlock` subclasses the existing
`TransformerBlock`, the current activation-checkpoint and FSDP discovery paths
find it without changes; current block-level FSDP will nevertheless materialize
the whole expert bank and is not expert parallelism. Grouped GEMM and then a
true expert-parallel mesh remain required before B/XL efficiency claims.

`selected_probability` gives a language-model gradient to a top-1 router but
scales the selected branch by its full-softmax probability. `renormalized`
preserves unit selected-route scale but top-1 then receives no task gradient
through the discrete choice. Both are exposed because this is an architectural
ablation, not a hidden implementation detail; the default is the former and
must be compared with branch RMS telemetry.

## Verified baseline boundary

The production HRM2 configuration has 16 physical H blocks and 16 physical L
blocks at XL after `half_layers` splits the configured 32 layers. Each forward
applies the L stack six times and the H stack twice. The same physical
parameters are therefore reused across recurrence calls, but each attention
application has a distinct KV cache.

Every block currently contains gated multi-head attention followed by a dense
SwiGLU. Both sublayers use parameterless RMSNorm in the pre-norm path, and each
H/L stack call ends with another parameterless RMSNorm. The only H/L fusion is
raw addition before a stack call. There is no segment, level, or recurrent-step
embedding.

At XL, `d=1536`, the dense SwiGLU width is `I=4096`, and a physical dense
feedforward contains:

```text
3 * d * I = 18,874,368 parameters
```

The complete model has `1,786,773,504` parameters. The 262,144-by-1,536 input
embedding and untied output classifier each contain `402,653,184` parameters;
together they are `805,306,368`, or 45.07% of the model. The non-vocabulary
core is `981,467,136` parameters.

Two gradient-horizon facts affect every architecture comparison:

- At the initial `bp_steps=2`, only the last H and L applications are marked
  differentiable. The original input path has already crossed a no-grad H
  call, so the input embedding receives no gradient. It starts receiving
  input-path gradients at `bp_steps>=3`. With the default warmup, BP remains
  at two for roughly the first 6.67% of updates.
- `zL_init` is a fixed random buffer broadcast across tokens. Simply changing
  it to a parameter would not make it learnable under the current maximum
  truncated-backpropagation horizon because its only use is before the
  differentiable L calls.

Weight tying would update the shared table immediately through the output
loss. A tied-versus-untied result is therefore both a parameter-sharing and an
early credit-assignment result unless it is crossed with the BP schedule.

## Why MoE is unusually relevant to HRM

Depth recurrence increases computation while reusing parameters. Sparse
experts can restore conditional parameter capacity without multiplying the
active feedforward matrix multiplications on every token. MoEUT provides the
closest direct precedent: it combines feedforward and attention experts with
small groups of distinct layers that are recurrently reused, and introduces a
normalization scheme specifically for shared-depth signal propagation.[^moeut]

HRM also creates a new failure mode. A router in one physical layer sees the
same token at several computation stages. A globally healthy load histogram
can hide collapse by recurrence call, and a token can touch many different
expert weights over eight applications. Route persistence and route churn are
therefore both quality and inference-bandwidth measurements, not optional
visualizations.

The labels H and L must not be treated as proof that one is globally semantic
and the other locally syntactic. Their current attention and block structures
are identical. The revised late-L starting point is evidence-nominated, not a
proven optimum; final-H and stack-entry controls are required before drawing an
architectural conclusion.

The operational joint-training contract, its boundary from FlexOlmo, balance
scope, domain specialization, and `(E, k, expert width)` experiment geometry
are maintained in [MoE Training and Routing](moe-training-and-routing.md).

## Reference implementation contract

### Placement and routing

Create a separate HRM2 MoE configuration. The evidence-integrated reference
uses:

```yaml
level: L
layer_selection: [last]
num_experts: 4
top_k: 1
expert_intermediate_size: dense_intermediate_size
dispatch: reference_dropless
router_dtype: float32
```

At XL this converts physical L layer 15. Because L runs six times, there are
six routed feedforward executions per model forward. Attention, token
embeddings, normalization, activation, H2/L3 recurrence, and optimizer remain
unchanged.

### Superseded seam-only placement

Before the local result files were supplied, the initial proposal selected H
layers `3, 7, 11, 15` at XL because `H_override` was the smallest existing
configuration seam and H executes less often. That is no longer the default.
It remains a possible later uniform-placement control after final-L versus
final-H is resolved.

The E=4/top-1 reference is an integration gate, not the final quality design.
Top-1 output weighting must be explicit: renormalizing the selected route to
one preserves branch scale but gives the router no language-model gradient
through its discrete choice; multiplying by its full softmax or sigmoid score
does train the gate but changes the branch scale at initialization. The tests
must cover the chosen rule. Do not hide it inside dispatch code.

After correctness, the first scientific sparse run should compare this with
E=8/top-2 experts of half the dense intermediate width. This keeps active
expert matrix multiplications approximately matched to the dense SwiGLU while
giving the router a meaningful continuous mixture. A later fine-grained row
can use more, narrower experts; OLMoE and DeepSeekMoE support testing fine
granularity, but their conclusions do not remove the need for an HRM-specific
ablation.[^olmoe][^deepseek-moe]


### Parameter and active-compute accounting

For hidden width `d`, dense intermediate width `I`, `E` experts, expert width
`I_e`, and `k` selected experts:

```text
dense SwiGLU parameters       = 3 d I
dense matmul FLOPs/token      ~= 6 d I
MoE parameters                = 3 E d I_e + E d
MoE active matmul FLOPs/token ~= 6 k d I_e + 2 E d
```

Using `I_e=I/k` approximately matches active feedforward matrix
multiplications. It does not make wall time equal: top-k, sorting, dispatch,
communication, imbalance, and smaller GEMMs remain overheads.

For XL E=4/top-1, each converted layer grows from `18,874,368` parameters to
`75,503,616`, an increment of `56,629,248`. The revised one-exit model contains
`1,843,402,752` parameters. Converting both L and H exits adds `113,258,496`
parameters. The older four-H-layer proposal added `226,516,992` and produced a
`2,013,290,496`-parameter model.

At XXS, one E4/top-1 exit adds `1,770,496` parameters to the
`139,722,752`-parameter baseline, producing `141,493,248`; both exits produce
`143,263,744`. However, the input and output vocabulary matrices account for
about 96.06% of the XXS baseline. XXS is suitable for correctness and schedule
discovery, not for extrapolating the parameter efficiency of a core MoE.

### Functional loss plumbing

The current block, Transformer, recurrent model, and LM head return no MoE
auxiliary loss. Add a pure functional output path that carries router losses
through all four levels. Do not store per-forward loss tensors or counters in
mutable module attributes: `torch.compile`, activation-checkpoint replay, and
multiple recurrent invocations can duplicate or stale such state.

Use a loss of the form:

```text
L = L_CE + lambda_balance * mean_valid_router_calls(L_balance)
         + lambda_z       * mean_valid_router_calls(L_z)
```

`0.01` balance and `0.001` z-loss are reasonable starting values from OLMoE,
not inherited truths.[^olmoe] Average by the number of participating router
invocations so changing recurrence depth or MoE placement does not silently
change the effective coefficient. Compute router logits, probabilities, and
auxiliary reductions in FP32.

Packed training tensors contain a padded tail. Routing, capacity, load loss,
and telemetry must use only `x[:total_seqlen]`; cached inference routes all
valid `[B,S]` positions. Per-sequence balancing is a later ablation because
MoEUT found it important for its shared-depth setup, but very short packed
segments can make uniform per-sequence loads impossible.[^moeut]

### Dropless dispatch and determinism

Dropping or zeroing overflow tokens is especially risky when the effect can
compound across recurrent calls. The reference path should be dropless. A
production path should use grouped GEMM or a block-sparse implementation such
as the class of kernels introduced by MegaBlocks, not a Python expert loop or
an all-experts dense computation presented as a speed result.[^megablocks]

Routing must replay deterministically under non-reentrant activation
checkpointing. If router jitter is later added, its random-state behavior must
be part of the checkpoint parity test.

## Recurrence-specific telemetry

Record metrics by level, physical layer, recurrent call, and whether that call
is inside the current gradient horizon. Pooled metrics alone are insufficient.
At minimum log:

- expert token fraction, entropy, maximum/minimum load, and coefficient of
  variation;
- balance loss, router z-loss, overflow/drop/fallback rate, and dead experts;
- selected-route probability and router/expert gradient and update norms;
- route Jaccard/persistence for the same token across H or L calls;
- route entropy, transitions, and specialization split by prefix/suffix,
  task, language, semantic condition, and correct/incorrect outcome;
- residual RMS, branch-update RMS, and update-to-residual ratio after every
  six L and two H stack applications;
- input-embedding gradient onset and frequent-versus-rare token row norms;
- raw and EMA validation loss separately during short runs.

Add expert-output zeroing, route-swap, or matched-donor interventions for the
winning placement. Load balance and correlation with a task or ITDA feature do
not establish that an expert is causally used.

The current EMA decay of 0.9999 retains about 90.5% of initialization after
1,000 updates and 36.8% after 10,000. Raw weights are the primary signal for
short architecture screens.

Only after measuring route behavior should the router receive a recurrence
index. A zero-initialized cycle bias or fixed recurrent-step encoding is a
cleaner first test than a recurrent GRU router. It must be passed separately
from attention metadata, and every learned entry must have a demonstrated
gradient path under truncated BPTT.

## Embedding and state lane

### Weight tying first

With the tokenizer fixed, straight input/output tying saves exactly
`402,653,184` XL parameters, yielding `1,384,120,320` parameters. It does not
reduce the vocabulary-logit matrix multiplication. Run a 2-by-2 control:

```text
{untied, tied} x {bp_min_steps=2, bp_min_steps=3}
```

This separates the tying hypothesis from the early frozen-input-table effect.
Preserve the current input-only `sqrt(d)` scaling, verify shared storage and
initial scale, and update checkpoint/export semantics explicitly.[^tying]

A useful budget-neutral follow-up is to reallocate the tied-head saving to
experts. Seven XL E=4/top-1 conversions add `396,404,736` parameters, giving a
tied-plus-MoE model of `1,780,525,056` parameters, slightly below the current
dense XL. This is a compelling final comparison, but only after tying and MoE
have independent controls.

### Factorization and vocabulary changes later

A shared rank-512 input/output table plus projections is about 135.0M
parameters, saving about 670.3M versus both current vocabulary matrices. Rank
256 is about 67.5M, saving about 737.8M. These also constrain the classifier
rank and change logit compute, so they are representation experiments rather
than free compression.[^adaptive-inputs]

Changing the 262K tokenizer belongs in a separate data/tokenization lane. Hold
raw documents or characters, not token counts alone, fixed and report Danish,
English, code, and math fertility before attributing a gain to architecture.

### Initial state and fusion

Before adding a learned embedding to `zL_init`, compare the fixed-random buffer
with zero. Then test `state + alpha * injection` with one learned scalar per
level, initialized exactly to `alpha=1`. A vector gate or GRU is justified only
if this baseline-equivalent control helps. A recurrent-step or level embedding
should be reinjected where it is reachable by the gradient horizon; changing
the initial buffer to a parameter alone is ineffective.

## Normalization and activation lane

The current parameterless exit RMSNorm is applied at every H/L stack call and
is plausibly central to recurrence stability. Preserve it in the first norm
experiments.

The clean first change is a separate learnable gamma for each internal
attention and MLP RMSNorm, initialized to one, while leaving the stack-exit
cap parameterless. At XL this adds only 98,304 parameters across the 32
physical blocks. Then test an affine exit norm and QK norm independently.
OLMoE found both parametric RMSNorm and QK norm useful but measured throughput
costs, while OLMo 2 combines QK norm with reordered norm placement; quality
and B200 step time must both be reported.[^olmoe][^olmo2]

MoEUT's peri-layernorm plus ReLU is a coupled shared-depth hypothesis: ReLU's
positive homogeneity is part of its signal-propagation argument.[^moeut] Test
that bundle as a named variant after the controlled RMSNorm experiments. Do
not casually swap only ReLU into the current pre-norm SwiGLU block and call it
a MoEUT reproduction. SwiGLU remains the default control; GEGLU or ReLU-squared
comes later with active parameter/FLOP matching, activation-aware initialization,
and a small learning-rate grid.

## Attention and parallelism lane

### GQA is the first attention optimization

The attention layer already stores a distinct KV-head count internally, but
the Transformer hardcodes it equal to the query-head count. Expose and validate
that setting before learned sparse attention. For XL, 12 query heads and four
KV heads give a 3:1 grouping and roughly a 3x reduction in K/V projection and
cache width. For XXL, 14-to-7 is the conservative divisible choice.

The current cache path eagerly repeats K/V heads, and the converter and native
serving implementation hardcode MHA, so a YAML field alone would not realize
the inference benefit. Training, cache, export, and serving parity are one
feature gate. Uptraining a dense MHA checkpoint through pooled K/V projections
is a later option; fresh small runs are the cleaner first comparison.[^gqa]

### Local and sparse attention order

At 4K, the measured B200 job is already dominated more by GEMMs than attention;
sparsity is primarily a long-context project. The implementation order is:

1. define per-level attention policy and a dense PrefixLM mask oracle;
2. implement and gradient-test FA4 native local windows on SM100;
3. add real ring/paged local-window serving with absolute RoPE positions;
4. test deterministic static blocks such as local plus sinks/strides;
5. only then add learned MoBA or NSA routing.

For the L-local/H-full hypothesis, include a reverse-role control because the
current model has not demonstrated that H is the global level. MoBA and NSA
are promising at long contexts, but both require specialized selection and
kernel work with packed PrefixLM semantics; the public MoBA package's FA2 pin
is not a drop-in for this repository's FA4/CUDA 13/B200 stack.[^moba][^nsa]

MLA can reduce KV cache much more aggressively, but it changes fused QKV,
RoPE, cache layout, checkpoint conversion, and serving together. It is a later
architecture, not the first attention ablation.[^mla]

### What “parallel” should mean here

- Local grouped GEMM is the first parallel MoE execution path.
- Expert parallelism requires token all-to-all, explicit expert/data groups,
  and expert weights excluded from ordinary block-level FSDP all-gathers.
- Tensor parallelism is plausible for projections and attention once KV-head
  divisibility is specified.
- Context parallelism follows validated packed PrefixLM window semantics.
- Pipeline parallelism is a poor first fit because recurrence repeatedly
  crosses H/L boundaries while reusing weights.

The present FSDP policy wraps complete Transformer blocks. Without an expert
parallel design it will all-gather every expert bank at each recurrent call;
that is valid for a small correctness run but not a scalable sparse system.

## Experiment matrix

Use the same tokenizer, input order, packing, context, global supervised-token
budget, optimizer, and BP schedule unless the row explicitly changes one of
them. Use at least three seeds for short screens and a small learning-rate grid
for finalists.

| Stage | Row | Only intended change | Purpose |
|---|---|---|---|
| 0 | B0 | none | Dense reproducibility and telemetry baseline |
| 0 | Z0 | zero instead of fixed-random `zL_init` | Test whether the fixed level seed helps |
| 0 | F1 | learned scalar H/L injection, initialized to one | Baseline-equivalent fusion test |
| 1 | R0 | `L[last]`, E4/top-1 reference | Evidence-nominated dispatch and recurrence gate |
| 1 | M1 | `H[last]`, same expert geometry | Test the high-impact H counterhypothesis |
| 1 | M2 | `L[last]+H[last]` | Test complementary formation and maintenance |
| 1 | M3 | winning stream at `[first]` versus `[last]` | Confirm that stack-exit placement matters |
| 1 | M4 | winning placement, E8/top-2 half-width | Primary compute-matched MoE quality screen |
| 2 | E1-E4 | tied/untied crossed with BP2/BP3 | Embedding efficiency and credit assignment |
| 2 | N1 | affine internal RMSNorm; fixed exit cap | Clean norm-capacity test |
| 2 | Q1 | QK norm only | Attention stability test |
| 3 | C1 | best dense/MoE crossed with best foundation variant | Detect an interaction, not an additive assumption |
| 4 | A1 | native GQA | KV/cache and quality comparison |
| 4 | A2 | native L-window/H-full plus reverse role | Long-context static attention comparison |
| 4 | A3 | deterministic block sparsity | Kernel/quality gate before learned routing |
| 5 | A4 | MoBA or NSA routing | Learned long-context sparsity |

Run R0 first on XXS/S for functional coverage, then B for a meaningful quality
and B200 performance screen. Keep H2/L3 and BP5 fixed for the placement rows;
then repeat the dense baseline and winner under full BP8. Do not launch XL
until grouped GEMM, finite multi-GPU
steps, checkpoint resume, and route balance pass their gates. HRM1 is useful as
a one-stack recurrence-only diagnostic, but HRM2 is the target architecture.

## Required gates before scaling

1. Default dense configuration retains numerical parity.
2. E=1/top-1 matches dense SwiGLU outputs and gradients for `[T,d]` and
   `[B,S,d]`; a separate test covers the real top-1 router gradient rule.
3. Padding is excluded from dispatch and all router statistics.
4. Router call counts and gradient reachability match every supported BP value;
   auxiliary coefficient zero recovers dense behavior.
5. Compiled/uncompiled, full and L-only activation-checkpoint, one-step FSDP,
   DCP resume, and EMA behavior agree.
6. Every expected parameter has a gradient and update; finite checks must not
   silently skip `grad=None` experts.
7. B200 reporting includes end-to-end tokens/s, peak/reserved memory, kernel
   time, routing overhead, and load skew, not theoretical sparse FLOPs alone.
8. MoE checkpoints fail fast in the dense HF/vLLM converter until custom
   runtime support exists. GQA, tying, norm asymmetry, and positional settings
   likewise require resolved-model and export assertions.
9. Local-window and sparse attention pass exact packed PrefixLM forward and
   backward tests, cache/decode tests, and first-token local-versus-serving
   parity before long training.

## Local versus B200 validation boundary (2026-09-03)

The reference H-MoE is not B200-only. The repository dispatches packed
PrefixLM attention to a dense PyTorch implementation for `cpu`/`none`, and to
the custom Metal implementation for supported float32 MPS tensors (otherwise
the MPS route also falls back to dense attention). On the local CPU, a four-token
packed PrefixLM batch completed the full embedding, H2/L3 recurrence, final-L
E4/top-1 routing, language-model objective, and backward pass. It produced the
expected six router calls and finite, nonzero router gradients. The focused
MoE suite also passes 10 tests locally.

Local execution is therefore the correctness gate for configuration loading,
routing and padding semantics, auxiliary losses and telemetry, recurrence/BP
reachability, checkpoint plumbing, and tiny forward/backward or optimizer-step
smokes. It is not evidence about sparse speed or production memory behavior:
the reference dispatcher uses eager per-expert gathers, and the CPU/MPS
attention route does not execute the SM100 FA4 implementation.

A two-step end-to-end XXS CPU training smoke was also validated using a
synthetic 32-row sampled dataset, `WANDB_MODE=disabled`, float32,
`distributed_strategy=none`, and compilation disabled. It completed both
optimizer steps and emitted aggregate and per-call expert loads, probability
means, balance loss, z loss, auxiliary loss, and objective. Use
`scripts/create_tiny_sampled_dataset.py` to create a new temporary dataset and
compose with `data=dfm9_mini` before overriding `data.path`; the default
`data=hlm` config does not declare `target_only`, so a direct
`data.target_only=true` override fails Hydra's struct check unless it is added
with `+`.

The established experiment record is W&B on rank zero: `pretrain.py` logs the
resolved configuration, data metadata, parameter count, reduced `train/*` and
`val/*` metrics, while model checkpoints remain under `checkpoint_path`.
Evaluation writes generations to local JSONL when configured, and dedicated
scripts subsequently log evaluation families to the corresponding W&B run or
export W&B histories to CSV. `WANDB_MODE=offline` preserves a locally syncable
run; `WANDB_MODE=disabled` performs no W&B tracking. For short benchmark runs,
`BENCH_OUTPUT` can additionally persist the benchmark summary as local JSON.

Use B200 in two escalation stages. First run a single-device BF16 SM100/FA4
smoke to validate the production attention path and compilation interaction.
Then run the multi-device FSDP/checkpoint/resume smoke used by the actual
training backend. Credible throughput, peak-memory, scaling, and any substantive
XXS/S/B training comparison belong on that backend. A full eight-GPU allocation
is not required merely to establish model correctness, but is required to
validate the intended distributed training configuration.

CRM2 and CRM3 upper-level MoE are explicitly out of scope until their final
upper-state updates are made task-reachable. The current CRM2 forward returns
`z_L` immediately after the final H update; CRM3 similarly returns `z_S` after
final M and H updates. At the minimum BP settings those prioritized upper calls
can receive auxiliary router gradients but no language-model task gradient.

## Success and stop criteria

A sparse row advances only if it is stable, has no persistently dead expert,
keeps padding/drop errors at zero, and improves held-out loss or downstream
quality at a declared total-parameter and active-compute comparison. It must
also have a credible grouped-kernel path; a reference Python implementation is
not evidence of efficiency.

Stop or redesign a row if route collapse remains after a small coefficient
grid, route churn makes recurrent inference weight-bandwidth bound, expert
overhead erases the matched-compute benefit, or an apparent gain disappears
under an LR/seed control. Report total parameters, active parameters per call,
active FLOPs, token budget, tokens/s, memory, raw/EMA loss, and downstream
scores together.

Adaptive token-level recurrent depth is a plausible later HRM-native direction:
Mixture-of-Recursions routes tokens through different numbers of repeated
blocks.[^mixture-recursions] It changes the recurrence and cache contract more
deeply than feedforward MoE, so it should follow rather than precede a stable
routed-FFN baseline.

[^moeut]: MoEUT, arXiv:2405.16039.
[^olmoe]: OLMoE, arXiv:2409.02060.
[^megablocks]: MegaBlocks, arXiv:2211.15841.
[^deepseek-moe]: DeepSeekMoE, arXiv:2401.06066.
[^gqa]: GQA, arXiv:2305.13245.
[^moba]: MoBA, arXiv:2502.13189.
[^nsa]: Native Sparse Attention, arXiv:2502.11089.
[^mla]: DeepSeek-V2/MLA, arXiv:2405.04434.
[^olmo2]: OLMo 2, arXiv:2501.00656.
[^tying]: Press and Wolf, arXiv:1608.05859.
[^adaptive-inputs]: Adaptive Input Representations, arXiv:1809.10853.
[^mixture-recursions]: Mixture-of-Recursions, arXiv:2507.10524.
[^palm]: PaLM, arXiv:2204.02311.
[^huginn]: Scaling up Test-Time Compute with Latent Reasoning, arXiv:2502.05171.
[^mixture-depths]: Mixture-of-Depths, arXiv:2404.02258.
[^multi-token]: Better & Faster Large Language Models via Multi-token Prediction, arXiv:2404.19737.
[^retrieval-attention]: RetrievalAttention, arXiv:2409.10516.
[^demix]: DEMix Layers, arXiv:2108.05036.
[^local-ablation-results]: `private/ablation_results.tex`, reviewed 2026-09-02.
[^local-mech-interp-results]: `private/UPLOAD_RESULTS_TO_OVERLEAF/results.tex`, reviewed 2026-09-02.
[^local-big-dc]: `private/The big-DC MoE LLM design.pdf`, reviewed 2026-09-02.
