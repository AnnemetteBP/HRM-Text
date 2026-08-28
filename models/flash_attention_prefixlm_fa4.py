from typing import Optional

import torch
from torch import Tensor

from models.flash_attention_prefixlm_common import (
    PREFIXLM_ROUTING_KEYS,
    prefixlm_prepared_from_tensors,
    prefixlm_routing_from_tensors,
)

__all__ = ["flash_attn_varlen_prefixlm"]


def _fa4_varlen(
    q: Tensor,
    k: Tensor,
    v: Tensor,
    *,
    cu_seqlens_q: Tensor,
    cu_seqlens_k: Tensor,
    max_seqlen_q: int,
    max_seqlen_k: int,
    causal: bool,
    seqused_q: Optional[Tensor] = None,
    seqused_k: Optional[Tensor] = None,
) -> Tensor:
    try:
        from flash_attn.cute import flash_attn_varlen_func
    except ImportError as exc:
        raise ImportError(
            "accelerator_type=sm100 requires FlashAttention 4 from flash_attn.cute."
        ) from exc

    out, _ = flash_attn_varlen_func(
        q,
        k,
        v,
        cu_seqlens_q=cu_seqlens_q,
        cu_seqlens_k=cu_seqlens_k,
        max_seqlen_q=max_seqlen_q,
        max_seqlen_k=max_seqlen_k,
        seqused_q=seqused_q,
        seqused_k=seqused_k,
        causal=causal,
        return_lse=True,
    )
    return out


class _MaskUndefinedSequsedGrad(torch.autograd.Function):
    """Zero FA4 gradients for storage rows excluded by ``seqused``."""

    @staticmethod
    def forward(ctx, tensor: Tensor, used: Tensor) -> Tensor:
        ctx.save_for_backward(used)
        return tensor

    @staticmethod
    def backward(ctx, grad: Tensor) -> tuple[Tensor, None]:
        (used,) = ctx.saved_tensors
        return grad.masked_fill(~used[:, None, None], 0), None


def _mask_undefined_seqused_grad(tensor: Tensor, used: Tensor) -> Tensor:
    return _MaskUndefinedSequsedGrad.apply(tensor, used)


def _flash_attn_varlen_prefixlm_seqused(
    q: Tensor,
    k: Tensor,
    v: Tensor,
    *,
    is_causal: bool,
    prefix_lens: Tensor,
    causal_lens: Tensor,
    cu_seqlens: Tensor,
    cu_seqlens_shifted: Tensor,
    prefix_mask: Tensor,
    causal_mask: Tensor,
    max_seqlen_prefix: Tensor,
    max_seqlen_causal: Tensor,
    max_seqlen_all: Tensor,
) -> Tensor:
    prefix_q = _mask_undefined_seqused_grad(q, prefix_mask)
    prefix_k = _mask_undefined_seqused_grad(k, prefix_mask)
    prefix_v = _mask_undefined_seqused_grad(v, prefix_mask)
    out_prefix = _fa4_varlen(
        prefix_q,
        prefix_k,
        prefix_v,
        cu_seqlens_q=cu_seqlens,
        cu_seqlens_k=cu_seqlens,
        seqused_q=prefix_lens,
        seqused_k=prefix_lens,
        max_seqlen_q=int(max_seqlen_prefix.item()),
        max_seqlen_k=int(max_seqlen_prefix.item()),
        causal=is_causal,
    )

    if int(max_seqlen_causal.item()) == 0:
        return out_prefix.masked_fill(~prefix_mask[:, None, None], 0)

    causal_q = _mask_undefined_seqused_grad(q, causal_mask)
    valid_mask = prefix_mask | causal_mask
    causal_k = _mask_undefined_seqused_grad(k, valid_mask)
    causal_v = _mask_undefined_seqused_grad(v, valid_mask)
    out_causal = _fa4_varlen(
        causal_q,
        causal_k,
        causal_v,
        cu_seqlens_q=cu_seqlens_shifted,
        cu_seqlens_k=cu_seqlens,
        seqused_q=causal_lens,
        max_seqlen_q=int(max_seqlen_causal.item()),
        max_seqlen_k=int(max_seqlen_all.item()),
        causal=True,
    )
    out = torch.where(prefix_mask[:, None, None], out_prefix, out_causal)
    return out.masked_fill(~valid_mask[:, None, None], 0)


def flash_attn_varlen_prefixlm(
    q: Tensor,
    k: Tensor,
    v: Tensor,
    is_causal: bool,
    prefix_lens: Tensor,
    causal_lens: Tensor,
    cu_seqlens: Tensor,
    total_seqlen: Tensor,
    numseqs: Tensor,
    max_seqlen_prefix: Tensor,
    max_seqlen_causal: Tensor,
    max_seqlen_all: Tensor,
    *,
    prefix_cu_seqlens: Optional[Tensor] = None,
    prefix_idx: Optional[Tensor] = None,
    causal_idx: Optional[Tensor] = None,
    active_key_idx: Optional[Tensor] = None,
    active_cu_seqlens_q: Optional[Tensor] = None,
    active_cu_seqlens_k: Optional[Tensor] = None,
    cu_seqlens_shifted: Optional[Tensor] = None,
    prefix_mask: Optional[Tensor] = None,
    causal_mask: Optional[Tensor] = None,
    impl: str = "gather",
) -> Tensor:
    if impl not in ("gather", "seqused"):
        raise ValueError(f"Unsupported FA4 PrefixLM implementation: {impl}")

    if impl == "seqused":
        if (
            cu_seqlens_shifted is None
            or prefix_mask is None
            or causal_mask is None
        ):
            fallback_routing = prefixlm_prepared_from_tensors(
                prefix_lens,
                causal_lens,
                cu_seqlens,
                total_seqlen,
                numseqs,
                max_seqlen_prefix,
                max_seqlen_causal,
                max_seqlen_all,
            )
            cu_seqlens_shifted = fallback_routing["cu_seqlens_shifted"]
            prefix_mask = fallback_routing["prefix_mask"]
            causal_mask = fallback_routing["causal_mask"]
        if prefix_mask.shape[0] > q.shape[0]:
            raise ValueError(
                f"PrefixLM metadata length {prefix_mask.shape[0]} exceeds Q length {q.shape[0]}"
            )
        if prefix_mask.shape[0] < q.shape[0]:
            padding = q.shape[0] - prefix_mask.shape[0]
            prefix_mask = torch.nn.functional.pad(prefix_mask, (0, padding), value=False)
            causal_mask = torch.nn.functional.pad(causal_mask, (0, padding), value=False)
        numseqs_int = int(numseqs.item())
        return _flash_attn_varlen_prefixlm_seqused(
            q,
            k,
            v,
            is_causal=is_causal,
            prefix_lens=prefix_lens[:numseqs_int],
            causal_lens=causal_lens[:numseqs_int],
            cu_seqlens=cu_seqlens[: numseqs_int + 1],
            cu_seqlens_shifted=cu_seqlens_shifted,
            prefix_mask=prefix_mask,
            causal_mask=causal_mask,
            max_seqlen_prefix=max_seqlen_prefix,
            max_seqlen_causal=max_seqlen_causal,
            max_seqlen_all=max_seqlen_all,
        )

    routing_values = (
        prefix_cu_seqlens,
        prefix_idx,
        causal_idx,
        active_key_idx,
        active_cu_seqlens_q,
        active_cu_seqlens_k,
    )
    if all(value is None for value in routing_values):
        routing = prefixlm_routing_from_tensors(
            prefix_lens,
            causal_lens,
            cu_seqlens,
            total_seqlen,
            numseqs,
            max_seqlen_prefix,
            max_seqlen_causal,
            max_seqlen_all,
        )
    elif any(value is None for value in routing_values):
        raise ValueError(f"PrefixLM routing tensors must provide all of {PREFIXLM_ROUTING_KEYS}")
    else:
        routing = dict(
            zip(PREFIXLM_ROUTING_KEYS, routing_values, strict=True)
        )  # type: ignore[arg-type]

    max_prefix = int(max_seqlen_prefix.item())

    out = torch.zeros_like(q)
    prefix_idx = routing["prefix_idx"]
    out_bidir = _fa4_varlen(
        q[prefix_idx],
        k[prefix_idx],
        v[prefix_idx],
        cu_seqlens_q=routing["prefix_cu_seqlens"],
        cu_seqlens_k=routing["prefix_cu_seqlens"],
        max_seqlen_q=max_prefix,
        max_seqlen_k=max_prefix,
        causal=is_causal,
    )
    out[prefix_idx] = out_bidir

    causal_idx = routing["causal_idx"]
    if causal_idx.numel() > 0:
        out_causal = _fa4_varlen(
            q[causal_idx],
            k[routing["active_key_idx"]],
            v[routing["active_key_idx"]],
            cu_seqlens_q=routing["active_cu_seqlens_q"],
            cu_seqlens_k=routing["active_cu_seqlens_k"],
            # FlashAttention accepts upper bounds here. Reuse the packed-batch
            # metadata instead of synchronizing two CUDA reductions to Python.
            max_seqlen_q=int(max_seqlen_causal.item()),
            max_seqlen_k=int(max_seqlen_all.item()),
            causal=True,
        )
        out[causal_idx] = out_causal

    return out
