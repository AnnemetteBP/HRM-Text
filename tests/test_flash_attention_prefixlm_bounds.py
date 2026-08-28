from importlib import import_module

import pytest
import torch


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
    prefix_lens = torch.tensor([3, 7, 0], dtype=torch.int32)
    causal_lens = torch.tensor([2, 0, 0], dtype=torch.int32)
    cu_seqlens = torch.tensor([0, 5, 12], dtype=torch.int32)
    q = torch.randn(12, 2, 8)

    output = module.flash_attn_varlen_prefixlm(
        q,
        q,
        q,
        False,
        prefix_lens,
        causal_lens,
        cu_seqlens,
        torch.tensor(12),
        torch.tensor(2),
        torch.tensor(7),
        torch.tensor(2),
        torch.tensor(7),
    )

    assert output.shape == q.shape
    assert len(launches) == 2
    assert launches[1]["max_seqlen_q"] == 2
    assert launches[1]["max_seqlen_k"] == 7
