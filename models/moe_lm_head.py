from typing import Tuple

import torch
import torch.distributed as dist
import torch.nn.functional as F
from torch import Tensor

from models.baselines.hrm_moe_nocarry_bp_warmup import HierarchicalMoEOutput
from models.common import IGNORE_LABEL_ID, packing_sequence_sum
from models.goldfish_loss import apply_goldfish_loss_mask
from models.layers import Carry
from models.lm_head import LMHead


class MoELMHead(LMHead):
    """LM head that adds functional MoE auxiliary losses to token CE."""

    def forward(
        self,
        carry: Carry,
        batch: dict[str, Tensor],
        **kwargs,
    ) -> Tuple[Carry, Tensor] | Tuple[Carry, Tensor, dict[str, Tuple[Tensor, Tensor]]]:
        input_embedding = self.embed_tokens(batch["inputs"])

        new_carry, model_output = self.model(
            carry,
            input_embedding,
            **{k: v for k, v in batch.items() if k not in ("inputs", "labels")},
            **kwargs,
        )
        if not isinstance(model_output, HierarchicalMoEOutput):
            raise TypeError(
                "MoELMHead requires HierarchicalMoEOutput from the backbone, "
                f"received {type(model_output).__name__}"
            )
        logits = self.lm_head(model_output.hidden_states)

        if "labels" not in batch:
            return new_carry, logits

        raw_labels = batch["labels"]
        labels, masks = apply_goldfish_loss_mask(
            labels=raw_labels,
            inputs=batch["inputs"],
            cu_seqlens=batch["cu_seqlens"],
            config=self.goldfish_config,
        )

        ce_sum = F.cross_entropy(
            logits.to(torch.float32),
            labels.to(torch.long),
            ignore_index=IGNORE_LABEL_ID,
            reduction="sum",
        )
        loss_divisor = masks.sum().to(torch.float32)
        if dist.is_available() and dist.is_initialized():
            dist.all_reduce(loss_divisor, op=dist.ReduceOp.AVG)

        router_calls = model_output.aux.router_calls.clamp_min(1.0)
        differentiable_mask = model_output.aux.call_is_differentiable
        differentiable_router_calls = differentiable_mask.sum().clamp_min(1.0)
        # HRM executes the same physical router at recurrent calls that may be
        # outside the truncated backward window. Averaging the objective over
        # all calls diluted its gradient during BP warmup. Only calls that can
        # actually contribute a gradient belong in the training objective.
        balance_loss = (
            model_output.aux.call_balance_losses * differentiable_mask
        ).sum() / differentiable_router_calls
        z_loss = (
            model_output.aux.call_z_losses * differentiable_mask
        ).sum() / differentiable_router_calls
        all_call_balance_loss = model_output.aux.balance_loss_sum / router_calls
        all_call_z_loss = model_output.aux.z_loss_sum / router_calls
        aux_loss = (
            self.model.moe_balance_loss_weight * balance_loss
            + self.model.moe_z_loss_weight * z_loss
        )
        objective = ce_sum / loss_divisor + aux_loss

        with torch.no_grad():
            is_correct = torch.argmax(logits, dim=-1) == labels
            raw_valid_counts = (raw_labels != IGNORE_LABEL_ID).sum()
            local_valid_counts = masks.sum()
            seq_num_tokens_correct = packing_sequence_sum(is_correct, batch["cu_seqlens"])
            seq_num_valid_tokens = packing_sequence_sum(masks, batch["cu_seqlens"])
            seq_is_valid = seq_num_valid_tokens > 0
            one = objective.new_ones(())

            metrics: dict[str, Tuple[Tensor, Tensor]] = {
                "loss": (ce_sum.detach(), local_valid_counts),
                "accuracy": (is_correct.sum(), local_valid_counts),
                "exact_accuracy": (
                    ((seq_num_tokens_correct == seq_num_valid_tokens) & seq_is_valid).sum(),
                    seq_is_valid.sum(),
                ),
                "objective": (objective.detach(), one),
                "moe/balance_loss": (balance_loss.detach(), one),
                "moe/z_loss": (z_loss.detach(), one),
                "moe/all_call_balance_loss": (all_call_balance_loss.detach(), one),
                "moe/all_call_z_loss": (all_call_z_loss.detach(), one),
                "moe/aux_loss": (aux_loss.detach(), one),
                "moe/router_calls": (model_output.aux.router_calls.detach(), one),
                "moe/differentiable_router_calls": (
                    differentiable_mask.sum().detach(),
                    one,
                ),
            }

            total_assignments = model_output.aux.expert_token_counts.sum().clamp_min(1.0)
            total_valid_tokens = model_output.aux.valid_tokens.clamp_min(1.0)
            aggregate_loads = model_output.aux.expert_token_counts / total_assignments
            metrics["moe/max_load"] = (aggregate_loads.max().detach(), one)
            metrics["moe/min_load"] = (aggregate_loads.min().detach(), one)
            metrics["moe/max_violation"] = (
                (
                    aggregate_loads.max()
                    * model_output.aux.expert_token_counts.shape[0]
                    - 1.0
                ).detach(),
                one,
            )
            for expert_index in range(model_output.aux.expert_token_counts.shape[0]):
                metrics[f"moe/expert_{expert_index}/load"] = (
                    model_output.aux.expert_token_counts[expert_index].detach(),
                    total_assignments,
                )
                metrics[f"moe/expert_{expert_index}/mean_probability"] = (
                    model_output.aux.expert_probability_sums[expert_index].detach(),
                    total_valid_tokens,
                )

            call_labels = self.model.router_call_labels
            if model_output.aux.call_balance_losses.shape[0] != len(call_labels):
                raise RuntimeError(
                    "Router trace length does not match the static H/L call map: "
                    f"{model_output.aux.call_balance_losses.shape[0]} != {len(call_labels)}"
                )
            for call_index, call_label in enumerate(call_labels):
                prefix = f"moe/calls/{call_label}"
                metrics[f"{prefix}/balance_loss"] = (
                    model_output.aux.call_balance_losses[call_index].detach(),
                    one,
                )
                metrics[f"{prefix}/z_loss"] = (
                    model_output.aux.call_z_losses[call_index].detach(),
                    one,
                )
                metrics[f"{prefix}/differentiable"] = (
                    model_output.aux.call_is_differentiable[call_index].detach(),
                    one,
                )
                call_assignments = model_output.aux.call_expert_token_counts[
                    call_index
                ].sum().clamp_min(1.0)
                call_valid_tokens = model_output.aux.call_valid_tokens[
                    call_index
                ].clamp_min(1.0)
                for expert_index in range(
                    model_output.aux.call_expert_token_counts.shape[1]
                ):
                    metrics[f"{prefix}/expert_{expert_index}/load"] = (
                        model_output.aux.call_expert_token_counts[
                            call_index, expert_index
                        ].detach(),
                        call_assignments,
                    )
                    metrics[f"{prefix}/expert_{expert_index}/mean_probability"] = (
                        model_output.aux.call_expert_probability_sums[
                            call_index, expert_index
                        ].detach(),
                        call_valid_tokens,
                    )

            if self.goldfish_config.enabled():
                dropped = raw_valid_counts - local_valid_counts
                metrics["goldfish_drop_rate"] = (dropped, raw_valid_counts)

        return new_carry, objective, metrics

    @torch.no_grad()
    def update_moe_router_bias(
        self,
        metrics: dict[str, tuple[Tensor, Tensor]],
    ) -> None:
        self.model.update_moe_router_bias(metrics)
