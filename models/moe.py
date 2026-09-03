from typing import Literal, NamedTuple, Optional

import torch
import torch.nn.functional as F
from pydantic import Field, model_validator
from torch import Tensor, nn

from models.common import unwrap_tensor
from models.layers import Cache, LinearInit, RotaryEmbedding, SwiGLU
from models.transformer import TransformerBlock, TransformerConfig


RouterWeighting = Literal["selected_probability", "renormalized"]


class MoETransformerConfig(TransformerConfig):
    moe_layers: list[int] = Field(default_factory=list)
    moe_num_experts: int = Field(default=4, ge=1)
    moe_top_k: int = Field(default=1, ge=1)
    moe_router_weighting: RouterWeighting = "selected_probability"
    moe_router_init_std: Optional[float] = Field(default=None, gt=0.0)

    @model_validator(mode="after")
    def validate_moe(self) -> "MoETransformerConfig":
        if self.moe_top_k > self.moe_num_experts:
            raise ValueError("moe_top_k must not exceed moe_num_experts")
        return self


class MoEAux(NamedTuple):
    balance_loss_sum: Tensor
    z_loss_sum: Tensor
    router_calls: Tensor
    valid_tokens: Tensor
    expert_token_counts: Tensor
    expert_probability_sums: Tensor
    call_balance_losses: Tensor
    call_z_losses: Tensor
    call_is_differentiable: Tensor
    call_valid_tokens: Tensor
    call_expert_token_counts: Tensor
    call_expert_probability_sums: Tensor


class MoETransformerOutput(NamedTuple):
    hidden_states: Tensor
    aux: MoEAux


def empty_moe_aux(reference: Tensor, num_experts: int) -> MoEAux:
    scalar = reference.new_zeros((), dtype=torch.float32)
    vector = reference.new_zeros((num_experts,), dtype=torch.float32)
    empty_calls = reference.new_zeros((0,), dtype=torch.float32)
    empty_call_experts = reference.new_zeros((0, num_experts), dtype=torch.float32)
    return MoEAux(
        scalar,
        scalar,
        scalar,
        scalar,
        vector,
        vector,
        empty_calls,
        empty_calls,
        empty_calls,
        empty_calls,
        empty_call_experts,
        empty_call_experts,
    )


@torch.compiler.disable
def add_moe_aux(left: MoEAux, right: MoEAux) -> MoEAux:
    return MoEAux(
        balance_loss_sum=left.balance_loss_sum + right.balance_loss_sum,
        z_loss_sum=left.z_loss_sum + right.z_loss_sum,
        router_calls=left.router_calls + right.router_calls,
        valid_tokens=left.valid_tokens + right.valid_tokens,
        expert_token_counts=left.expert_token_counts + right.expert_token_counts,
        expert_probability_sums=(
            left.expert_probability_sums + right.expert_probability_sums
        ),
        call_balance_losses=torch.cat(
            (left.call_balance_losses, right.call_balance_losses)
        ),
        call_z_losses=torch.cat((left.call_z_losses, right.call_z_losses)),
        call_is_differentiable=torch.cat(
            (left.call_is_differentiable, right.call_is_differentiable)
        ),
        call_valid_tokens=torch.cat(
            (left.call_valid_tokens, right.call_valid_tokens)
        ),
        call_expert_token_counts=torch.cat(
            (left.call_expert_token_counts, right.call_expert_token_counts),
            dim=0,
        ),
        call_expert_probability_sums=torch.cat(
            (
                left.call_expert_probability_sums,
                right.call_expert_probability_sums,
            ),
            dim=0,
        ),
    )


class DroplessMoE(nn.Module):
    """Correctness-first token-choice MoE.

    Dispatch uses eager per-expert gathers in a compiler-disabled region and is
    intentionally not presented as an efficient sparse kernel. Only valid
    packed tokens participate in routing, the auxiliary losses, or expert load
    statistics.
    """

    def __init__(self, config: MoETransformerConfig) -> None:
        super().__init__()
        self.hidden_size = config.hidden_size
        self.num_experts = config.moe_num_experts
        self.top_k = config.moe_top_k
        self.router_weighting = config.moe_router_weighting

        router_init_std = config.moe_router_init_std
        if router_init_std is None:
            router_init_std = config.init_config.in_std
        self.router = LinearInit(
            config.hidden_size,
            config.moe_num_experts,
            bias=False,
            init_std=router_init_std,
        )
        self.experts = nn.ModuleList(
            [
                SwiGLU(
                    hidden_size=config.hidden_size,
                    intermediate_size=config.intermediate_size,
                    init_std_in=config.init_config.in_std,
                    init_std_out=config.init_config.ff_out_std,
                )
                for _ in range(config.moe_num_experts)
            ]
        )

    @staticmethod
    def _valid_mask(flat_states: Tensor, total_seqlen: object | None) -> Tensor:
        if total_seqlen is None:
            return torch.ones(flat_states.shape[0], dtype=torch.bool, device=flat_states.device)

        valid_count = unwrap_tensor(total_seqlen)  # type: ignore[arg-type]
        if not isinstance(valid_count, Tensor):
            valid_count = torch.tensor(valid_count, device=flat_states.device)
        else:
            valid_count = valid_count.to(device=flat_states.device)
        return torch.arange(flat_states.shape[0], device=flat_states.device) < valid_count

    @torch.compiler.disable
    def forward(self, x: Tensor, *, total_seqlen: object | None = None) -> tuple[Tensor, MoEAux]:
        original_shape = x.shape
        flat_states = x.reshape(-1, self.hidden_size)
        valid_mask = self._valid_mask(flat_states, total_seqlen)
        valid_indices = torch.nonzero(valid_mask, as_tuple=False).flatten()
        valid_states = flat_states.index_select(0, valid_indices)

        # Routing is explicitly evaluated in FP32 even under model autocast.
        router_logits = F.linear(
            valid_states.to(torch.float32),
            self.router.weight.to(torch.float32),
            self.router.bias.to(torch.float32) if self.router.bias is not None else None,
        )
        router_probabilities = torch.softmax(router_logits, dim=-1)
        top_probabilities, top_indices = torch.topk(router_probabilities, self.top_k, dim=-1)

        if self.router_weighting == "renormalized":
            top_weights = top_probabilities / top_probabilities.sum(dim=-1, keepdim=True).clamp_min(1e-9)
        else:
            top_weights = top_probabilities

        output_valid = torch.zeros_like(valid_states)
        for expert_index, expert in enumerate(self.experts):
            token_indices, route_slots = torch.nonzero(
                top_indices == expert_index,
                as_tuple=True,
            )
            expert_inputs = valid_states.index_select(0, token_indices)
            expert_outputs = expert(expert_inputs)
            # Autocast can produce BF16 expert outputs while the recurrent
            # residual stream (and therefore the dispatch accumulator) stays
            # FP32. index_add requires identical source/self dtypes, so cast
            # both factors to the accumulator dtype before combining routes.
            route_weights = top_weights[token_indices, route_slots].to(output_valid.dtype)
            weighted_outputs = expert_outputs.to(output_valid.dtype) * route_weights.unsqueeze(-1)
            output_valid = output_valid.index_add(
                0,
                token_indices,
                weighted_outputs,
            )

        flat_output = torch.zeros_like(flat_states).index_copy(0, valid_indices, output_valid)

        assignments = F.one_hot(top_indices, num_classes=self.num_experts).to(torch.float32)
        expert_token_counts = assignments.sum(dim=(0, 1))
        assignment_fraction = expert_token_counts / (valid_states.shape[0] * self.top_k)
        mean_router_probability = router_probabilities.mean(dim=0)
        balance_loss = self.num_experts * torch.sum(assignment_fraction * mean_router_probability)
        z_loss = torch.mean(torch.logsumexp(router_logits, dim=-1).square())

        one = router_logits.new_ones(())
        valid_tokens = router_logits.new_tensor(float(valid_states.shape[0]))
        aux = MoEAux(
            balance_loss_sum=balance_loss,
            z_loss_sum=z_loss,
            router_calls=one,
            valid_tokens=valid_tokens,
            expert_token_counts=expert_token_counts,
            expert_probability_sums=router_probabilities.sum(dim=0),
            call_balance_losses=balance_loss.unsqueeze(0),
            call_z_losses=z_loss.unsqueeze(0),
            call_is_differentiable=router_logits.new_tensor(
                [float(torch.is_grad_enabled())]
            ),
            call_valid_tokens=valid_tokens.unsqueeze(0),
            call_expert_token_counts=expert_token_counts.unsqueeze(0),
            call_expert_probability_sums=router_probabilities.sum(dim=0).unsqueeze(0),
        )
        return flat_output.reshape(original_shape), aux


class MoETransformerBlock(TransformerBlock):
    """Existing serial Transformer block with a dropless MoE feedforward."""

    def __init__(self, config: MoETransformerConfig) -> None:
        super().__init__(config)
        self.mlp = DroplessMoE(config)
        # TransformerBlock installs an instance-level forward for compile
        # friendliness, so refresh it after resolving these overridden methods.
        self.forward = getattr(self, f"_forward_{config.norm_type}")

    def _forward_pre(self, x: Tensor, **seq_info) -> tuple[Tensor, MoEAux]:
        x = x + self.attn(self.norm(x), **seq_info)
        update, aux = self.mlp(self.norm(x), total_seqlen=seq_info.get("total_seqlen"))
        return x + update, aux

    def _forward_post(self, x: Tensor, **seq_info) -> tuple[Tensor, MoEAux]:
        x = self.norm(x + self.attn(x, **seq_info))
        update, aux = self.mlp(x, total_seqlen=seq_info.get("total_seqlen"))
        return self.norm(x + update), aux


def resolve_moe_layers(layer_indices: list[int], n_layers: int) -> set[int]:
    resolved: set[int] = set()
    for layer_index in layer_indices:
        normalized = layer_index if layer_index >= 0 else n_layers + layer_index
        if not 0 <= normalized < n_layers:
            raise ValueError(
                f"MoE layer index {layer_index} is outside a stack with {n_layers} layers"
            )
        resolved.add(normalized)
    return resolved


class MoETransformer(nn.Module):
    """Transformer stack with MoE only at explicitly selected physical layers."""

    def __init__(self, config: MoETransformerConfig) -> None:
        super().__init__()
        self.num_experts = config.moe_num_experts
        self.moe_layer_indices = resolve_moe_layers(config.moe_layers, config.n_layers)
        self.head_hint = {
            "in": {"dim": config.hidden_size, "init_std": config.init_config.in_std},
            "out": {"dim": config.hidden_size, "init_std": config.init_config.in_std},
        }

        if config.pos_emb_type == "rope":
            assert config.rope_theta is not None
            self.rotary_emb = RotaryEmbedding(
                config.hidden_size // config.num_heads,
                config.max_seq_len,
                base=config.rope_theta,
            )

        self.layers = nn.ModuleList(
            [
                MoETransformerBlock(config)
                if layer_index in self.moe_layer_indices
                else TransformerBlock(config)
                for layer_index in range(config.n_layers)
            ]
        )

        self.norm_f = lambda x: x
        if config.norm_type == "pre":
            self.norm_f = lambda x: F.rms_norm(x, (x.shape[-1],), eps=config.norm_eps)

        self.create_cache = lambda **kwargs: [
            Cache.create(
                **kwargs,
                num_heads=config.num_heads,
                head_dim=config.hidden_size // config.num_heads,
            )
            for _ in range(config.n_layers)
        ]

    def forward(
        self,
        x: Tensor,
        cache: Optional[list[Cache]] = None,
        **seq_info,
    ) -> MoETransformerOutput:
        seq_info["cos_sin"] = (
            self.rotary_emb(seq_info.pop("position_ids", None))
            if hasattr(self, "rotary_emb")
            else None
        )
        aux = empty_moe_aux(x, self.num_experts)

        for layer_id, layer in enumerate(self.layers):
            layer_cache = cache[layer_id] if cache is not None else None
            if layer_id in self.moe_layer_indices:
                x, layer_aux = layer(x, **seq_info, cache=layer_cache)
                aux = add_moe_aux(aux, layer_aux)
            else:
                x = layer(x, **seq_info, cache=layer_cache)

        return MoETransformerOutput(self.norm_f(x), aux)
