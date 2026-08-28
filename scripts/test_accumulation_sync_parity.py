#!/usr/bin/env python3
"""Deterministic GAS parity test for the production accumulation function."""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch
import torch.distributed as dist
from torch import nn
from torch.nn.parallel import DistributedDataParallel

from models.adam_atan2 import AdamATan2
from pretrain import (
    PretrainConfig,
    TrainState,
    apply_fsdp,
    create_fsdp_mesh,
    train_accumulated_batches,
)


class ToyHead(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.proj = nn.Linear(5, 3, bias=True)

    def forward(self, *, batch, carry, **_kwargs):
        prediction = self.proj(batch["inputs"])
        error = prediction - batch["targets"]
        loss_sum = error.square().sum()
        divisor = torch.tensor(error.numel(), dtype=torch.float32, device=error.device)
        if dist.is_initialized():
            dist.all_reduce(divisor, op=dist.ReduceOp.AVG)
        metrics = {"loss": (loss_sum.detach(), divisor.detach())}
        return carry, loss_sum / divisor, metrics


def local_tensor(tensor: torch.Tensor) -> torch.Tensor:
    return tensor.to_local() if hasattr(tensor, "to_local") else tensor


def snapshot(state: TrainState) -> dict[str, list[torch.Tensor]]:
    result = {"parameters": [local_tensor(p).detach().cpu().clone() for p in state.model.parameters()]}
    for optim_state in state.optim.state.values():
        for key, value in optim_state.items():
            if torch.is_tensor(value):
                result.setdefault(f"optimizer/{key}", []).append(
                    local_tensor(value).detach().cpu().clone()
                )
    return result


def make_config(strategy: str, degree: int | None, sync_mode: str) -> PretrainConfig:
    return PretrainConfig.model_construct(
        distributed_strategy=strategy,
        fsdp_shard_degree=degree,
        fsdp_accumulation_sync_mode=sync_mode,
        resume_trace=False,
    )


def run_once(strategy: str, degree: int | None, sync_mode: str, gas: int, device: torch.device):
    torch.manual_seed(1234)
    model: nn.Module = ToyHead().to(device)
    if strategy == "ddp":
        model = DistributedDataParallel(model, device_ids=[device.index])
    else:
        config = make_config(strategy, degree, sync_mode)
        apply_fsdp(model, torch.float32, mesh=create_fsdp_mesh(config), reshard_after_forward=False)

    optimizer = AdamATan2(
        model.parameters(), lr=1e-2, betas=(0.9, 0.95), weight_decay=0.1, ema=0.9
    )
    state = TrainState(
        model=model,
        carry=None,
        optim=optimizer,
        step=1,
        total_steps=1,
        fwd_bwd_dtype=torch.float32,
        use_cuda_autocast=False,
    )

    generator = torch.Generator(device="cpu").manual_seed(9000 + dist.get_rank())
    inputs = torch.randn(8, 5, generator=generator).to(device)
    targets = torch.randn(8, 3, generator=generator).to(device)
    labels = torch.zeros(8, dtype=torch.long, device=device)
    batches = []
    for inputs_part, targets_part, labels_part in zip(
        inputs.chunk(gas), targets.chunk(gas), labels.chunk(gas)
    ):
        batches.append({"inputs": inputs_part, "targets": targets_part, "labels": labels_part})

    config = make_config(strategy, degree, sync_mode)
    train_accumulated_batches(config, dist.get_rank(), state, batches, use_compiled=False)
    return snapshot(state)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", choices=("ddp", "fsdp"), required=True)
    parser.add_argument("--shard-degree", type=int)
    parser.add_argument("--sync-mode", choices=("no_sync", "reduce_scatter"), default="no_sync")
    args = parser.parse_args()

    dist.init_process_group("nccl")
    local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local_rank)
    device = torch.device("cuda", local_rank)

    gas1 = run_once(args.strategy, args.shard_degree, args.sync_mode, 1, device)
    gas4 = run_once(args.strategy, args.shard_degree, args.sync_mode, 4, device)
    differences = {}
    for key in sorted(gas1):
        differences[key] = max(
            (left - right).abs().max().item() if left.numel() else 0.0
            for left, right in zip(gas1[key], gas4[key])
        )
    maximum = max(differences.values())
    if dist.get_rank() == 0:
        print(json.dumps({
            "strategy": args.strategy,
            "shard_degree": args.shard_degree,
            "sync_mode": args.sync_mode,
            "max_abs_difference": maximum,
            "differences": differences,
        }, sort_keys=True))
    if maximum > 2e-6:
        raise SystemExit(f"GAS parity failed: max abs difference {maximum}")
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
