#!/usr/bin/env python3
"""Evaluate exported Ferrum HF checkpoints on HRM direct JSONL rows."""

from __future__ import annotations

import argparse
import collections
import gzip
import json
import re
from pathlib import Path
from typing import Iterator

import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

IGNORE_LABEL_ID = -100


def open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open("r", encoding="utf-8")


def iter_rows(path: Path) -> Iterator[dict[str, str]]:
    with open_text(path) as source:
        for line in source:
            row = json.loads(line)
            if isinstance(row.get("instruction"), str) and isinstance(row.get("response"), str):
                yield row


def processor_family(label: str) -> str:
    label = label.strip()
    if not label:
        return ""
    return label.split("(", 1)[0].strip() or label


STATUS_SECTIONS = (
    "solved",
    "transformed_strong",
    "transformed_weak",
    "failed",
    "timeout",
)

STATUS_HEADER_RE = re.compile(r"\b(solved|transformed_strong|transformed_weak|failed|timeout)\s*:")
ATOM_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]*(?:\s*\([^)]*\))?")


def normalize_atom(atom: str) -> str:
    atom = re.sub(r"\s+", " ", atom.strip())
    atom = re.sub(r"\s*([(),=])\s*", r"\1", atom)
    atom = re.sub(r"=\s*-\s*", "=-", atom)
    return atom


def parse_status_map(text: str) -> dict[str, set[str]]:
    sections: dict[str, set[str]] = {section: set() for section in STATUS_SECTIONS}
    matches = list(STATUS_HEADER_RE.finditer(text))
    if not matches:
        return sections
    for idx, match in enumerate(matches):
        section = match.group(1)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end]
        for atom_match in ATOM_RE.finditer(body):
            atom = normalize_atom(atom_match.group(0))
            if atom and atom not in STATUS_SECTIONS:
                sections[section].add(atom)
    return sections


def update_status_map_metrics(metrics: dict[str, float], guess_text: str, gold_text: str) -> None:
    guess = parse_status_map(guess_text)
    gold = parse_status_map(gold_text)
    all_equal = True
    for section in STATUS_SECTIONS:
        g = guess[section]
        y = gold[section]
        tp = len(g & y)
        fp = len(g - y)
        fn = len(y - g)
        metrics[f"status/{section}/tp"] += tp
        metrics[f"status/{section}/fp"] += fp
        metrics[f"status/{section}/fn"] += fn
        metrics[f"status/{section}/gold"] += len(y)
        metrics[f"status/{section}/pred"] += len(g)
        if g == y:
            metrics[f"status/{section}/exact"] += 1
        else:
            all_equal = False
    metrics["status/rows"] += 1
    if all_equal:
        metrics["status/exact"] += 1


def decode_label(tokenizer, ids: list[int], eos_id: int | None) -> str:
    if eos_id is not None and eos_id in ids:
        ids = ids[: ids.index(eos_id)]
    return tokenizer.decode(ids, skip_special_tokens=True).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--dtype", default="bfloat16")
    parser.add_argument("--attn-implementation", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dtype = getattr(torch, args.dtype)
    config = AutoConfig.from_pretrained(args.model)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model_kwargs = {"torch_dtype": dtype}
    if args.attn_implementation:
        model_kwargs["attn_implementation"] = args.attn_implementation
    model = AutoModelForCausalLM.from_pretrained(args.model, **model_kwargs).to(args.device).eval()

    bos_id = tokenizer.convert_tokens_to_ids("[BOS]")
    sep_id = tokenizer.convert_tokens_to_ids("[SEP]")
    eos_id = tokenizer.convert_tokens_to_ids("[EOS]")
    unk_id = tokenizer.convert_tokens_to_ids("[UNK]")
    if None in (bos_id, sep_id, eos_id, unk_id):
        raise SystemExit("export tokenizer must define [BOS], [SEP], [EOS], and [UNK]")

    max_len = int(getattr(config, "max_position_embeddings", 0) or 0)
    rows_seen = rows_kept = skipped_too_long = skipped_unk = 0
    token_correct = token_total = 0
    seq_exact = seq_total = 0
    processor_correct = processor_total = 0
    loss_sum = 0.0
    status_metrics: dict[str, float] = collections.defaultdict(float)

    batch: list[tuple[list[int], list[int], list[int], str]] = []

    def flush() -> None:
        nonlocal token_correct, token_total, seq_exact, seq_total
        nonlocal processor_correct, processor_total, loss_sum, batch
        if not batch:
            return
        pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
        batch_max = max(len(inputs) for inputs, _, _, _ in batch)
        input_ids = torch.full((len(batch), batch_max), pad_id, dtype=torch.long)
        labels = torch.full((len(batch), batch_max), IGNORE_LABEL_ID, dtype=torch.long)
        attention_mask = torch.zeros((len(batch), batch_max), dtype=torch.long)
        token_type_ids = torch.zeros((len(batch), batch_max), dtype=torch.long)
        for row_idx, (inputs, row_labels, row_token_type_ids, _) in enumerate(batch):
            input_ids[row_idx, : len(inputs)] = torch.tensor(inputs, dtype=torch.long)
            labels[row_idx, : len(row_labels)] = torch.tensor(row_labels, dtype=torch.long)
            token_type_ids[row_idx, : len(row_token_type_ids)] = torch.tensor(row_token_type_ids, dtype=torch.long)
            attention_mask[row_idx, : len(inputs)] = 1

        input_ids = input_ids.to(args.device)
        labels = labels.to(args.device)
        attention_mask = attention_mask.to(args.device)
        token_type_ids = token_type_ids.to(args.device)
        with torch.inference_mode():
            logits = model(input_ids=input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids).logits
            shifted_logits = logits[:, :-1, :]
            shifted_labels = labels[:, 1:]
            loss = torch.nn.functional.cross_entropy(
                shifted_logits.reshape(-1, shifted_logits.shape[-1]).to(torch.float32),
                shifted_labels.reshape(-1),
                ignore_index=IGNORE_LABEL_ID,
                reduction="sum",
            )
            pred = torch.argmax(shifted_logits, dim=-1)

        valid = shifted_labels != IGNORE_LABEL_ID
        token_correct += int(((pred == shifted_labels) & valid).sum().item())
        valid_count = int(valid.sum().item())
        token_total += valid_count
        loss_sum += float(loss.item())

        pred_cpu = pred.cpu()
        labels_cpu = shifted_labels.cpu()
        valid_cpu = valid.cpu()
        for row_idx, (_, _, _, gold_text) in enumerate(batch):
            mask = valid_cpu[row_idx]
            gold_ids = [int(x) for x in labels_cpu[row_idx][mask].tolist()]
            pred_ids = [int(x) for x in pred_cpu[row_idx][mask].tolist()]
            seq_total += 1
            if pred_ids == gold_ids:
                seq_exact += 1
            processor_total += 1
            guess_text = decode_label(tokenizer, pred_ids, eos_id)
            if processor_family(guess_text) == processor_family(gold_text):
                processor_correct += 1
            update_status_map_metrics(status_metrics, guess_text, gold_text)
        batch = []

    for row in iter_rows(args.input):
        rows_seen += 1
        inst = [bos_id] + tokenizer.encode(row["instruction"], add_special_tokens=False) + [sep_id]
        resp = tokenizer.encode(row["response"], add_special_tokens=False) + [eos_id]
        row_len = len(inst) + len(resp)
        if max_len and row_len > max_len + 1:
            skipped_too_long += 1
            continue
        if unk_id in inst or unk_id in resp:
            skipped_unk += 1
            continue
        inputs = inst + resp
        labels = [IGNORE_LABEL_ID] * len(inst) + resp
        token_type_ids = [1] * len(inst) + [0] * len(resp)
        batch.append((inputs, labels, token_type_ids, row["response"].strip()))
        rows_kept += 1
        if len(batch) >= args.batch_size:
            flush()
        if args.max_rows is not None and rows_seen >= args.max_rows:
            break
    flush()

    status_result = {}
    rows = status_metrics.get("status/rows", 0.0)
    if rows:
        status_result["exact_accuracy"] = status_metrics["status/exact"] / rows
        status_result["rows"] = int(rows)
        status_result["sections"] = {}
        for section in STATUS_SECTIONS:
            tp = status_metrics[f"status/{section}/tp"]
            fp = status_metrics[f"status/{section}/fp"]
            fn = status_metrics[f"status/{section}/fn"]
            precision = tp / (tp + fp) if (tp + fp) else None
            recall = tp / (tp + fn) if (tp + fn) else None
            f1 = 2 * precision * recall / (precision + recall) if precision and recall else None
            status_result["sections"][section] = {
                "exact_accuracy": status_metrics[f"status/{section}/exact"] / rows,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "gold_count": int(status_metrics[f"status/{section}/gold"]),
                "pred_count": int(status_metrics[f"status/{section}/pred"]),
                "tp": int(tp),
                "fp": int(fp),
                "fn": int(fn),
            }

    result = {
        "model": str(args.model),
        "input": str(args.input),
        "batch_size": args.batch_size,
        "rows_seen": rows_seen,
        "rows_kept": rows_kept,
        "skipped_too_long": skipped_too_long,
        "skipped_unk": skipped_unk,
        "accuracy": token_correct / token_total if token_total else None,
        "exact_accuracy": seq_exact / seq_total if seq_total else None,
        "correct_processor": processor_correct / processor_total if processor_total else None,
        "loss": loss_sum / token_total if token_total else None,
        "status_map": status_result,
        "counts": {
            "token_correct": token_correct,
            "token_total": token_total,
            "seq_exact": seq_exact,
            "seq_total": seq_total,
            "processor_correct": processor_correct,
            "processor_total": processor_total,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
