#!/usr/bin/env python3
"""Small TorchRun/NCCL all-reduce preflight for multi-node launches."""

from __future__ import annotations

import os
import socket

import torch
import torch.distributed as dist


def main() -> None:
    local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local_rank)
    dist.init_process_group(backend="nccl")
    rank = dist.get_rank()
    world_size = dist.get_world_size()
    value = torch.tensor(float(rank + 1), device=f"cuda:{local_rank}")
    dist.all_reduce(value)
    expected = world_size * (world_size + 1) / 2
    if value.item() != expected:
        raise RuntimeError(
            f"NCCL all-reduce returned {value.item()}, expected {expected}"
        )
    dist.barrier()
    print(
        f"NCCL smoke passed host={socket.gethostname()} rank={rank}/{world_size} "
        f"local_rank={local_rank} sum={value.item():g}",
        flush=True,
    )
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
