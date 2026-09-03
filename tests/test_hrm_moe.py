from types import SimpleNamespace

import pytest
import torch
from torch import nn

from models.activation_checkpointing import apply_activation_checkpointing
from models.baselines.hrm_moe_nocarry_bp_warmup import (
    HierarchicalMoEModel,
    HierarchicalMoEOutput,
)
from models.layers import SwiGLU
from models.moe import (
    DroplessMoE,
    MoEAux,
    MoETransformerBlock,
    MoETransformerConfig,
    resolve_moe_layers,
)
from models.moe_lm_head import MoELMHead
from models.transformer import TransformerBlock


def _moe_config(**overrides) -> MoETransformerConfig:
    values = {
        "max_seq_len": 16,
        "n_layers": 2,
        "hidden_size": 8,
        "num_heads": 2,
        "expansion": 1.0,
        "attn_type": "causal",
        "init_type": "lecun_normal",
        "norm_type": "pre",
        "norm_eps": 1e-6,
        "pos_emb_type": "rope",
        "rope_theta": 10_000.0,
        "moe_layers": [1],
        "moe_num_experts": 2,
        "moe_top_k": 1,
        "moe_router_weighting": "selected_probability",
    }
    values.update(overrides)
    return MoETransformerConfig(**values)


def test_one_expert_matches_dense_swiglu_forward_and_backward() -> None:
    torch.manual_seed(1)
    config = _moe_config(moe_num_experts=1, moe_top_k=1)
    moe = DroplessMoE(config)
    dense = SwiGLU(
        hidden_size=config.hidden_size,
        intermediate_size=config.intermediate_size,
        init_std_in=config.init_config.in_std,
        init_std_out=config.init_config.ff_out_std,
    )
    moe.experts[0].load_state_dict(dense.state_dict())
    with torch.no_grad():
        moe.router.weight.zero_()

    dense_input = torch.randn(7, config.hidden_size, requires_grad=True)
    moe_input = dense_input.detach().clone().requires_grad_(True)
    dense_output = dense(dense_input)
    moe_output, aux = moe(moe_input)

    torch.testing.assert_close(moe_output, dense_output)
    assert aux.router_calls.item() == 1
    assert aux.valid_tokens.item() == 7
    assert aux.expert_token_counts.tolist() == [7.0]

    dense_output.square().sum().backward()
    moe_output.square().sum().backward()
    torch.testing.assert_close(moe_input.grad, dense_input.grad)
    for moe_parameter, dense_parameter in zip(
        moe.experts[0].parameters(), dense.parameters(), strict=True
    ):
        torch.testing.assert_close(moe_parameter.grad, dense_parameter.grad)


def test_padding_is_excluded_from_dispatch_and_statistics() -> None:
    torch.manual_seed(2)
    config = _moe_config(moe_num_experts=3, moe_top_k=2)
    moe = DroplessMoE(config)
    states = torch.randn(7, config.hidden_size)

    output, aux = moe(states, total_seqlen=torch.tensor(4))

    assert torch.count_nonzero(output[4:]).item() == 0
    assert aux.valid_tokens.item() == 4
    assert aux.expert_token_counts.sum().item() == 8
    assert aux.expert_probability_sums.sum().item() == pytest.approx(4.0)
    assert aux.balance_loss_sum.dtype == torch.float32
    assert aux.z_loss_sum.dtype == torch.float32


def test_selected_probability_top1_provides_task_gradient_to_router() -> None:
    torch.manual_seed(3)
    config = _moe_config(moe_num_experts=3, moe_top_k=1)
    moe = DroplessMoE(config)
    states = torch.randn(11, config.hidden_size)

    output, _ = moe(states)
    output.square().mean().backward()

    assert moe.router.weight.grad is not None
    assert torch.isfinite(moe.router.weight.grad).all()
    assert torch.count_nonzero(moe.router.weight.grad).item() > 0


def test_dispatch_accumulator_handles_bfloat16_autocast() -> None:
    torch.manual_seed(30)
    moe = DroplessMoE(_moe_config(moe_num_experts=3, moe_top_k=2))
    states = torch.randn(11, moe.hidden_size, dtype=torch.float32, requires_grad=True)

    with torch.autocast(device_type="cpu", dtype=torch.bfloat16):
        output, aux = moe(states)
        loss = output.square().mean() + 0.01 * aux.balance_loss_sum
    loss.backward()

    assert output.dtype == states.dtype
    assert torch.isfinite(output).all()
    assert states.grad is not None
    assert torch.isfinite(states.grad).all()


def test_reference_dispatch_runs_inside_compiled_caller() -> None:
    torch.manual_seed(31)
    moe = DroplessMoE(_moe_config())
    compiled = torch.compile(moe, backend="eager", dynamic=False)
    states = torch.randn(6, moe.hidden_size, requires_grad=True)

    output, aux = compiled(states, total_seqlen=torch.tensor(5))
    (output.square().mean() + 0.01 * aux.balance_loss_sum).backward()

    assert output.shape == states.shape
    assert aux.valid_tokens.item() == 5
    assert moe.router.weight.grad is not None


def test_hrm_routes_only_the_selected_l_exit_on_every_l_call() -> None:
    torch.manual_seed(4)
    config = {
        **_moe_config(n_layers=2).model_dump(),
        "half_layers": True,
        "H_cycles": 2,
        "L_cycles": 3,
        "bp_warmup_ratio": 0.2,
        "bp_min_steps": 2,
        "bp_max_steps": 5,
        "fwd_bwd_dtype": "float32",
        "H_override": {},
        "H_moe_layers": [],
        "L_moe_layers": [-1],
        "moe_num_experts": 2,
        "moe_top_k": 1,
    }
    model = HierarchicalMoEModel(config)
    cache = model.create_cache(
        max_batch_size=1,
        max_seq_len=16,
        dtype=torch.float32,
        device="cpu",
    )
    states = torch.randn(1, 2, config["hidden_size"])

    _, output = model(
        None,
        states,
        cache=cache,
        cache_lengths=torch.zeros(1, dtype=torch.long),
        position_ids=torch.arange(2).unsqueeze(0),
        bp_steps=5,
    )

    assert output.hidden_states.shape == states.shape
    assert output.aux.router_calls.item() == 6
    assert output.aux.valid_tokens.item() == 12
    assert output.aux.expert_token_counts.sum().item() == 12
    assert output.aux.call_expert_token_counts.shape == (6, 2)
    assert model.router_call_labels == [
        "L/call_0/layer_0",
        "L/call_1/layer_0",
        "L/call_2/layer_0",
        "L/call_3/layer_0",
        "L/call_4/layer_0",
        "L/call_5/layer_0",
    ]

    loss = (
        output.hidden_states.square().mean()
        + 0.01 * output.aux.balance_loss_sum / output.aux.router_calls
        + 0.001 * output.aux.z_loss_sum / output.aux.router_calls
    )
    loss.backward()
    router = model.L_level.core.layers[0].mlp.router
    assert router.weight.grad is not None
    assert torch.isfinite(router.weight.grad).all()


class _FakeMoEBackbone(nn.Module):
    def __init__(self, hidden_size: int, num_experts: int) -> None:
        super().__init__()
        self.head_hint = {
            "in": {"dim": hidden_size, "init_std": hidden_size**-0.5},
            "out": {"dim": hidden_size, "init_std": hidden_size**-0.5},
        }
        self.num_experts = num_experts
        self.router_call_labels = ["L/call_0/layer_0", "L/call_1/layer_0"]
        self.moe_balance_loss_weight = 0.1
        self.moe_z_loss_weight = 0.01
        self.aux_scale = nn.Parameter(torch.tensor(2.0))
        self.create_cache = lambda **kwargs: None
        self.compute_train_extra_args = lambda train_state: {}

    def forward(self, carry, x, **kwargs):
        scalar = self.aux_scale.square()
        aux = MoEAux(
            balance_loss_sum=2.0 * scalar,
            z_loss_sum=4.0 * scalar,
            router_calls=scalar.new_tensor(2.0),
            valid_tokens=scalar.new_tensor(float(x.shape[0])),
            expert_token_counts=scalar.new_tensor([2.0, 2.0]),
            expert_probability_sums=scalar.new_tensor([2.5, 1.5]),
            call_balance_losses=scalar.new_tensor([3.0, 5.0]),
            call_z_losses=scalar.new_tensor([7.0, 9.0]),
            call_is_differentiable=scalar.new_tensor([1.0, 1.0]),
            call_valid_tokens=scalar.new_tensor([2.0, 2.0]),
            call_expert_token_counts=scalar.new_tensor([[1.0, 1.0], [1.0, 1.0]]),
            call_expert_probability_sums=scalar.new_tensor(
                [[1.25, 0.75], [1.25, 0.75]]
            ),
        )
        return carry, HierarchicalMoEOutput(x, aux)


def test_moe_head_adds_auxiliary_objective_and_metrics() -> None:
    torch.manual_seed(5)
    backbone = _FakeMoEBackbone(hidden_size=8, num_experts=2)
    head = MoELMHead(
        backbone,
        {
            "vocab_size": 16,
            "goldfish_strategy": None,
        },
    )
    batch = {
        "inputs": torch.tensor([1, 2, 3, 4]),
        "labels": torch.tensor([2, 3, 4, 5]),
        "cu_seqlens": torch.tensor([0, 4], dtype=torch.int32),
    }

    _, objective, metrics = head(None, batch)
    objective.backward()

    assert backbone.aux_scale.grad is not None
    assert backbone.aux_scale.grad.item() != 0
    assert metrics["moe/router_calls"][0].item() == 2
    assert "moe/expert_0/load" in metrics
    assert "moe/expert_1/mean_probability" in metrics
    assert "moe/calls/L/call_0/layer_0/expert_0/load" in metrics
    ce_mean = metrics["loss"][0] / metrics["loss"][1]
    assert objective.detach().item() > ce_mean.item()


def test_layer_selection_supports_negative_indices_and_rejects_invalid() -> None:
    assert resolve_moe_layers([-1, 0], 4) == {0, 3}
    with pytest.raises(ValueError, match="outside a stack"):
        resolve_moe_layers([4], 4)


def test_bp_warmup_reaches_configured_endpoints() -> None:
    config = {
        **_moe_config(n_layers=2).model_dump(),
        "half_layers": True,
        "H_cycles": 2,
        "L_cycles": 3,
        "bp_warmup_ratio": 0.2,
        "bp_min_steps": 2,
        "bp_max_steps": 5,
        "fwd_bwd_dtype": "float32",
    }
    model = HierarchicalMoEModel(config)

    start = model.compute_train_extra_args(SimpleNamespace(step=0, total_steps=100))
    end = model.compute_train_extra_args(SimpleNamespace(step=20, total_steps=100))
    assert start == {"bp_steps": 2}
    assert end == {"bp_steps": 5}


class _ZeroAttention(nn.Module):
    def forward(self, hidden_states, **kwargs):
        return torch.zeros_like(hidden_states)


def test_moe_blocks_are_checkpoint_discoverable_and_backward_safe() -> None:
    torch.manual_seed(6)
    config = {
        **_moe_config(n_layers=2).model_dump(),
        "half_layers": True,
        "H_cycles": 2,
        "L_cycles": 3,
        "bp_warmup_ratio": 0.2,
        "bp_min_steps": 2,
        "bp_max_steps": 5,
        "fwd_bwd_dtype": "float32",
    }
    model = HierarchicalMoEModel(config)
    for module in model.modules():
        if isinstance(module, TransformerBlock):
            module.attn = _ZeroAttention()

    checkpointed = apply_activation_checkpointing(model, "full")
    assert len(checkpointed) == 2
    assert any(isinstance(module, MoETransformerBlock) for module in checkpointed)

    states = torch.randn(5, config["hidden_size"], requires_grad=True)
    _, output = model(
        None,
        states,
        position_ids=torch.arange(5),
        total_seqlen=torch.tensor(5),
        bp_steps=5,
    )
    loss = output.hidden_states.square().mean()
    loss.backward()

    assert states.grad is not None
    router = model.L_level.core.layers[0].mlp.router
    assert router.weight.grad is not None


def test_end_to_end_packed_training_objective_backward() -> None:
    torch.manual_seed(7)
    config = {
        **_moe_config(n_layers=2).model_dump(),
        "half_layers": True,
        "H_cycles": 2,
        "L_cycles": 3,
        "bp_warmup_ratio": 0.2,
        "bp_min_steps": 2,
        "bp_max_steps": 5,
        "fwd_bwd_dtype": "float32",
        "vocab_size": 32,
        "goldfish_strategy": None,
    }
    backbone = HierarchicalMoEModel(config)
    for module in backbone.modules():
        if isinstance(module, TransformerBlock):
            module.attn = _ZeroAttention()
    model = MoELMHead(backbone, config)
    compiled_model = torch.compile(model, backend="eager", dynamic=False)
    batch = {
        "inputs": torch.tensor([1, 2, 3, 4, 5]),
        "labels": torch.tensor([2, 3, 4, 5, -100]),
        "position_ids": torch.arange(5),
        "cu_seqlens": torch.tensor([0, 5], dtype=torch.int32),
        "total_seqlen": torch.tensor(5),
    }

    _, objective, metrics = compiled_model(None, batch, bp_steps=5)
    objective.backward()

    assert torch.isfinite(objective)
    assert metrics["moe/router_calls"][0].item() == 6
    assert model.embed_tokens.embedding_weight.grad is not None
    assert model.lm_head.weight.grad is not None
    router = backbone.L_level.core.layers[0].mlp.router
    assert router.weight.grad is not None
