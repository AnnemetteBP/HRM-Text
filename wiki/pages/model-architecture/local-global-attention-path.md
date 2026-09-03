---
type: Technical Reference
title: Local-Global Attention Path
description: 'Extend HRM context to 32K by using sliding-window attention in L layers
  and full global attention in H layers.'
tags:
- architecture
- hrm
- long-context
- attention
status: draft
last_updated: 2026-09-02
confidence: medium
part_of: /pages/model-architecture.md
---
# Local-Global Attention Path

Part of [Model Architecture](/pages/model-architecture.md).

Added on 2026-08-12. Status: **proposal** — not implemented, not validated.

## Implementation audit (2026-09-02)

This audit supersedes the implementation sketch and Phase 1.5 cache estimate
retained below as historical design context. The high-level local-L/global-H
hypothesis remains unvalidated.

- The current `TransformerConfig` has no attention-window field and hardcodes
  the KV-head count to the query-head count. The packed PrefixLM dispatcher and
  this repository's FA4 wrapper do not currently pass a window or sparse-mask
  argument.
- Current FA4 main exposes local-window and block-mask primitives, but the
  repository installs an unpinned Git revision. Support on the deployed B200
  environment must be feature-probed, backward-tested, and pinned before it is
  treated as available.
- The simple inference cache writes absolute positions into a fixed tensor and
  attends from index zero. Merely allocating a 4K L cache would overflow after
  position 4095; local serving needs ring or paged eviction while preserving
  absolute RoPE positions.
- The native HF/vLLM HRM path does not currently consume per-level window
  settings. Training, conversion, and serving support are all implementation
  work, not configuration-only changes.
- The first three L calls see the initial `z_H=x`; the next three see the first
  learned H update; the final H update is returned without a following L call.
  L therefore receives one learned H update, not two. H/L role labels still
  require a reverse-pattern control.

The corrected XL BF16 batch-one virtual-cache comparison at 32K, excluding
allocator overhead, is:

| Attention pattern | L cache | H cache | Total |
|---|---:|---:|---:|
| All 128 virtual layers retain 32K | 19.33 GB | 6.44 GB | 25.77 GB |
| L retains 4K; H retains 32K | 2.42 GB | 6.44 GB | 8.86 GB |

The local/global layout therefore saves about 16.91 GB, or 65.6%, relative to
an all-full 32K cache. It does not reduce L from 2.41 GB to 0.30 GB; that older
Phase 1.5 figure was low by a factor of eight.

## Motivation

Current HRM-Text XL uses full attention in both H and L levels, trained at
`max_seq_len=4096`. Extending to 32K context with full attention in all 128
virtual layers would cost 8x the KV cache and 8x the attention FLOPs, making
inference impractical and training expensive.

The key observation: the HRM schedule already separates "global" (H) from
"local/refinement" (L) roles through cross-injection. L runs 3 cycles between
each H cycle, refining local representations. H gathers global context and
injects it into L. This maps naturally to a mixed attention pattern:

- **L layers**: sliding window attention (window=4096) -- local precision, O(n x w)
- **H layers**: full global attention (up to 32768) -- global awareness, O(n^2)

H provides the big picture; L refines local details within a fixed window.
The cross-injection mechanism is unchanged.

## Design

### Attention Pattern

| Block | Applications per forward pass | Virtual layers | Attention | Complexity |
|---|---:|---:|---|---|
| L | 6 (3 cycles x 2 H cycles) | 96 | Sliding window, w=4096 | O(n x 4096) |
| H | 2 (2 H cycles) | 32 | Full global, up to 32768 | O(n^2) |
| Total | 8 | 128 | -- | -- |

Both H and L use the same RoPE position encoding (global positions 0..n), but L
attention is masked to a sliding window. PrefixLM attention applies within the
window: prefix tokens attend bidirectionally to nearby prefix tokens, suffix
tokens attend causally to previous tokens within the window.

### Cross-Injection (unchanged)

```text
z_L = z_L + z_H   (H injects global context into L)
z_H = z_H + z_L   (L injects local refinements into H)
```

Both `z_L` and `z_H` remain full-sequence tensors `[T, d]`. No architectural
compression. The injection schedule and BPTT allocation are unchanged.

### Schedule (unchanged)

```text
for each of 2 H cycles:
  run 3 L cycles  (sliding window attention, w=4096)
  run 1 H cycle   (full global attention, up to 32768)
```

## KV Cache Analysis (inference, bf16)

Constants:
- KV per token per virtual layer: 2 (K,V) x 12 heads x 128 dim x 2 bytes = 6144 bytes
- 96 L virtual layers, 32 H virtual layers

| Config | L KV | H KV | Total KV | x current |
|---|---:|---:|---:|---:|
| Current (4096, all full) | 2.41 GB | 0.80 GB | 3.22 GB | 1.0x |
| Idea 1 (32K, L=window, H=global) | 2.41 GB | 6.44 GB | 8.86 GB | 2.75x |
| All-full (32K) | 19.33 GB | 6.44 GB | 25.77 GB | 8.0x |

L KV is fixed at 2.41 GB regardless of total context length because the
sliding window caps at 4096 entries per layer. Only H KV grows with context
length. At 32K, Idea 1 uses 2.75x current KV cache, while all-full would use
8.0x.

## Attention FLOPs at 32K

Attention FLOPs per forward pass (QK^T + softmax x V, proportional):

| Config | L FLOPs | H FLOPs | Total | vs all-full |
|---|---:|---:|---:|---:|
| All-full (32K) | 3.16 x 10^14 | 1.06 x 10^14 | 4.22 x 10^14 | 1.0x |
| Idea 1 (32K) | 3.96 x 10^13 | 1.06 x 10^14 | 1.46 x 10^14 | 2.9x faster |

L FLOPs drop by 8x (from O(n^2) to O(n x w)). H FLOPs unchanged. Net speedup:
2.9x for attention only. MLP FLOPs are unchanged (O(n x d^2) regardless of
attention pattern), so the end-to-end speedup is smaller than 2.9x but still
significant for long sequences where attention dominates.

## Training Memory (8x B200, FSDP)

Per-GPU budget: ~183 GB VRAM. Model+optimizer shards ~2.7 GB per GPU, leaving
~177 GB for activations.

Sliding window reduces attention FLOPs but not activation memory because FA4
does not materialize attention matrices. Activation memory is dominated by
hidden states and MLP intermediates:

- Per virtual layer application (32K, batch=1, bf16): ~8.3 GB
- 8 applications without grad checkpointing: ~66 GB (fits in 177 GB budget)
- With BPTT (5 steps with grad): stored activations for 5 of 8 applications

This matches the prior analysis: 32K at batch=1/gpu fits without grad
checkpointing. With grad checkpointing, 32K at batch=8 fits. The sliding
window does not change these numbers materially; its benefit is FLOPs and
inference KV cache, not training memory.

## RoPE Extension

Current: RoPE theta=10000, `max_position_embeddings=4096`. H layers need
position encoding up to 32768 (8x extension). L layers only attend within a
4096 window, so extended positions are irrelevant to L attention.

Options:

1. **NTK-aware interpolation**: scale base frequency
   `theta' = theta x scale^(d/(d-2))` where `scale = 32768/4096 = 8`.
   Non-linearly scales RoPE frequencies: interpolates low frequencies,
   extrapolates high frequencies. No fine-tuning required for moderate
   extensions. Well-tested for 8x scaling.

2. **YaRN**: three-range frequency partition (interpolate low, smooth
   middle, extrapolate high). Better quality than NTK for large scale
   factors. Requires short fine-tuning for best results.

3. **Reinitialize with larger `max_seq_len`**: clean but requires continued
   pretraining.

Recommendation: NTK-aware scaling applied uniformly to all layers. L layers
use the same global position encoding but are attention-masked to the sliding
window. This keeps position encoding consistent between H and L, avoiding
mismatched position semantics in cross-injection.

## Historical implementation sketch (superseded 2026-09-02)

1. **L block attention**: add `sliding_window=4096` to FA4 attention call.
   FA4 natively supports `sliding_window` parameter. The mask limits each
   token to attend to the previous 4096 positions (prefix bidirectional
   within window, suffix causal within window).

2. **H block attention**: no change (full attention).

3. **Config**: add to `hrm.yaml`:
   ```yaml
   L_sliding_window: 4096
   H_sliding_window: null   # null = full attention
   ```

4. **vllm**: sliding window reduces L KV cache to 4096 entries. vllm
   supports `sliding_window` natively. H still needs full KV cache up to
   `max_model_len=32768`.

5. **Training**: increase `max_seq_len` to 32768. Apply NTK scaling to RoPE.
   Use gradient checkpointing if batch > 1 per GPU.

## Risks

1. **Information loss in L**: L can only attend to local context (4096
   tokens). Critical information outside the window must reach L through
   H injection (`z_H -> z_L`). The earlier statement that L receives two
   learned H updates per forward is superseded: it receives only the first H
   update before its final three calls. This may fail on tasks requiring
   fine-grained long-range attention in L (e.g., exact token-level retrieval
   across 32K tokens).

2. **H is the scaling bottleneck**: H uses full O(n^2) attention. Beyond
   32K (e.g., 100K+), H would also need sparse or sliding attention. See
   [Sparse Attention Path](sparse-attention-path.md).

3. **RoPE extrapolation with recurrence**: the same positions are encoded
   multiple times across virtual layers (repeated RoPE application). NTK
   scaling has been tested for standard transformers but not for recurrent
   architectures with repeated position encoding. Behavior at 8x scale
   is uncertain without empirical validation.

4. **PrefixLM interaction**: sliding window in PrefixLM mode needs careful
   masking. The bidirectional prefix part should also respect the window,
   not just the causal suffix. FA4 handles this via `sliding_window` + the
   existing PrefixLM cu_seqlens metadata, but this combination needs testing.

## Historical Phase 1.5 cache estimate (superseded 2026-09-02)

The table in this section is retained to show the original proposal. Its
`0.30 GB` optimized-L value and `6.74 GB` total are incorrect; use the
2026-09-02 audit table above.

Phase 1 keeps full `max_seq_len` KV cache for all layers (simpler, no vllm
changes). Phase 1.5 caps L layer KV cache at `sliding_window` entries:

| Component | Current (Phase 1) | Phase 1.5 |
|---|---|---|
| L KV (96 vlayers) | 2.41 GB (full 32K) | 0.30 GB (4K window) |
| H KV (32 vlayers) | 6.44 GB | 6.44 GB (unchanged) |
| Total | 8.86 GB | 6.74 GB |
| Savings | -- | 2.12 GB (24%) |

Implementation:
- Training: `Cache.create` for L caches uses `max_seq_len=sliding_window`
- vllm: per-level KV cache sizes in `hrm_text.py` model. vllm's paged KV
  cache would need per-layer `max_cache_len` support. Requires changes to
  vllm's `hrm_text.py` and potentially the paged cache allocator.
- No model weight changes, no retraining needed -- pure inference optimization.

## Relationship to Other Paths

- **Compression**: this path does not compress between levels. Both z_H and
  z_L remain full token-sequence tensors. See [Compression](compression.md).
- **CRM2/CRM3**: those paths compress H into latent slots. This path keeps
  H at full token resolution but limits L to a sliding window. The two
  approaches are orthogonal and could be combined.
- **Sparse Attention Path**: the natural next step beyond 32K. Replaces H
  full attention with learned sparse attention (NSA/SSA-style). See
  [Sparse Attention Path](sparse-attention-path.md).
