#!/usr/bin/env python3
"""Safely rebuild a sampled dataset's shared source-token backing store."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import yaml
from tqdm import tqdm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokenized-path", type=Path, required=True)
    parser.add_argument("--sampled-path", type=Path, required=True)
    parser.add_argument("--prefix-config", type=Path, required=True)
    parser.add_argument("--chunk-mib", type=int, default=64)
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def target_dtype(tokenized_path: Path) -> np.dtype:
    info = json.loads((tokenized_path / "tokenizer_info.json").read_text())
    vocab_size = info.get("vocab_size")
    if vocab_size is not None and vocab_size <= np.iinfo(np.uint8).max:
        return np.dtype(np.uint8)
    if vocab_size is not None and vocab_size <= np.iinfo(np.uint16).max:
        return np.dtype(np.uint16)
    return np.dtype(np.int32)


def selected_tasks(tokenized_path: Path, prefix_config: Path) -> list[Path]:
    prefixes = tuple(item["prefix"] for item in yaml.safe_load(prefix_config.read_text()))
    return [
        task
        for task in sorted(tokenized_path.iterdir())
        if task.is_dir() and task.name.startswith(prefixes) and (task / "tokens.npy").is_file()
    ]


def array_header(path: Path) -> tuple[tuple[int, ...], np.dtype, int]:
    with path.open("rb") as handle:
        version = np.lib.format.read_magic(handle)
        reader = (
            np.lib.format.read_array_header_1_0
            if version[0] == 1
            else np.lib.format.read_array_header_2_0
        )
        shape, fortran_order, dtype = reader(handle)
        if fortran_order:
            raise ValueError(f"Fortran-order token arrays are unsupported: {path}")
        return shape, np.dtype(dtype), handle.tell()


def validate_epoch_offsets(sampled_path: Path, total_tokens: int) -> None:
    for epoch in sorted(sampled_path.glob("epoch_*")):
        max_end = 0
        for stem in ("inst", "resp"):
            starts = np.load(epoch / f"{stem}_start.npy", mmap_mode="r")
            lengths = np.load(epoch / f"{stem}_len.npy", mmap_mode="r")
            if starts.shape != lengths.shape:
                raise ValueError(f"Mismatched index shapes in {epoch}: {stem}")
            if starts.size:
                max_end = max(max_end, int(np.max(starts + lengths)))
        if max_end > total_tokens:
            raise ValueError(f"{epoch} references token {max_end:,}, beyond backing store {total_tokens:,}")


def main() -> None:
    args = parse_args()
    tasks = selected_tasks(args.tokenized_path, args.prefix_config)
    if not tasks:
        raise SystemExit("No tokenized tasks matched the prefix configuration")

    sources: list[tuple[Path, int, np.dtype, int]] = []
    total_tokens = 0
    for task in tqdm(tasks, desc="Validating sources"):
        source = task / "tokens.npy"
        shape, source_dtype, offset = array_header(source)
        if len(shape) != 1:
            raise ValueError(f"Expected one-dimensional token array: {source}")
        length = int(shape[0])
        expected_bytes = offset + length * source_dtype.itemsize
        if source.stat().st_size != expected_bytes:
            raise ValueError(
                f"Incomplete source token array: {source}; "
                f"expected {expected_bytes:,} bytes, found {source.stat().st_size:,}"
            )
        sources.append((source, length, source_dtype, offset))
        total_tokens += length

    current_path = args.sampled_path / "tokens.npy"
    if current_path.exists():
        current_shape, _, _ = array_header(current_path)
        if current_shape != (total_tokens,):
            raise ValueError(
                f"Existing declared shape {current_shape} does not match selected sources {(total_tokens,)}"
            )

    validate_epoch_offsets(args.sampled_path, total_tokens)
    dtype = target_dtype(args.tokenized_path)
    chunk_tokens = max(1, args.chunk_mib * 1024 * 1024 // dtype.itemsize)
    temp_path = args.sampled_path / ".tokens.npy.rebuild"
    if temp_path.exists():
        temp_path.unlink()

    print(
        json.dumps(
            {
                "tasks": len(tasks),
                "tokens": total_tokens,
                "dtype": str(dtype),
                "output_bytes": total_tokens * dtype.itemsize,
                "chunk_tokens": chunk_tokens,
                "temporary_path": str(temp_path),
            },
            indent=2,
        )
    )

    with temp_path.open("wb") as destination:
        np.lib.format.write_array_header_1_0(
            destination,
            {
                "descr": np.lib.format.dtype_to_descr(dtype),
                "fortran_order": False,
                "shape": (total_tokens,),
            },
        )
        with tqdm(total=total_tokens, desc="Rebuilding tokens", unit="tok", unit_scale=True) as progress:
            for source_path, length, source_dtype, offset in sources:
                with source_path.open("rb") as source:
                    source.seek(offset)
                    remaining = length
                    while remaining:
                        take = min(remaining, chunk_tokens)
                        payload = source.read(take * source_dtype.itemsize)
                        if len(payload) != take * source_dtype.itemsize:
                            raise EOFError(f"Short read from {source_path}")
                        if source_dtype == dtype:
                            destination.write(payload)
                        elif source_dtype.itemsize == dtype.itemsize and source_dtype.kind in "iu" and dtype.kind in "iu":
                            # Token IDs are non-negative; signedness does not change their byte representation.
                            destination.write(payload)
                        else:
                            converted = np.frombuffer(payload, dtype=source_dtype).astype(dtype)
                            destination.write(converted.tobytes())
                        remaining -= take
                        progress.update(take)
        destination.flush()
        os.fsync(destination.fileno())

    rebuilt = np.load(temp_path, mmap_mode="r")
    if rebuilt.shape != (total_tokens,) or rebuilt.dtype != dtype:
        raise RuntimeError(f"Rebuilt array validation failed: shape={rebuilt.shape}, dtype={rebuilt.dtype}")
    del rebuilt

    if not args.replace:
        print(f"Validated rebuilt store at {temp_path}; pass --replace to install it")
        return
    os.replace(temp_path, current_path)
    directory_fd = os.open(args.sampled_path, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    print(f"Installed complete backing store at {current_path}")


if __name__ == "__main__":
    main()
