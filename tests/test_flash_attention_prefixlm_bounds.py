from importlib import import_module

import pytest
import torch

from models.common import prepare_prefixlm_batch, wrap_tensor
from models.flash_attention_prefixlm_common import PREFIXLM_ROUTING_KEYS, prefixlm_routing_from_tensors


def packed_inputs() -> tuple[torch.Tensor, ...]:
    return (
        torch.tensor([3, 7, 0], dtype=torch.int32),
        torch.tensor([2, 0, 0], dtype=torch.int32),
        torch.tensor([0, 5, 12], dtype=torch.int32),
        torch.tensor(12),
        torch.tensor(2),
        torch.tensor(7),
        torch.tensor(2),
        torch.tensor(7),
    )


@pytest.mark.parametrize(
    ("module_name", "kernel_name"),
    [
        ("models.flash_attention_prefixlm_fa4", "_fa4_varlen"),
        ("models.flash_attention_prefixlm_rocm", "_rocm_varlen"),
    ],
)
def test_causal_launch_reuses_batch_sequence_bounds(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    kernel_name: str,
) -> None:
    module = import_module(module_name)
    launches: list[dict[str, object]] = []

    def fake_varlen(q: torch.Tensor, _k: torch.Tensor, _v: torch.Tensor, **kwargs: object) -> torch.Tensor:
        launches.append(kwargs)
        return torch.zeros_like(q)

    monkeypatch.setattr(module, kernel_name, fake_varlen)

    # The prefix-only sequence makes max_seqlen_all a conservative upper bound
    # for the active causal launch (7 versus an exact active maximum of 5).
    prefix_lens, causal_lens, cu_seqlens, *scalars = packed_inputs()
    q = torch.randn(12, 2, 8)

    output = module.flash_attn_varlen_prefixlm(
        q,
        q,
        q,
        False,
        prefix_lens,
        causal_lens,
        cu_seqlens,
        *scalars,
    )

    assert output.shape == q.shape
    assert len(launches) == 2
    assert launches[1]["max_seqlen_q"] == 2
    assert launches[1]["max_seqlen_k"] == 7


def test_prepare_prefixlm_batch_is_complete_and_idempotent() -> None:
    prefix_lens, causal_lens, cu_seqlens, *scalars = packed_inputs()
    scalar_names = (
        "total_seqlen",
        "numseqs",
        "max_seqlen_prefix",
        "max_seqlen_causal",
        "max_seqlen_all",
    )
    batch = {
        "prefix_lens": prefix_lens,
        "causal_lens": causal_lens,
        "cu_seqlens": cu_seqlens,
        **{name: wrap_tensor(value) for name, value in zip(scalar_names, scalars, strict=True)},
    }

    prepared = prepare_prefixlm_batch(batch)

    assert all(name in prepared for name in PREFIXLM_ROUTING_KEYS)
    assert prepare_prefixlm_batch(prepared) is prepared
    assert torch.equal(prepared["prefix_idx"], torch.tensor([0, 1, 2, 5, 6, 7, 8, 9, 10, 11]))
    assert torch.equal(prepared["causal_idx"], torch.tensor([3, 4]))
    assert torch.equal(prepared["active_key_idx"], torch.tensor([0, 1, 2, 3, 4]))


def test_prepare_prefixlm_batch_leaves_other_backends_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("models.accelerator.get_accelerator_type", lambda: "sm90")
    batch = {"inputs": torch.tensor([1])}

    assert prepare_prefixlm_batch(batch) is batch


@pytest.mark.parametrize(
    ("module_name", "kernel_name"),
    [
        ("models.flash_attention_prefixlm_fa4", "_fa4_varlen"),
        ("models.flash_attention_prefixlm_rocm", "_rocm_varlen"),
    ],
)
def test_precomputed_routing_matches_backend_fallback(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    kernel_name: str,
) -> None:
    module = import_module(module_name)
    launches: list[tuple[torch.Tensor, dict[str, object]]] = []

    def fake_varlen(q: torch.Tensor, _k: torch.Tensor, _v: torch.Tensor, **kwargs: object) -> torch.Tensor:
        launches.append((q.clone(), kwargs))
        return q.clone()

    monkeypatch.setattr(module, kernel_name, fake_varlen)
    packed = packed_inputs()
    q = torch.randn(12, 2, 8)

    fallback_output = module.flash_attn_varlen_prefixlm(q, q, q, False, *packed)
    fallback_launches = launches.copy()
    launches.clear()

    routing = prefixlm_routing_from_tensors(*packed)
    monkeypatch.setattr(
        module,
        "prefixlm_routing_from_tensors",
        lambda *_args, **_kwargs: pytest.fail("backend recomputed pre-supplied PrefixLM routing"),
    )
    prepared_output = module.flash_attn_varlen_prefixlm(q, q, q, False, *packed, **routing)

    assert torch.equal(prepared_output, fallback_output)
    assert len(launches) == len(fallback_launches)
    for (prepared_q, prepared_kwargs), (fallback_q, fallback_kwargs) in zip(
        launches, fallback_launches, strict=True
    ):
        assert torch.equal(prepared_q, fallback_q)
        assert prepared_kwargs.keys() == fallback_kwargs.keys()
        for name in prepared_kwargs:
            prepared_value = prepared_kwargs[name]
            fallback_value = fallback_kwargs[name]
            if isinstance(prepared_value, torch.Tensor):
                assert torch.equal(prepared_value, fallback_value)
            else:
                assert prepared_value == fallback_value
