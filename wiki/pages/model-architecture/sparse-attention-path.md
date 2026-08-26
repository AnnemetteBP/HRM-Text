---
type: Technical Reference
title: Sparse Attention Path
description: 'Extend HRM context beyond 32K using learned sparse attention (NSA/MoBA/HSA)
  in H layers, building on the local-global attention path.'
tags:
- architecture
- hrm
- long-context
- sparse-attention
status: draft
last_updated: 2026-08-12
confidence: medium
part_of: /pages/model-architecture.md
---
# Sparse Attention Path

Part of [Model Architecture](/pages/model-architecture.md).

Added on 2026-08-12. Updated 2026-08-12 with MoBA and The Sparse Frontier.
Status: **proposal / research phase** -- not implemented, not validated.

## Motivation

The [Local-Global Attention Path](local-global-attention-path.md) extends
context to 32K by giving L layers a sliding window and H layers full global
attention. Beyond 32K, H's O(n^2) attention becomes the bottleneck:

| Context | H attention FLOPs (32 vlayers) | L attention FLOPs (96 vlayers, w=4096) | Total |
|---:|---:|---:|---:|
| 32K | 1.06 x 10^14 | 3.96 x 10^13 | 1.46 x 10^14 |
| 131K | 1.69 x 10^15 | 1.58 x 10^14 | 1.85 x 10^15 |
| 524K | 2.70 x 10^16 | 6.32 x 10^14 | 2.76 x 10^16 |

At 131K, H accounts for 91% of attention FLOPs. At 524K, 98%. To scale beyond
32K, H needs sub-quadratic attention.

## Background

Four approaches are relevant, plus a large-scale empirical study that guides
deployment decisions.

### NSA: Native Sparse Attention (DeepSeek, Feb 2025)

arXiv:2502.11089. Yuan et al.

Hierarchical sparse attention with two branches:

1. **Compression branch (coarse)**: tokens are grouped into blocks (e.g.,
   512 tokens/block). Block summaries are computed via MLP compression.
   Each query attends to all block summaries to identify relevant regions.
   Cost: O(n x n/block_size).

2. **Selection branch (fine)**: top-k blocks are selected per query based on
   compression scores. The query then attends to individual tokens within
   those k blocks. Cost: O(n x k x block_size).

Total: O(n x (n/block_size + k x block_size)). With block_size=512, k=8:
O(n x (256 + 4096)) = O(n x 4352) -- effectively linear.

Key properties:
- **Natively trainable**: trained end-to-end with sparse attention from
  scratch, not a post-hoc approximation. Maintains or exceeds full-attention
  quality on general benchmarks, long-context, and reasoning.
- **Hardware-aligned**: arithmetic intensity is balanced to maximize GPU
  utilization. Block compression and selection are implemented with
  Triton/CUDA kernels.
- **Speedup**: substantial speedup over full attention on 64K sequences for
  decoding, forward, and backward.
- Adds a "lightning indexer" in a smaller head dimension to keep the O(n^2)
  scoring practical. This is a learned component with extra parameters.

### MoBA: Mixture of Block Attention (Moonshot AI / Kimi, Feb 2025)

arXiv:2502.13189. Lu et al. Code: github.com/MoonshotAI/MoBA.

Applies MoE principles to attention. Context is partitioned into blocks;
a gating network routes each query token to the top-k most relevant blocks.

**Mechanism**:

```text
1. Split KV into n_blocks blocks of size B
2. Compute block summaries: K_bar = mean_pool(K, block_size=B)
3. Gate scores: s_i = <q, K_bar_i> (inner product per head)
4. Select top-k blocks per query (with causal constraint: no future blocks)
5. Current block always selected (causal masking within it)
6. Compute attention only over selected blocks (FlashAttention with varlen)
7. Combine outputs via online softmax
```

Key properties:
- **No new parameters**: the gate uses the existing K projection (mean-pooled).
  MoBA is a drop-in replacement for full attention with the same parameter
  count. This is critical for HRM -- no architecture change needed.
- **Seamless full/sparse transition**: any layer can switch between full
  attention and MoBA at any point during training. MoBA authors show 90% MoBA
  + 10% full attention training matches full attention quality.
- **Sliding window and attention sink are special cases of MoBA**: MoBA
  strictly generalizes both. The gate can learn to always select recent blocks
  (= sliding window) or initial blocks (= attention sink).
- **Layer-wise hybrid**: last few layers can remain full attention while
  others use MoBA. MoBA authors show this helps SFT (prompt loss masking
  + sparse attention causes gradient sparsity; full attention in later layers
  mitigates this).
- **Deployed in production**: Kimi uses MoBA for 1M-context requests.
  Llama-8B-1M-MoBA: block_size=4096, top_k=12, last 3 layers full attention,
  95.31% sparsity at 1M context.
- **Scaling law**: MoBA matches full attention within 1e-3 loss at 8K.
  Trailing loss slightly higher at 32K but gap narrows with scale.
- **Speedup**: 6.5x at 1M prefill, 16x at 10M (attention layer only).
- **Fine-grained block segmentation helps**: finer blocks (more, smaller)
  improve quality at fixed sparsity, consistent with MoE literature.

### SubQ / SSA: Subquadratic Sparse Attention (Subquadratic Inc., May 2026)

Subquadratic Inc. (Miami-based startup, $29M seed). Product: "SubQ" model.

Architecture: "Subquadratic Sparse Attention" (SSA). Uses **learned,
content-adaptive sparsity**: for each query token, the model dynamically
selects a small subset of positions and computes exact attention only over
those. Claims O(n) scaling.

Key claims (self-reported, not independently verified):
- 12M token research context, 1M production context
- 52x speedup vs FlashAttention-2 at 1M tokens
- RULER 128K: 95.0-95.6% (comparable to Claude Opus 4.6: 94.8%)
- SWE-Bench Verified: 81.8%

Caveats:
- **No public paper** describing SSA mechanism in reproducible detail.
- **Closed weights**, closed-source implementation.
- Claims are self-reported. No arXiv paper as of Aug 2026.
- Public skepticism: may be a sparse-attention finetune of existing models
  rather than a fully new architecture.

Relevance: demonstrates that learned content-adaptive sparse attention can
reach frontier quality at very long context (if claims hold). The approach
is conceptually similar to NSA's selection branch but reportedly without the
separate compression branch.

### HSA: Hierarchical Sparse Attention (Hu et al., Nov 2025)

arXiv:2511.23319. "Every Token Counts: Generalizing 16M Ultra-Long Context."

8B-parameter MoE model trained on 8T tokens. Uses Hierarchical Sparse
Attention (HSA) with three key properties:
1. **Sparsity**: each token attends to a small subset of positions.
2. **Random-access flexibility**: any position can be accessed (not
   limited to local windows or fixed patterns).
3. **Length generalization**: trained on shorter sequences, generalizes
   to much longer ones.

Results: 90%+ accuracy on in-context retrieval up to 16M tokens. Performs
comparably to full-attention baselines on in-domain lengths.

Relevance: demonstrates that sparse attention can generalize to extreme
lengths (16M) with proper training. The hierarchical structure may map
naturally to HRM's H/L hierarchy.

### The Sparse Frontier: Empirical Study (Nawrot et al., Apr 2025)

arXiv:2504.17768. Nawrot, Li, Huang, Ruder, Marchisio, Ponti
(Edinburgh/Cohere/Meta).

Largest-scale empirical analysis of **training-free** sparse attention:
6 methods, 3 model families (Qwen 2.5, Llama 3.1, Gemma 3), sizes 4B-72B,
sequences 16K-128K, sparsity up to 95%.

**Taxonomy** (4 design axes):

| Axis | Options |
|---|---|
| Unit of sparsification | blocks/pages, verticals+slashes, individual tokens |
| Importance estimation | fixed patterns, content-aware (attention scores, key norms) |
| Budget allocation | uniform, adaptive (per-layer, per-head, threshold-based) |
| KV cache management | eviction (permanent discard), full cache (selective load) |

**Key findings**:

1. **Sparse attention is effective**: larger sparse models outperform smaller
   dense ones at equivalent cost. For Qwen at 128K, only high-sparsity
   configs (0.8-0.93) lie on the Pareto frontier.

2. **Prefill vs decode differ fundamentally**: during prefill, fine-grained
   per-query importance estimation is impractical (cost is quadratic, and no
   kernel translates fine-grained sparsity to wall-clock gains). Methods must
   choose between global fine-grained selection (Vertical-Slash) or
   block-to-block selection (Block-Sparse). During decode, per-query
   selection is cheap (single query), so token-to-page methods (Quest)
   achieve better generalisation and higher sparsity tolerance.

3. **Longer sequences tolerate higher sparsity**: at 1/20 budget, relative
   error drops from 0.33 (16K) to 0.20 (64K). Optimal token budget grows
   sublinearly with sequence length.

4. **Sparsity tolerance varies dramatically across tasks**: single QA
   tolerates 95% sparsity. Multi-hop reasoning and aggregation degrade at
   50-67% sparsity. Evaluating only on retrieval benchmarks masks failures.

5. **Full cache > eviction**: Quest (full cache, selective load) outperforms
   SnapKV/Ada-SnapKV (eviction) because discarded tokens may become relevant
   later. Eviction trades memory for irreversibility.

6. **Training-free methods are fundamentally limited** during prefill by the
   lack of an efficient fine-grained estimator + matching kernel.
   Training-based methods (NSA, MoBA) sidestep this by learning the
   selection mechanism during pretraining.

**Relevance to HRM**: confirms that training-based sparse attention (not
training-free) is the right approach. The task-dependent sparsity tolerance
means HRM's sparse attention must be evaluated on diverse tasks (RULER VT,
multi-hop, aggregation), not just needle-in-a-haystack. The sublinear budget
scaling finding supports using larger block sizes at longer contexts.

## Design Options

All options assume L layers use sliding window (w=4096) from the
[Local-Global Attention Path](local-global-attention-path.md). The
options differ in how H layers are made sub-quadratic.

### Option A: NSA-style H

- H layers: NSA dual-branch sparse attention (compression + selection)
- Block size: 512 tokens, top-k=8 blocks selected per query
- Cross-injection: unchanged (z_H, z_L remain full-sequence tensors)
- H still stores full token KV cache (needed for future selection)
- FLOPs: O(n x 4352) per H virtual layer (vs O(n^2) for full)
- Adds learned compression MLP + lightning indexer parameters to H blocks

### Option B: SSA-style H

- H layers: learned content-adaptive sparse attention (SubQ-style)
- Each query dynamically selects k positions via a learned routing function
- Mechanism not published; would need to implement from first principles
  or wait for Subquadratic Inc. to release details
- Conceptually simpler than NSA (single-branch selection, no compression)
- FLOPs: O(n x k) per H virtual layer, where k is the selection budget

### Option C: HSA-style Hierarchical H

- H layers: multi-level sparse attention with increasing receptive field
- Could map to HRM's H cycles: each H cycle uses a different sparsity level
  - Cycle 1: local blocks (small receptive field)
  - Cycle 2: global blocks (large receptive field)
- Natural fit for HRM's recurrent structure
- More complex implementation than Options A or B

### Option D: CRM2 Compression

- H layers: operate on latent slots (not token sequence) via
  [CRM2](crm2-latent-compressed-experimental-path.md) compression
- H attention on K=256 latents: O(K^2) = 65,536 per virtual layer -- negligible
- Token-to-latent compression via cross-attention (CRM2 mechanism)
- Smallest KV cache of all options
- Changes the architecture: H no longer operates on token sequences

### Option E: MoBA-style H (recommended)

- H layers: MoBA block attention with top-k gating
- No new parameters: gate uses mean-pooled K projection (existing weights)
- Block size and top-k configurable per context length:

| Context | Block size | Top-k | n_blocks | Sparsity | Coverage |
|---:|---:|---:|---:|---:|---:|
| 32K | 2048 | 4 | 16 | 75% | 25% |
| 131K | 4096 | 12 | 32 | 62.5% | 37.5% |
| 524K | 4096 | 12 | 128 | 90.6% | 9.4% |
| 1M | 4096 | 12 | 256 | 95.3% | 4.7% |

- **Hybrid training**: start from HRM-Text XL checkpoint with full H attention,
  switch to MoBA for continued pretraining on long sequences. MoBA authors
  show 90% MoBA + 10% full attention matches full attention quality. No loss
  spikes during transition.
- **Layer-wise hybrid**: if SFT quality degrades, switch last few H
  applications back to full attention. MoBA authors show this helps with
  loss-masked SFT gradients.
- **Seamless fallback**: if MoBA quality is insufficient, any H layer can
  revert to full attention by setting top-k = n_blocks. Same parameters.
- **PrefixLM compatibility**: MoBA's causal constraint (no future blocks)
  maps to PrefixLM by treating prefix tokens as always-selected blocks.
  Current block causal masking aligns with suffix causal masking.
- Cross-injection: unchanged (z_H, z_L remain full-sequence tensors)
- H stores full token KV cache (MoBA reduces FLOPs, not memory)
- Open-source implementation available (github.com/MoonshotAI/MoBA)

## FLOPs Analysis

Convention: attention FLOPs = 2 x (work) x d, where d = hidden_size = 1536.
This counts QK^T + softmax x V interactions. QKV projections and MLP are
excluded (identical across configs).

### At 131K context (n=131072)

| Config | L FLOPs (96 vlayers) | H FLOPs (32 vlayers) | Total | vs all-full |
|---|---:|---:|---:|---:|
| All-full | 1.58 x 10^14 | 1.69 x 10^15 | 1.85 x 10^15 | 1.0x |
| Idea 1 (L=window, H=full) | 1.58 x 10^14 | 1.69 x 10^15 | 1.85 x 10^15 | 1.0x |
| Option A (NSA H, bs=512, k=8) | 1.58 x 10^14 | 5.28 x 10^13 | 2.11 x 10^14 | 8.8x faster |
| Option E (MoBA H, bs=4096, k=12) | 1.58 x 10^14 | 6.33 x 10^14 | 7.91 x 10^14 | 2.3x faster |
| Option E (MoBA H, bs=512, k=8) | 1.58 x 10^14 | 5.28 x 10^13 | 2.11 x 10^14 | 8.8x faster |
| Option D (CRM2) | 1.58 x 10^14 | ~0 | 1.58 x 10^14 | 11.7x faster |

Note: MoBA with bs=4096, k=12 (Kimi deployment settings) has only 62.5%
sparsity at 131K -- conservative. With bs=512, k=8 (NSA-like settings),
sparsity is 96.9% and FLOPs match Option A. The Sparse Frontier finding
that longer sequences tolerate higher sparsity supports finer-grained
settings at 131K+.

### At 32K context (n=32768)

| Config | L FLOPs | H FLOPs | Total | vs all-full |
|---|---:|---:|---:|---:|
| All-full | 3.16 x 10^14 | 1.06 x 10^14 | 4.22 x 10^14 | 1.0x |
| Idea 1 (L=window, H=full) | 3.96 x 10^13 | 1.06 x 10^14 | 1.46 x 10^14 | 2.9x faster |
| Option E (MoBA H, bs=2048, k=4) | 3.96 x 10^13 | 2.64 x 10^13 | 6.60 x 10^13 | 6.4x faster |
| Option E (MoBA H, bs=512, k=8) | 3.96 x 10^13 | 1.32 x 10^13 | 5.28 x 10^13 | 8.0x faster |
| Option D (CRM2) | 3.96 x 10^13 | ~0 | 3.96 x 10^13 | 10.7x faster |

## KV Cache Analysis (inference, bf16)

Sparse attention (NSA/MoBA/HSA) reduces **attention FLOPs** but does not
reduce **KV cache** for H layers. The model must still store all token KV
because future queries may select any token. Only compression (Option D)
reduces KV cache.

| Config | L KV (96 vlayers) | H KV (32 vlayers) | Total | x current |
|---|---:|---:|---:|---:|
| Current (4096, all full) | 2.41 GB | 0.80 GB | 3.22 GB | 1.0x |
| Idea 1 (32K) | 2.41 GB | 6.44 GB | 8.86 GB | 2.75x |
| Option E (131K, MoBA H) | 2.41 GB | 25.77 GB | 28.18 GB | 8.75x |
| Option D (131K, CRM2 H) | 2.41 GB | 0.05 GB | 2.46 GB | 0.76x |

For deployment on limited VRAM (e.g., MIG 1g.23gb ~20.5 GB):
- Option E at 131K: 28.18 GB KV cache -- does not fit (same as full H)
- Option D at 131K: 2.46 GB KV cache -- fits easily
- Idea 1 at 32K: 8.86 GB KV cache -- fits

The Sparse Frontier finding that full-cache methods (Quest) outperform
eviction methods (SnapKV) suggests that KV eviction is not a viable
alternative to compression for quality-sensitive deployment.

## Training Implications

### Native Training

Both NSA and MoBA are designed for **native training** (sparse attention
from the start or via continued pretraining, not post-hoc modification).

- Post-hoc sparse attention (e.g., StreamingLLM, H2O) degrades quality
  because the model was trained expecting full attention.
- Native training lets the model learn to use sparse attention patterns
  during pretraining, maintaining quality.
- The Sparse Frontier confirms: training-free methods are fundamentally
  limited during prefill by the lack of efficient fine-grained estimation.
  Training-based methods sidestep this by learning the selection mechanism.

For HRM with MoBA (Option E):
- Start from HRM-Text XL checkpoint (step 1,650,000) with full H attention.
- Switch H layers to MoBA for continued pretraining on long sequences.
- MoBA authors show seamless transition with no loss spikes.
- Use 90% MoBA + 10% full attention schedule if quality dips.
- Training data should include long sequences (32K-131K) to learn
  long-range block selection patterns.

### RoPE Extension

Same requirements as Idea 1:
- L layers: no change (window=4096, existing RoPE sufficient)
- H layers: need RoPE extension to target context length (131K = 32x
  extension)
- YaRN or NTK-aware scaling recommended for large extensions (32x)
- May require fine-tuning on long sequences for YaRN to work well
- MoBA authors use position interpolation for 128K to 1M extension

### BPTT Interaction

Current BPTT: 5 of 8 recurrent applications have gradients (80 virtual
layers with grad, 48 without). Sparse attention in H does not change
the BPTT schedule, but:

- MoBA adds no parameters (gate uses existing K projection). No new
  gradient paths needed. BPTT allocation unchanged.
- NSA adds a compression MLP and lightning indexer (~1-2% of block
  parameters). These follow the H BPTT allocation.

### Implementation Complexity

| Option | Complexity | Key challenges |
|---|---|---|
| A (NSA H) | High | Custom Triton/CUDA kernels for block compression + top-k selection; FA4 does not support dynamic token selection natively; extra parameters |
| B (SSA H) | Unknown | No published mechanism; would need to design from scratch |
| C (HSA H) | High | Multi-level sparse attention; custom kernels; limited public implementation details |
| D (CRM2) | Medium | CRM2 already implemented; main work is CRM2 evaluation at long context |
| E (MoBA H) | **Medium-low** | Open-source implementation exists; no new parameters; FlashAttention with varlen for block attention; causal + PrefixLM masking needs adaptation; gate is a simple inner product |

Option E (MoBA) is the lowest-complexity path to sub-quadratic H attention:
- No new parameters to implement or debug
- Open-source reference implementation (Moonshot AI)
- Seamlessly falls back to full attention (top-k = n_blocks)
- Block attention uses standard FlashAttention with variable lengths
- Main adaptation work: PrefixLM causal masking in MoBA's block framework

## Deployment Guidance

From The Sparse Frontier findings:

1. **Evaluate on diverse tasks**: sparsity tolerance varies from 95%
   (single QA) to 50% (multi-hop reasoning). Needle-in-a-haystack alone
   is insufficient. Use RULER (NIAH, VT, CWE) + natural language tasks.

2. **Sublinear budget scaling**: at longer contexts, increase sparsity.
   MoBA's fixed top-k with growing block count naturally implements this.
   At 131K with bs=4096, k=12: only 37.5% coverage needed. At 1M: 4.7%.

3. **Full cache over eviction**: The Sparse Frontier shows Quest (full
   cache) outperforms SnapKV (eviction). MoBA and NSA both retain full KV
   cache, aligning with this finding. CRM2 (Option D) is compression, not
   eviction -- also preserves all information in latent form.

4. **Phase-dependent deployment**: MoBA for prefill (sparse), full attention
   for decode (if quality matters). This is exactly what Kimi does:
   Llama-8B-1M-MoBA uses MoBA for prefill, full attention for generation.

## Risks

1. **Selection accuracy**: MoBA's mean-pooled key gating is a simple
   heuristic. If block summaries don't capture relevant information,
   selection may miss critical blocks. MoBA's fine-grained block
   segmentation (smaller blocks) mitigates this at fixed sparsity.

2. **No public SSA mechanism**: SubQ's claims are unverified. Without a
   published paper, Option B cannot be evaluated or implemented.

3. **KV cache does not shrink**: Options A, E reduce FLOPs but not KV
   cache. For deployment on limited VRAM, only Option D (compression)
   reduces KV cache. This is a fundamental limitation of sparse attention
   without compression.

4. **HRM-specific kernel work**: MoBA implementations exist for standard
   transformers. HRM's recurrent structure with PrefixLM and
   per-application attention requires adapting the block attention
   framework, particularly the causal masking within blocks.

5. **Training stability with long sequences**: 131K context training
   requires significant memory even with gradient checkpointing. Sparse
   attention reduces FLOPs but not activation memory, so the memory
   constraint is the same as Idea 1.

6. **Recurrent block selection consistency**: in HRM, H is applied 2x per
   forward pass. If each H application independently selects blocks, the
   model may attend to different blocks in cycle 1 vs cycle 2. This could
   be beneficial (multi-round refinement of different regions) or
   harmful (inconsistent attention pattern across cycles). Needs
   empirical evaluation.

## Recommended Path

1. **Phase 1**: Implement Idea 1 (L=window, H=full) for 32K context.
   Low implementation cost, fits in 20.5 GB MIG for inference, validated
   FLOPs/KV analysis. H attention-only gradient checkpointing for
   batch=4 training (24% overhead, fits 183 GB budget).

2. **Phase 2**: Implement Option E (MoBA H) for 131K context.
   - Start from Phase 1 checkpoint (32K, L=window, H=full).
   - Switch H to MoBA with bs=2048, k=4 (75% sparsity at 32K, then
     increase block size for 131K).
   - Continued pretraining on long sequences (32K-131K) with MoBA.
   - Use 90% MoBA + 10% full attention if quality dips.
   - Evaluate on RULER (NIAH, VT, CWE) + natural language multi-hop tasks.
   - No new parameters, open-source reference implementation, seamless
     fallback to full attention. Lowest-risk path to sub-quadratic H.

3. **Phase 3** (if KV cache is the bottleneck): Evaluate Option D (CRM2)
   for 131K+ context where VRAM is limited. CRM2 is already implemented.
   Main question is compression quality at long context. Evaluate on
   long-range retrieval benchmarks (RULER, Needle-in-a-Haystack).

4. **Phase 4** (if MoBA quality is insufficient): Implement Option A (NSA H)
   for cases where MoBA's simple gate underperforms NSA's learned
   compression + selection. Requires custom kernel development.

5. **Monitor SubQ/SSA**: if Subquadratic Inc. publishes a paper, evaluate
   Option B as a potentially simpler alternative to NSA.

## Relationship to Other Paths

- [Local-Global Attention Path](local-global-attention-path.md): Phase 1
  foundation. This path builds on it.
- [Compression](compression.md): current HRM has no compression. Option D
  uses CRM2-style compression for H.
- [CRM2](crm2-latent-compressed-experimental-path.md): Option D combines
  CRM2 compression with sparse attention concepts.
- [CRM3](crm3-latent-compressed-experimental-path.md): alternative
  compression approach. Could also be combined with sparse attention.
- [Schedule](schedule.md): recurrence schedule and BPTT allocation are
  unchanged by sparse attention. MoBA adds no parameters, so BPTT is
  identical. NSA adds ~1-2% parameters to H blocks.
