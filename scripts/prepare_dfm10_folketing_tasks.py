#!/usr/bin/env python3
"""Turn Folketinget documents into audited self-supervised DFM10 tasks.

The Rigsarkivet delivery is raw Danish document text, not instruction data.
This script therefore creates bounded reconstruction/continuation examples:

* ``folketingets-dokumenter-prefix-continuation``
* ``folketingets-dokumenter-denoising``
* ``folketingets-dokumenter-error-correction``
* ``folketingets-dokumenter-span-filling``

Each output is an export-style ``data/*.jsonl.gz`` tree, compatible with
``scripts/audit_export_datasets.py``. The source document is never placed in
the user prompt as metadata; title and provenance are retained in row fields.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
import re
import shutil
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

import pyarrow.parquet as pq


ARCHIVE_URL = "https://digidata.rigsarkivet.dk/download/14004"
DEFAULT_ARCHIVE = Path("data/downloads/datasets/folketingets_dokumenter_14004/14004.zip")
DEFAULT_OUTPUT = Path("data/dfm10_folketing_transform_sources")
SOURCE_NAME = "folketingets-dokumenter-14004"
MAX_SOURCE_CHARS = 2_200

TASKS = (
    "folketingets-dokumenter-prefix-continuation",
    "folketingets-dokumenter-denoising",
    "folketingets-dokumenter-error-correction",
    "folketingets-dokumenter-span-filling",
)

WORD_RE = re.compile(r"\S+")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--parquet", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-chars", type=int, default=MAX_SOURCE_CHARS)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--seed", type=int, default=20260822)
    parser.add_argument("--max-docs", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def extract_archive(archive: Path) -> Path:
    if not archive.is_file():
        raise FileNotFoundError(
            f"Missing {archive}. Download {ARCHIVE_URL} into this path first."
        )
    parquet_files = sorted(archive.parent.glob("*.parquet"))
    if parquet_files:
        return parquet_files[0]
    with zipfile.ZipFile(archive) as source:
        names = [name for name in source.namelist() if name.endswith(".parquet")]
        if len(names) != 1:
            raise ValueError(f"Expected one parquet in {archive}, found {names}")
        name = names[0]
        target = archive.parent / Path(name).name
        with source.open(name) as src, target.open("wb") as dst:
            shutil.copyfileobj(src, dst, length=8 * 1024 * 1024)
    return target


def stable_seed(seed: int, *parts: object) -> int:
    digest = hashlib.blake2b(digest_size=8)
    digest.update(str(seed).encode())
    for part in parts:
        digest.update(b"\0")
        digest.update(str(part).encode("utf-8", errors="replace"))
    return int.from_bytes(digest.digest(), "little")


def clean_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = CONTROL_RE.sub(" ", text)
    text = text.replace("\ufffd", " ")
    return re.sub(r"[ \t]+", " ", text).strip()


def usable_document(text: str) -> bool:
    words = WORD_RE.findall(text)
    if len(words) < 40:
        return False
    alnum = sum(char.isalnum() for char in text)
    return alnum >= 100 and alnum / max(1, len(text)) >= 0.18


def split_windows(text: str, max_chars: int) -> Iterator[str]:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            window = text[start:end]
            candidates = [window.rfind("\n\n"), window.rfind(". "), window.rfind("! "), window.rfind("? ")]
            cut = max(candidates)
            if cut >= max_chars // 2:
                end = start + cut + 1
            else:
                space = window.rfind(" ")
                if space >= max_chars // 2:
                    end = start + space
        chunk = text[start:end].strip()
        if chunk and len(WORD_RE.findall(chunk)) >= 20:
            yield chunk
        start = max(end, start + 1)


def corrupt_words(text: str, rng: random.Random) -> str:
    words = text.split()
    if len(words) < 12:
        return text
    vocabulary = [word for word in words if len(word) > 2] or words
    out: list[str] = []
    index = 0
    while index < len(words):
        word = words[index]
        if rng.random() >= 0.10:
            out.append(word)
            index += 1
            continue
        operation = rng.choice(("delete", "replace", "duplicate", "swap"))
        if operation == "delete":
            index += 1
        elif operation == "replace":
            out.append(rng.choice(vocabulary))
            index += 1
        elif operation == "duplicate":
            out.extend((word, word))
            index += 1
        elif index + 1 < len(words):
            out.extend((words[index + 1], word))
            index += 2
        else:
            out.append(word)
            index += 1
    return " ".join(out)


OCR_CONFUSIONS = {
    "rn": "m",
    "m": "rn",
    "l": "1",
    "I": "l",
    "o": "0",
    "O": "0",
    "e": "c",
}


def corrupt_characters(text: str, rng: random.Random) -> str:
    """Inject sparse reversible-looking OCR errors without changing content scale."""
    chars = list(text)
    candidates = [i for i, char in enumerate(chars) if char.isalpha() and char.lower() in "aeilmnorc"]
    if len(candidates) < 8:
        return text
    for index in rng.sample(candidates, k=max(1, min(len(candidates) // 80, 8))):
        char = chars[index]
        replacement = OCR_CONFUSIONS.get(char, OCR_CONFUSIONS.get(char.lower(), char))
        if replacement != char:
            chars[index] = replacement
    return "".join(chars)


def mask_spans(text: str, rng: random.Random) -> str:
    matches = list(WORD_RE.finditer(text))
    if len(matches) < 20:
        return text
    target = max(2, min(10, round(len(matches) * 0.15)))
    start = rng.randrange(2, max(3, len(matches) - target))
    end = min(len(matches), start + target)
    return text[: matches[start].start()] + "<mask_1>" + text[matches[end - 1].end() :]


def chat_row(task: str, source_id: str, instruction: str, response: str, metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "user", "content": instruction.strip()},
            {"role": "assistant", "content": response.strip()},
        ],
        "source": SOURCE_NAME,
        "source_id": source_id,
        "task": task,
        "language": "da",
        "metadata": metadata,
    }


def rows_for_chunk(text: str, source_id: str, seed: int, metadata: dict[str, Any]) -> Iterator[tuple[str, dict[str, Any]]]:
    prefix_rng = random.Random(stable_seed(seed, source_id, "prefix"))
    cut = int(len(text) * prefix_rng.uniform(0.30, 0.70))
    while cut < len(text) - 1 and not text[cut].isspace():
        cut += 1
    prefix, suffix = text[:cut].strip(), text[cut:].strip()
    if prefix and suffix:
        yield TASKS[0], chat_row(
            TASKS[0], source_id, "Fortsæt teksten naturligt.\n\n" + prefix, suffix, metadata
        )

    noisy = corrupt_words(text, random.Random(stable_seed(seed, source_id, "denoise")))
    if noisy != text:
        yield TASKS[1], chat_row(TASKS[1], source_id, "Gendan den oprindelige tekst.\n\n" + noisy, text, metadata)

    corrected = corrupt_characters(text, random.Random(stable_seed(seed, source_id, "ocr")))
    if corrected != text:
        yield TASKS[2], chat_row(TASKS[2], source_id, "Ret OCR- og tekstfejlene.\n\n" + corrected, text, metadata)

    masked = mask_spans(text, random.Random(stable_seed(seed, source_id, "span")))
    if masked != text:
        yield TASKS[3], chat_row(TASKS[3], source_id, "Udfyld den manglende tekst.\n\n" + masked, text, metadata)


class Writers:
    def __init__(self, root: Path, batch_size: int) -> None:
        self.root = root
        self.batch_size = batch_size
        self.handles: dict[str, Any] = {}
        self.buffers: dict[str, list[str]] = {task: [] for task in TASKS}
        self.counts: Counter[str] = Counter()

    def write(self, task: str, row: dict[str, Any]) -> None:
        self.buffers[task].append(json.dumps(row, ensure_ascii=False) + "\n")
        if len(self.buffers[task]) >= self.batch_size:
            self.flush(task)

    def flush(self, task: str) -> None:
        rows = self.buffers[task]
        if not rows:
            return
        if task not in self.handles:
            path = self.root / task / "data" / "train-00000.jsonl.gz"
            path.parent.mkdir(parents=True, exist_ok=True)
            self.handles[task] = gzip.open(path, "wt", encoding="utf-8", compresslevel=1)
        self.handles[task].writelines(rows)
        self.counts[task] += len(rows)
        self.buffers[task] = []

    def close(self) -> None:
        for task in TASKS:
            self.flush(task)
        for handle in self.handles.values():
            handle.close()


def main() -> None:
    args = parse_args()
    parquet = args.parquet or extract_archive(args.archive)
    if args.output_root.exists():
        if not args.force:
            raise FileExistsError(f"{args.output_root} exists; use --force")
        shutil.rmtree(args.output_root)
    args.output_root.mkdir(parents=True)

    writers = Writers(args.output_root, args.batch_size)
    stats: Counter[str] = Counter()
    parquet_file = pq.ParquetFile(parquet)
    for row_number, row in enumerate(parquet_file.iter_batches(
        columns=["identifikator", "indhold", "titel", "skabt", "type", "dannet ved OCR", "OCR-metode"],
        batch_size=args.batch_size,
    )):
        for source_row in row.to_pylist():
            if args.max_docs is not None and stats["documents_seen"] >= args.max_docs:
                break
            stats["documents_seen"] += 1
            text = clean_text(source_row.get("indhold"))
            if not usable_document(text):
                stats["documents_skipped"] += 1
                continue
            metadata = {
                "document_id": clean_text(source_row.get("identifikator")),
                "title": clean_text(source_row.get("titel")),
                "period": clean_text(source_row.get("skabt")),
                "document_type": clean_text(source_row.get("type")),
                "ocr": clean_text(source_row.get("dannet ved OCR")),
                "ocr_method": clean_text(source_row.get("OCR-metode")),
                "source_row": stats["documents_seen"] - 1,
            }
            stats["documents_used"] += 1
            for chunk_index, chunk in enumerate(split_windows(text, args.max_chars)):
                stats["source_windows"] += 1
                source_id = f"{metadata['document_id']}:{chunk_index}"
                for task, generated in rows_for_chunk(chunk, source_id, args.seed, metadata):
                    writers.write(task, generated)
                    stats[f"rows_{task}"] += 1
                    stats[f"chars_{task}"] += len(chunk)
        if args.max_docs is not None and stats["documents_seen"] >= args.max_docs:
            break
        if (row_number + 1) % 25 == 0:
            print(f"documents={stats['documents_seen']} windows={stats['source_windows']} rows={sum(stats[k] for k in stats if k.startswith('rows_'))}", flush=True)
    writers.close()

    manifest = {
        "source": "Rigsarkivet handover 14004 / Folketinget",
        "source_url": "https://digidata.rigsarkivet.dk/aflevering/14004",
        "archive": str(args.archive),
        "parquet": str(parquet),
        "max_chars": args.max_chars,
        "seed": args.seed,
        "tasks": list(TASKS),
        "stats": dict(stats),
        "row_counts": dict(writers.counts),
    }
    (args.output_root / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    for task in TASKS:
        readme = args.output_root / task / "README.md"
        readme.write_text(
            f"# {task}\n\nGenerated from Rigsarkivet handover 14004. Rows must be audited with `scripts/audit_export_datasets.py` before training.\n",
            encoding="utf-8",
        )
    print(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
