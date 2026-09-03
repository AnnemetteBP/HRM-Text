from typing import Any, Dict, NamedTuple, Optional, Tuple

import torch
from pydantic import Field
from torch import Tensor, nn

from models.common import trunc_normal_init_
from models.moe import (
    MoEAux,
    MoETransformer,
    MoETransformerConfig,
    MoETransformerOutput,
    add_moe_aux,
    empty_moe_aux,
)
from models.transformer import Cache


class HierarchicalMoEModelConfig(MoETransformerConfig):
    half_layers: bool = False

    H_cycles: int = Field(ge=1)
    L_cycles: int = Field(ge=1)

    bp_warmup_ratio: float = Field(default=0.0, ge=0.0)
    bp_min_steps: int = Field(default=2, ge=2)
    bp_max_steps: int = Field(default=5, ge=2)
    fwd_bwd_dtype: str = "bfloat16"

    H_override: Dict[str, Any] = Field(default_factory=dict)
    H_moe_layers: list[int] = Field(default_factory=list)
    L_moe_layers: list[int] = Field(default_factory=lambda: [-1])
    moe_balance_loss_weight: float = Field(default=0.01, ge=0.0)
    moe_z_loss_weight: float = Field(default=0.001, ge=0.0)


class HierarchicalMoEOutput(NamedTuple):
    hidden_states: Tensor
    aux: MoEAux


class HierarchicalMoERecurrentBlock(nn.Module):
    def __init__(self, config: MoETransformerConfig) -> None:
        super().__init__()
        self.core = MoETransformer(config)
        self.create_cache = self.core.create_cache

    def forward(
        self,
        hidden_states: Tensor,
        input_injection: Tensor,
        **kwargs,
    ) -> MoETransformerOutput:
        return self.core(hidden_states + input_injection, **kwargs)


class HierarchicalMoEModel(nn.Module):
    """Two-state HRM with MoE at selected physical H/L feedforwards."""

    def __init__(self, config_dict: dict) -> None:
        super().__init__()
        config = HierarchicalMoEModelConfig(**config_dict)
        if config.bp_max_steps < config.bp_min_steps:
            raise ValueError("bp_max_steps must be greater than or equal to bp_min_steps")
        max_recurrent_steps = config.H_cycles + config.H_cycles * config.L_cycles
        if config.bp_max_steps > max_recurrent_steps:
            raise ValueError("bp_max_steps cannot exceed the total number of H/L calls")

        if config.half_layers:
            if config.n_layers % 2 != 0:
                raise ValueError("n_layers must be divisible by 2 when half_layers is enabled")
            config.n_layers //= 2

        base_config = config.model_dump()
        h_config = MoETransformerConfig(
            **(base_config | config.H_override | {"moe_layers": config.H_moe_layers})
        )
        l_config = MoETransformerConfig(
            **(base_config | {"moe_layers": config.L_moe_layers})
        )

        self.H_level = HierarchicalMoERecurrentBlock(h_config)
        self.L_level = HierarchicalMoERecurrentBlock(l_config)

        self.H_cycles = config.H_cycles
        self.L_cycles = config.L_cycles
        self.bp_warmup_ratio = config.bp_warmup_ratio
        self.bp_min_steps = config.bp_min_steps
        self.bp_max_steps = config.bp_max_steps
        self.num_experts = config.moe_num_experts
        self.moe_balance_loss_weight = config.moe_balance_loss_weight
        self.moe_z_loss_weight = config.moe_z_loss_weight

        self.hidden_size = config.hidden_size
        self.head_hint = self.H_level.core.head_hint
        self.router_call_labels = []
        for h_cycle in range(self.H_cycles):
            for l_cycle in range(
                h_cycle * self.L_cycles,
                (h_cycle + 1) * self.L_cycles,
            ):
                for layer_index in sorted(self.L_level.core.moe_layer_indices):
                    self.router_call_labels.append(
                        f"L/call_{l_cycle}/layer_{layer_index}"
                    )
            for layer_index in sorted(self.H_level.core.moe_layer_indices):
                self.router_call_labels.append(
                    f"H/call_{h_cycle}/layer_{layer_index}"
                )
        self.zL_init = nn.Buffer(
            trunc_normal_init_(
                torch.empty(
                    config.hidden_size,
                    dtype=getattr(torch, config.fwd_bwd_dtype),
                ),
                std=1.0,
            ),
            persistent=True,
        )

        self.create_cache = lambda **kwargs: {
            "H": [self.H_level.create_cache(**kwargs) for _ in range(self.H_cycles)],
            "L": [
                self.L_level.create_cache(**kwargs)
                for _ in range(self.H_cycles * self.L_cycles)
            ],
        }

    def forward(
        self,
        carry: None,
        x: Tensor,
        cache: Optional[dict[str, list[list[Cache]]]] = None,
        bp_steps: int = 2,
        **seq_info,
    ) -> Tuple[None, HierarchicalMoEOutput]:
        if not self.bp_min_steps <= bp_steps <= self.bp_max_steps:
            raise ValueError(
                f"bp_steps={bp_steps} must be within "
                f"[{self.bp_min_steps}, {self.bp_max_steps}]"
            )

        z_H, z_L = x, self.zL_init
        aux = empty_moe_aux(x, self.num_experts)

        H_bp_steps = min(self.H_cycles, bp_steps - 1)
        L_bp_steps = bp_steps - H_bp_steps

        for h_cycle in range(self.H_cycles):
            for l_cycle in range(
                h_cycle * self.L_cycles,
                (h_cycle + 1) * self.L_cycles,
            ):
                with torch.set_grad_enabled(
                    torch.is_grad_enabled()
                    and l_cycle >= self.H_cycles * self.L_cycles - L_bp_steps
                ):
                    l_output = self.L_level(
                        z_L,
                        z_H,
                        **seq_info,
                        cache=cache["L"][l_cycle] if cache is not None else None,
                    )
                    z_L = l_output.hidden_states
                    aux = add_moe_aux(aux, l_output.aux)

            with torch.set_grad_enabled(
                torch.is_grad_enabled() and h_cycle >= self.H_cycles - H_bp_steps
            ):
                h_output = self.H_level(
                    z_H,
                    z_L,
                    **seq_info,
                    cache=cache["H"][h_cycle] if cache is not None else None,
                )
                z_H = h_output.hidden_states
                aux = add_moe_aux(aux, h_output.aux)

        return None, HierarchicalMoEOutput(z_H, aux)

    def compute_train_extra_args(self, train_state: Any) -> dict[str, Any]:
        if self.bp_warmup_ratio == 0:
            return {"bp_steps": self.bp_max_steps}
        progress = min(
            1.0,
            train_state.step / (train_state.total_steps * self.bp_warmup_ratio),
        )
        return {
            "bp_steps": self.bp_min_steps
            + int(progress * (self.bp_max_steps - self.bp_min_steps))
        }

    def initial_carry(self, batch_size: int, dtype: torch.dtype) -> None:
        return None
