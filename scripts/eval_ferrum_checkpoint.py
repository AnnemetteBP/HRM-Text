#!/usr/bin/env python3
"""Evaluate a Ferrum HRM strategy checkpoint on a packed split."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch
import torch.distributed as dist
import torch.distributed.checkpoint as dcp
import yaml
from tokenizers import Tokenizer

from dataset_new import V1DatasetMeta
from models.accelerator import set_accelerator_type, torch_device_for_accelerator
from models.adam_atan2 import AdamATan2
from models.common import IGNORE_LABEL_ID, wrap_tensor
from pretrain import (
    PretrainConfig,
    TrainState,
    compute_train_extra_args,
    create_dataloader,
    create_model_and_carry,
    initial_model_carry,
    move_batch_to_device,
    sharded_checkpoint_id,
    unsharded_checkpoint_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--tag", default="epoch_10")
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-batches", type=int)
    return parser.parse_args()


def load_config(checkpoint: Path, data_path: str, tag: str) -> PretrainConfig:
    config_path = checkpoint / "all_config.yaml"
    if not config_path.is_file():
        raise SystemExit(f"missing checkpoint config: {config_path}")
    raw = yaml.safe_load(config_path.read_text())
    raw["data"]["path"] = data_path
    raw["data"]["validation_path"] = None
    raw["epochs"] = 1
    raw["checkpoint_path"] = None
    raw["resume_checkpoint_path"] = str(checkpoint)
    raw["resume_checkpoint_tag"] = tag
    raw["wandb_run_id"] = None
    raw["wandb_resume"] = None
    raw["project_name"] = None
    raw["run_name"] = None
    raw["compile_train_batch"] = False
    return PretrainConfig(**raw)


def decode_ids(tokenizer: Tokenizer, ids: list[int], eos_id: int | None) -> str:
    if eos_id is not None and eos_id in ids:
        ids = ids[: ids.index(eos_id)]
    return tokenizer.decode(ids, skip_special_tokens=True).strip()


def processor_family(label: str) -> str:
    label = label.strip()
    if not label:
        return ""
    head = label.split("(", 1)[0].strip()
    return head or label


def reduce_sums(values: dict[str, float], device: torch.device) -> dict[str, float]:
    keys = sorted(values)
    tensor = torch.tensor([values[k] for k in keys], dtype=torch.float64, device=device)
    if dist.is_available() and dist.is_initialized():
        dist.reduce(tensor, dst=0, op=dist.ReduceOp.SUM)
    return {k: float(v) for k, v in zip(keys, tensor.cpu().tolist())}


def load_eval_model(config: PretrainConfig, train_state: TrainState, tag: str, rank: int) -> None:
    if config.resume_checkpoint_path is None:
        raise ValueError("resume_checkpoint_path must be set")

    if config.checkpoint_format == "sharded":
        checkpoint_id = sharded_checkpoint_id(config.resume_checkpoint_path, tag)
        if not Path(checkpoint_id).is_dir():
            raise ValueError(f"Checkpoint directory not found: {checkpoint_id}")
        model_state = train_state.model.state_dict()
        dcp.load({"model": model_state}, checkpoint_id=checkpoint_id)
        train_state.model.load_state_dict(model_state)
        return

    if config.checkpoint_format == "unsharded":
        checkpoint_path = unsharded_checkpoint_path(config.resume_checkpoint_path, tag)
        if not Path(checkpoint_path).is_file():
            raise ValueError(f"Checkpoint file not found: {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False) if rank == 0 else {}
        if dist.is_available() and dist.is_initialized():
            keys = [checkpoint] if rank == 0 else [None]
            dist.broadcast_object_list(keys, src=0)
            checkpoint = keys[0]
        train_state.model.load_state_dict(checkpoint["model"])
        return

    raise ValueError(f"Unsupported checkpoint_format: {config.checkpoint_format}")


def restore_eval_step(checkpoint: Path, tag: str, train_state: TrainState, config: PretrainConfig) -> None:
    state_path = checkpoint / f"checkpoint_state_{tag}.json"
    if state_path.is_file():
        state = json.loads(state_path.read_text())
        train_state.step = int(state.get("step", train_state.step))

    metadata_path = checkpoint / "train_metadata.yaml"
    if metadata_path.is_file():
        metadata = yaml.safe_load(metadata_path.read_text()) or {}
        total_length = int(metadata.get("total_length", 0) or 0)
        if total_length > 0:
            train_state.total_steps = max(1, int(config.epochs * (total_length // config.global_batch_size)))


@torch.inference_mode()
def main() -> int:
    args = parse_args()

    world_size = 1
    rank = 0
    local_rank = 0
    if "LOCAL_RANK" in os.environ:
        dist.init_process_group(backend="nccl")
        world_size = dist.get_world_size()
        rank = dist.get_rank()
        local_rank = int(os.environ["LOCAL_RANK"])
        torch.cuda.set_device(local_rank)

    config = load_config(args.checkpoint, args.data, args.tag)
    set_accelerator_type(config.accelerator_type)
    device = torch_device_for_accelerator(config.accelerator_type, local_rank=local_rank)
    fwd_bwd_dtype = getattr(torch, config.fwd_bwd_dtype)
    local_batch_size = config.global_batch_size // (world_size * config.gradient_accumulation_steps)

    loader, metadata = create_dataloader(
        config,
        local_batch_size,
        drop_last_batch=False,
        rank=rank,
        world_size=world_size,
        dataset_path=args.data,
    )
    model, carry, optim = create_model_and_carry(config, metadata, local_batch_size, device)
    train_state = TrainState(
        model=model,
        carry=carry,
        optim=optim,
        step=0,
        total_steps=1,
        fwd_bwd_dtype=fwd_bwd_dtype,
        use_cuda_autocast=(
            config.distributed_strategy == "ddp"
            and device.type == "cuda"
            and fwd_bwd_dtype != torch.float32
        ),
    )
    load_eval_model(config, train_state, args.tag, rank)
    restore_eval_step(args.checkpoint, args.tag, train_state, config)
    train_state.model.eval()

    tokenizer_info = metadata.tokenizer_info
    tokenizer_path = Path(tokenizer_info["tokenizer_path"])
    tokenizer_file = tokenizer_path / "tokenizer.json" if tokenizer_path.is_dir() else tokenizer_path
    tokenizer = Tokenizer.from_file(str(tokenizer_file))
    eos_id = tokenizer.token_to_id(tokenizer_info.get("eos", "[EOS]"))

    sums: dict[str, float] = {
        "token_correct": 0.0,
        "token_total": 0.0,
        "seq_exact": 0.0,
        "seq_total": 0.0,
        "processor_correct": 0.0,
        "processor_total": 0.0,
        "loss_sum": 0.0,
        "loss_tokens": 0.0,
        "batches": 0.0,
    }

    with torch.device(device):
        train_state.carry = initial_model_carry(train_state.model, local_batch_size, dtype=fwd_bwd_dtype)

    for batch_idx, (batch, batch_info) in enumerate(loader, start=1):
        if args.max_batches is not None and batch_idx > args.max_batches:
            break
        batch = move_batch_to_device(batch, device)
        batch_info.pop("resume_info", None)
        batch = batch | {k: wrap_tensor(torch.tensor(v, device="cpu")) for k, v in batch_info.items()}

        labels = batch["labels"].to(torch.long)
        labels_for_loss = labels.clone()
        valid = labels != IGNORE_LABEL_ID
        model_batch = {k: v for k, v in batch.items() if k != "labels"}
        device_type = batch["inputs"].device.type
        use_autocast = (
            (device_type in ("mps", "cpu") and train_state.fwd_bwd_dtype != torch.float32)
            or (device_type == "cuda" and train_state.use_cuda_autocast)
        )
        extra_args = compute_train_extra_args(train_state.model, train_state)
        with torch.autocast(device_type=device_type, dtype=train_state.fwd_bwd_dtype, enabled=use_autocast, cache_enabled=False):
            train_state.carry, logits = train_state.model(batch=model_batch, carry=train_state.carry, **extra_args)
        pred = torch.argmax(logits, dim=-1)

        token_total = valid.sum()
        token_correct = ((pred == labels) & valid).sum()
        loss = torch.nn.functional.cross_entropy(
            logits.to(torch.float32),
            labels_for_loss,
            ignore_index=IGNORE_LABEL_ID,
            reduction="sum",
        )

        cu = batch["cu_seqlens"].to(torch.long).detach().cpu().tolist()
        pred_cpu = pred.detach().cpu()
        labels_cpu = labels.detach().cpu()
        valid_cpu = valid.detach().cpu()
        seq_exact = 0
        seq_total = 0
        processor_correct = 0
        processor_total = 0
        for start, end in zip(cu, cu[1:]):
            span_valid = valid_cpu[start:end]
            if not bool(span_valid.any()):
                continue
            seq_total += 1
            if bool(((pred_cpu[start:end] == labels_cpu[start:end]) | ~span_valid).all()):
                seq_exact += 1
            gold_ids = labels_cpu[start:end][span_valid].tolist()
            pred_ids = pred_cpu[start:end][span_valid].tolist()
            gold = decode_ids(tokenizer, [int(x) for x in gold_ids], eos_id)
            guess = decode_ids(tokenizer, [int(x) for x in pred_ids], eos_id)
            processor_total += 1
            if processor_family(guess) == processor_family(gold):
                processor_correct += 1

        sums["token_correct"] += float(token_correct.item())
        sums["token_total"] += float(token_total.item())
        sums["seq_exact"] += float(seq_exact)
        sums["seq_total"] += float(seq_total)
        sums["processor_correct"] += float(processor_correct)
        sums["processor_total"] += float(processor_total)
        sums["loss_sum"] += float(loss.item())
        sums["loss_tokens"] += float(token_total.item())
        sums["batches"] += 1.0

        if rank == 0 and batch_idx % 10 == 0:
            print(json.dumps({"checkpoint": str(args.checkpoint), "tag": args.tag, "batch": batch_idx}), flush=True)

    reduced = reduce_sums(sums, device)
    if rank == 0:
        result: dict[str, Any] = {
            "checkpoint": str(args.checkpoint),
            "tag": args.tag,
            "data": args.data,
            "accuracy": reduced["token_correct"] / reduced["token_total"] if reduced["token_total"] else None,
            "exact_accuracy": reduced["seq_exact"] / reduced["seq_total"] if reduced["seq_total"] else None,
            "correct_processor": reduced["processor_correct"] / reduced["processor_total"] if reduced["processor_total"] else None,
            "loss": reduced["loss_sum"] / reduced["loss_tokens"] if reduced["loss_tokens"] else None,
            "counts": reduced,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True), flush=True)

    if dist.is_available() and dist.is_initialized():
        dist.barrier()
        dist.destroy_process_group()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
