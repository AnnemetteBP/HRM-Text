from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch import nn
from torch.distributed.device_mesh import init_device_mesh
from torch.distributed.fsdp import FSDPModule, fully_shard

from models.gradient_clipping import clip_grad_norm_mean_units


def _global_l2(grads: list[torch.Tensor]) -> float:
    local_sumsq = torch.zeros((), dtype=torch.float64)
    for grad in grads:
        local = grad.to_local() if hasattr(grad, "to_local") else grad
        local_sumsq += local.double().square().sum()
    dist.all_reduce(local_sumsq)
    return local_sumsq.sqrt().item()


def _run_fsdp_clip_check(rank: int, world_size: int, rendezvous: str) -> None:
    dist.init_process_group(
        "gloo",
        init_method=f"file://{rendezvous}",
        rank=rank,
        world_size=world_size,
    )
    try:
        mesh = init_device_mesh("cpu", (world_size,))
        model = nn.Linear(4, 4, bias=False)
        with torch.no_grad():
            model.weight.zero_()
        fully_shard(model, mesh=mesh, reshard_after_forward=False)
        assert isinstance(model, FSDPModule)
        model.set_gradient_divide_factor(1.0)
        model.set_force_sum_reduction_for_comms(True)

        # The summed gradient repeats [3, 6, 9, 12] across four rows.
        inputs = torch.tensor([[1.0, 2.0, 3.0, 4.0]]) * (rank + 1)
        model(inputs).sum().backward()
        grads = [parameter.grad for parameter in model.parameters() if parameter.grad is not None]
        raw_norm_before = _global_l2(grads)

        metrics = clip_grad_norm_mean_units(
            model.parameters(),
            max_norm=1.0,
            summed_gradient_scale=float(world_size),
        )
        raw_norm_after = _global_l2(grads)

        assert metrics.total_norm.item() == pytest.approx(raw_norm_before / world_size)
        assert metrics.clip_coefficient.item() == pytest.approx(
            world_size / raw_norm_before
        )
        assert metrics.clipped.item() == 1.0
        assert raw_norm_after / world_size == pytest.approx(1.0)
    finally:
        dist.destroy_process_group()


def test_fsdp2_clips_sum_reduced_dtensor_gradients_in_mean_units() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        rendezvous = str(Path(temp_dir) / "rdzv")
        mp.spawn(_run_fsdp_clip_check, args=(2, rendezvous), nprocs=2, join=True)
