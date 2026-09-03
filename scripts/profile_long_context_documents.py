#!/usr/bin/env python3
"""Profile full source documents for provenance-first long-context curation.

This is deliberately not an instruction-data generator. It measures complete
documents with the target tokenizer and, only for a source whose register row
has ``commercial_release_status=green``, can emit a deterministic candidate
sample for later task construction and human review.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import heapq
import json
import re
import zipfile
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REGISTER = Path("legal/registers/long-context-commercial-source-candidates.csv")
DEFAULT_SOURCE_ID = "rigsarkivet-folketinget-14004"
DEFAULT_INPUT = Path("data/downloads/datasets/folketingets_dokumenter_14004/14004.zip")
BIN_EDGES = (0, 4_096, 8_192, 16_384, 32_768, 60_000)
BIN_LABELS = ("under_4k", "4k_8k", "8k_16k", "16k_32k", "32k_60k", "60k_plus")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--source-register", type=Path, default=DEFAULT_REGISTER)
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--tokenizer-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--text-field", default="indhold")
    parser.add_argument("--id-field", default="identifikator")
    parser.add_argument(
        "--metadata-field",
        action="append",
        default=None,
        help="Field to preserve; repeat as needed. Folketing defaults are used when omitted.",
    )
    parser.add_argument("--language", default="da")
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--max-docs", type=int, default=None)
    parser.add_argument(
        "--sample-mode",
        choices=("first", "hash"),
        default="hash",
        help="With --max-docs, select the first eligible rows or a deterministic collection-wide sample.",
    )
    parser.add_argument("--sample-seed", type=int, default=20260831)
    parser.add_argument("--year-field", default="skabt")
    parser.add_argument("--year-min", type=int, default=None)
    parser.add_argument("--year-max", type=int, default=None)
    parser.add_argument("--ocr-field", default="dannet ved OCR")
    parser.add_argument("--ocr-value", default=None, help="Optional exact OCR-field filter, for example 'Nej'.")
    parser.add_argument("--min-chars", type=int, default=200)
    parser.add_argument("--candidate-min-tokens", type=int, default=8_192)
    parser.add_argument("--max-candidates-per-bin", type=int, default=100)
    parser.add_argument(
        "--emit-candidates",
        action="store_true",
        help="Write full-text candidates. Refused unless the source register status is green.",
    )
    return parser.parse_args()


def load_source(register: Path, source_id: str) -> dict[str, str]:
    with register.open(newline="", encoding="utf-8") as handle:
        matches = [row for row in csv.DictReader(handle) if row.get("source_id") == source_id]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one register row for {source_id!r}, found {len(matches)}")
    return matches[0]


def require_release_eligible(source: dict[str, str]) -> None:
    status = source.get("commercial_release_status", "").strip().lower()
    if status != "green":
        raise PermissionError(
            f"Source {source.get('source_id')!r} has commercial_release_status={status!r}; "
            "full-text candidate export requires an explicit human-reviewed 'green' decision"
        )


def clean_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\ufffd", " ")
    text = CONTROL_RE.sub(" ", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def bin_label(token_count: int) -> str:
    if token_count < 0:
        raise ValueError("token count cannot be negative")
    for index in range(len(BIN_EDGES) - 1):
        if BIN_EDGES[index] <= token_count < BIN_EDGES[index + 1]:
            return BIN_LABELS[index]
    return BIN_LABELS[-1]


def iter_json_rows(path: Path) -> Iterator[dict[str, Any]]:
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            yield row


def iter_rows(path: Path, fields: list[str], batch_size: int) -> Iterator[dict[str, Any]]:
    if path.name.endswith((".jsonl", ".jsonl.gz")):
        yield from iter_json_rows(path)
        return
    if path.suffix not in {".parquet", ".zip"}:
        raise ValueError(f"Unsupported input format: {path}")
    try:
        import pyarrow.parquet as pq
    except ImportError as error:
        raise RuntimeError("Parquet input requires pyarrow in the active environment") from error
    if path.suffix == ".parquet":
        parquet = pq.ParquetFile(path)
        for batch in parquet.iter_batches(columns=fields, batch_size=batch_size):
            yield from batch.to_pylist()
        return
    with zipfile.ZipFile(path) as archive:
        names = sorted(name for name in archive.namelist() if name.endswith(".parquet"))
        if len(names) != 1:
            raise ValueError(f"Expected one Parquet member in {path}, found {names}")
        with archive.open(names[0]) as member:
            parquet = pq.ParquetFile(member)
            for batch in parquet.iter_batches(columns=fields, batch_size=batch_size):
                yield from batch.to_pylist()


def load_token_counter(tokenizer_path: Path) -> Callable[[str], int]:
    try:
        from transformers import AutoTokenizer
    except ImportError as error:
        raise RuntimeError("Exact profiling requires the project's transformers environment") from error
    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_path,
        trust_remote_code=True,
        local_files_only=True,
    )

    def count(text: str) -> int:
        return len(tokenizer.encode(text, add_special_tokens=False))

    return count


def percentile(values: list[int], fraction: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = round((len(ordered) - 1) * fraction)
    return ordered[index]


def document_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def candidate_priority(source_id: str, document_id: str, digest: str) -> int:
    material = f"{source_id}\0{document_id}\0{digest}".encode("utf-8")
    return int.from_bytes(hashlib.blake2b(material, digest_size=8).digest(), "big")


def parse_year(value: object) -> int | None:
    prefix = clean_text(value)[:4]
    return int(prefix) if prefix.isdigit() else None


def row_passes_filters(
    row: dict[str, Any],
    *,
    year_field: str,
    year_min: int | None,
    year_max: int | None,
    ocr_field: str,
    ocr_value: str | None,
) -> bool:
    if year_min is not None or year_max is not None:
        year = parse_year(row.get(year_field))
        if year is None or (year_min is not None and year < year_min) or (year_max is not None and year > year_max):
            return False
    return ocr_value is None or clean_text(row.get(ocr_field)) == ocr_value


def filter_rows(
    rows: Iterable[dict[str, Any]],
    *,
    year_field: str,
    year_min: int | None,
    year_max: int | None,
    ocr_field: str,
    ocr_value: str | None,
) -> Iterator[dict[str, Any]]:
    for row in rows:
        if row_passes_filters(
            row,
            year_field=year_field,
            year_min=year_min,
            year_max=year_max,
            ocr_field=ocr_field,
            ocr_value=ocr_value,
        ):
            yield row


def select_hash_indices(
    rows: Iterable[dict[str, Any]],
    *,
    source_id: str,
    id_field: str,
    limit: int,
    seed: int,
    year_field: str,
    year_min: int | None,
    year_max: int | None,
    ocr_field: str,
    ocr_value: str | None,
) -> tuple[set[int], int]:
    """Select exact bottom-k stable hashes without retaining document text."""
    if limit < 1:
        raise ValueError("hash sample limit must be positive")
    heap: list[tuple[int, int]] = []
    eligible = 0
    for row_number, row in enumerate(rows):
        if not row_passes_filters(
            row,
            year_field=year_field,
            year_min=year_min,
            year_max=year_max,
            ocr_field=ocr_field,
            ocr_value=ocr_value,
        ):
            continue
        eligible += 1
        document_id = clean_text(row.get(id_field)) or f"row-{row_number}"
        material = f"{source_id}\0{seed}\0{document_id}\0{row_number}".encode("utf-8")
        priority = int.from_bytes(hashlib.blake2b(material, digest_size=8).digest(), "big")
        entry = (-priority, row_number)
        if len(heap) < limit:
            heapq.heappush(heap, entry)
        elif entry > heap[0]:
            heapq.heapreplace(heap, entry)
    return {row_number for _, row_number in heap}, eligible


def rows_at_indices(rows: Iterable[dict[str, Any]], indices: set[int]) -> Iterator[dict[str, Any]]:
    for row_number, row in enumerate(rows):
        if row_number in indices:
            yield row


def profile_documents(
    rows: Iterable[dict[str, Any]],
    *,
    source: dict[str, str],
    text_field: str,
    id_field: str,
    metadata_fields: list[str],
    language: str,
    count_tokens: Callable[[str], int],
    min_chars: int,
    max_docs: int | None,
    emit_candidates: bool,
    candidate_min_tokens: int,
    max_candidates_per_bin: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    if emit_candidates:
        require_release_eligible(source)
    if min_chars < 1 or candidate_min_tokens < 0 or max_candidates_per_bin < 1:
        raise ValueError("minimums and candidate capacity must be positive")

    stats: Counter[str] = Counter()
    token_lengths: list[int] = []
    heaps: dict[str, list[tuple[int, str, int, dict[str, Any]]]] = {label: [] for label in BIN_LABELS}
    candidate_digests: set[str] = set()
    profiled_metadata: list[dict[str, Any]] = []

    for row_number, row in enumerate(rows):
        if max_docs is not None and stats["documents_seen"] >= max_docs:
            break
        stats["documents_seen"] += 1
        text = clean_text(row.get(text_field))
        if len(text) < min_chars:
            stats["documents_skipped_short"] += 1
            continue
        token_count = count_tokens(text)
        label = bin_label(token_count)
        stats["documents_profiled"] += 1
        stats[f"documents_{label}"] += 1
        stats[f"tokens_{label}"] += token_count
        token_lengths.append(token_count)

        document_id = clean_text(row.get(id_field)) or f"row-{row_number}"
        digest = document_hash(text)
        metadata = {field: clean_text(row.get(field)) for field in metadata_fields}
        profiled_metadata.append(
            {
                "schema_version": "dfm-long-context-profiled-document-v1",
                "source_id": source["source_id"],
                "document_id": document_id,
                "language": language,
                "document_sha256": digest,
                "measurements": {"source_tokens": token_count, "length_bin": label},
                "metadata": metadata,
                "release_status": source.get("commercial_release_status", ""),
                "contains_source_text": False,
            }
        )

        if not emit_candidates or token_count < candidate_min_tokens:
            continue
        if digest in candidate_digests:
            stats["candidate_exact_duplicates_skipped"] += 1
            continue
        candidate_digests.add(digest)
        candidate = {
            "schema_version": "dfm-long-context-source-v1",
            "candidate_id": f"{source['source_id']}:{digest[:20]}",
            "stage": "source_document_not_instruction_data",
            "language": language,
            "native_status": source.get("native_status", ""),
            "text": text,
            "measurements": {"source_tokens": token_count, "length_bin": label},
            "source": {
                "source_id": source["source_id"],
                "document_id": document_id,
                "source_url": source.get("source_url", ""),
                "publisher": source.get("publisher", ""),
                "licence": source.get("licence", ""),
                "licence_url": source.get("licence_url", ""),
                "commercial_release_status": source.get("commercial_release_status", ""),
                "document_sha256": digest,
            },
            "metadata": metadata,
        }
        priority = candidate_priority(source["source_id"], document_id, digest)
        heap = heaps[label]
        entry = (-priority, candidate["candidate_id"], row_number, candidate)
        if len(heap) < max_candidates_per_bin:
            heapq.heappush(heap, entry)
        elif entry > heap[0]:
            heapq.heapreplace(heap, entry)

    candidates = [entry[3] for heap in heaps.values() for entry in heap]
    candidates.sort(key=lambda row: (row["measurements"]["source_tokens"], row["candidate_id"]))
    summary = {
        "schema_version": "dfm-long-context-profile-v1",
        "source_id": source["source_id"],
        "commercial_release_status": source.get("commercial_release_status", ""),
        "bin_semantics": {
            label: (
                f"[{BIN_EDGES[index]}, {BIN_EDGES[index + 1]})"
                if index < len(BIN_EDGES) - 1
                else f"[{BIN_EDGES[-1]}, infinity)"
            )
            for index, label in enumerate(BIN_LABELS)
        },
        "stats": dict(stats),
        "token_length_percentiles": {
            "min": min(token_lengths) if token_lengths else None,
            "p50": percentile(token_lengths, 0.50),
            "p90": percentile(token_lengths, 0.90),
            "p95": percentile(token_lengths, 0.95),
            "p99": percentile(token_lengths, 0.99),
            "max": max(token_lengths) if token_lengths else None,
        },
        "candidate_count": len(candidates),
        "profiled_metadata_count": len(profiled_metadata),
    }
    return summary, candidates, profiled_metadata


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def atomic_write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def main() -> None:
    args = parse_args()
    metadata_fields = args.metadata_field or [
        "titel",
        "skabt",
        "type",
        "antal ord",
        "dannet ved OCR",
        "OCR-metode",
    ]
    source = load_source(args.source_register, args.source_id)
    if args.emit_candidates:
        require_release_eligible(source)
    fields = list(
        dict.fromkeys(
            [args.text_field, args.id_field, args.year_field, args.ocr_field, *metadata_fields]
        )
    )
    counter = load_token_counter(args.tokenizer_path)
    sampling: dict[str, Any] = {
        "mode": args.sample_mode if args.max_docs is not None else "all",
        "seed": args.sample_seed,
        "requested_documents": args.max_docs,
        "year_min": args.year_min,
        "year_max": args.year_max,
        "ocr_value": args.ocr_value,
    }
    if args.max_docs is not None and args.sample_mode == "hash":
        selection_fields = list(dict.fromkeys([args.id_field, args.year_field, args.ocr_field]))
        selected, eligible = select_hash_indices(
            iter_rows(args.input, selection_fields, args.batch_size),
            source_id=args.source_id,
            id_field=args.id_field,
            limit=args.max_docs,
            seed=args.sample_seed,
            year_field=args.year_field,
            year_min=args.year_min,
            year_max=args.year_max,
            ocr_field=args.ocr_field,
            ocr_value=args.ocr_value,
        )
        rows = rows_at_indices(iter_rows(args.input, fields, args.batch_size), selected)
        profile_limit = None
        sampling.update({"eligible_documents": eligible, "selected_documents": len(selected)})
    else:
        rows = filter_rows(
            iter_rows(args.input, fields, args.batch_size),
            year_field=args.year_field,
            year_min=args.year_min,
            year_max=args.year_max,
            ocr_field=args.ocr_field,
            ocr_value=args.ocr_value,
        )
        profile_limit = args.max_docs
    summary, candidates, profiled_metadata = profile_documents(
        rows,
        source=source,
        text_field=args.text_field,
        id_field=args.id_field,
        metadata_fields=metadata_fields,
        language=args.language,
        count_tokens=counter,
        min_chars=args.min_chars,
        max_docs=profile_limit,
        emit_candidates=args.emit_candidates,
        candidate_min_tokens=args.candidate_min_tokens,
        max_candidates_per_bin=args.max_candidates_per_bin,
    )
    summary.update(
        {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "input": str(args.input),
            "tokenizer_path": str(args.tokenizer_path),
            "text_field": args.text_field,
            "id_field": args.id_field,
            "metadata_fields": metadata_fields,
            "sampling": sampling,
        }
    )
    atomic_write_json(args.output_dir / "profile.json", summary)
    atomic_write_jsonl(args.output_dir / "profiled_documents.jsonl", profiled_metadata)
    if args.emit_candidates:
        atomic_write_jsonl(args.output_dir / "source_documents.jsonl", candidates)
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
