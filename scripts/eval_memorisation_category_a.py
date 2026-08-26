#!/usr/bin/env python3
"""Run the Category-A raw/chat verbatim-continuation extraction probe."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import heapq
import json
import math
import os
import statistics
import unicodedata
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator


REPO = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = REPO / "exports/dfm8_XL_step1650000_ema_hf"
DEFAULT_OUTPUT = REPO / "logs/analysis/dfm9_memorisation_category_a_step1650000"
DEFAULT_TEMPLATE = REPO / "evaluation/chat_templates/gemma4_native_chat.jinja"
PREFIX_TOKENS = 64
TARGET_TOKENS = 64
AGREEMENT_SUBSETS = ("dkmedier", "odense", "danskerhverv")
PROTOCOL_ID = "dfm9-memorisation-prefix64-target64-gemma4-chat-v1"


@dataclass(frozen=True)
class SourceRow:
    cohort: str
    source_id: str
    title: str
    url: str
    text: str
    source_path: str


@dataclass(frozen=True)
class Candidate:
    rank: int
    content_hash: str
    row: SourceRow


class BottomK:
    """Retain the deterministic k-smallest unique content-hash ranks."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.heap: list[tuple[int, str, Candidate]] = []
        self.selected: set[str] = set()

    def add(self, candidate: Candidate) -> None:
        if candidate.content_hash in self.selected:
            return
        item = (-candidate.rank, candidate.content_hash, candidate)
        if len(self.heap) < self.limit:
            heapq.heappush(self.heap, item)
            self.selected.add(candidate.content_hash)
            return
        if candidate.rank >= -self.heap[0][0]:
            return
        removed = heapq.heapreplace(self.heap, item)[2]
        self.selected.remove(removed.content_hash)
        self.selected.add(candidate.content_hash)

    def ordered(self) -> list[Candidate]:
        return sorted((item[2] for item in self.heap), key=lambda item: item.rank)


def normalized_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def make_candidate(row: SourceRow, seed: int) -> Candidate:
    canonical = normalized_text(row.text)
    content_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    rank = int.from_bytes(
        hashlib.sha256(f"{seed}\0{row.cohort}\0{content_hash}".encode()).digest()[:16],
        "big",
    )
    return Candidate(rank=rank, content_hash=content_hash, row=row)


def metadata_title_url(row: dict[str, Any]) -> tuple[str, str]:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    title = str(metadata.get("title") or "")
    url = str(metadata.get("url") or "")
    nested = metadata.get("metadata") if isinstance(metadata.get("metadata"), dict) else {}
    graph = nested.get("@graph") if isinstance(nested.get("@graph"), list) else []
    if graph and isinstance(graph[0], dict):
        title = title or str(graph[0].get("headline") or graph[0].get("name") or "")
        url = url or str(graph[0].get("mainEntityOfPage") or "")
    return title, url


def iter_jsonl(path: Path, cohort: str) -> Iterator[SourceRow]:
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                row = json.loads(line, strict=False)
            except json.JSONDecodeError:
                continue
            text = str(row.get("text") or "").strip()
            if not text:
                continue
            title, url = metadata_title_url(row)
            yield SourceRow(
                cohort=cohort,
                source_id=str(row.get("id") or f"{path.name}:{line_number}"),
                title=title,
                url=url,
                text=text,
                source_path=str(path),
            )


def iter_instruct_bt(path: Path) -> Iterator[SourceRow]:
    import pyarrow.parquet as pq

    parquet = pq.ParquetFile(path)
    columns = ["prompt_id", "messages", "title", "url", "subset"]
    for batch in parquet.iter_batches(batch_size=4096, columns=columns):
        for row in batch.to_pylist():
            subset = str(row.get("subset") or "")
            if subset not in AGREEMENT_SUBSETS:
                continue
            messages = row.get("messages") or []
            assistant = [str(item.get("content") or "") for item in messages if item.get("role") == "assistant"]
            text = assistant[-1].strip() if assistant else ""
            if not text:
                continue
            yield SourceRow(
                cohort=f"A-06-{subset}",
                source_id=str(row.get("prompt_id") or ""),
                title=str(row.get("title") or ""),
                url=str(row.get("url") or ""),
                text=text,
                source_path=str(path),
            )


def category_a_rows() -> Iterator[SourceRow]:
    downloads = REPO / "data/downloads/datasets"
    yield from iter_jsonl(downloads / "lexdk/lexdk_articles.jsonl.gz", "A-01-lexdk")
    for path in sorted((downloads / "dbc").glob("dbc-abstracts_*.jsonl.gz")):
        yield from iter_jsonl(path, "A-02-dbc-abstracts")
    yield from iter_jsonl(downloads / "dbc/dbc-reviews.jsonl.gz", "A-03-dbc-reviews")
    yield from iter_jsonl(downloads / "dbc/dbc-faktalink.jsonl.gz", "A-04-faktalink")
    yield from iter_jsonl(downloads / "dbc/dbc-farfatterweb.jsonl.gz", "A-05-forfatterweb")
    yield from iter_instruct_bt(downloads / "oliverkinch_instruct_bt/data/train-00000-of-00001.parquet")


def first_message(messages: list[dict[str, Any]], roles: set[str]) -> str:
    for message in messages:
        if str(message.get("role") or message.get("from") or "").lower() in roles:
            return str(message.get("content") or message.get("value") or "").strip()
    return ""


def iter_rlve(path: Path) -> Iterator[SourceRow]:
    import pyarrow.parquet as pq

    for parquet_path in sorted(path.rglob("*.parquet")):
        parquet = pq.ParquetFile(parquet_path)
        for batch in parquet.iter_batches(batch_size=4096, columns=["id", "messages", "category"]):
            for row in batch.to_pylist():
                text = first_message(row.get("messages") or [], {"user", "human"})
                if text:
                    yield SourceRow(
                        cohort="B-01-rlve-source-problems",
                        source_id=str(row.get("id") or ""),
                        title=str(row.get("category") or ""),
                        url="",
                        text=text,
                        source_path=str(parquet_path),
                    )


def iter_longalign(path: Path) -> Iterator[SourceRow]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            text = first_message(row.get("messages") or [], {"user", "human"})
            if text:
                yield SourceRow(
                    cohort="B-02-longalign-documents",
                    source_id=str(row.get("id") or ""),
                    title=str(row.get("dataset") or ""),
                    url="",
                    text=text,
                    source_path=str(path),
                )


def embedded_document(text: str) -> str:
    import re

    match = re.search(r"<document>\s*(.*?)\s*</document>", text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def iter_euroblocks(path: Path) -> Iterator[SourceRow]:
    import pyarrow.parquet as pq

    embedded_labels = {"instruction-generation", "instruction-generation-ifeval"}
    unavailable_seed_labels = {
        "multilingual-synthetic-llama3.1-70B",
        "multilingual-synthetic-ifeval-llama3.1-70B",
        "multilingual-synthetic-ifeval-llama3.1-405B",
    }
    ordinal = 0
    for parquet_path in sorted(path.glob("*.parquet")):
        parquet = pq.ParquetFile(parquet_path)
        for batch in parquet.iter_batches(batch_size=4096, columns=["conversations", "dataset", "language"]):
            for row in batch.to_pylist():
                label = str(row.get("dataset") or "")
                if label not in embedded_labels | unavailable_seed_labels:
                    continue
                prompt = first_message(row.get("conversations") or [], {"user", "human"})
                if label in embedded_labels:
                    text = embedded_document(prompt)
                    cohort = "B-03-euroblocks-embedded-documents"
                else:
                    text = prompt
                    cohort = "B-04-euroblocks-unavailable-seed-proxies"
                if not text:
                    continue
                ordinal += 1
                yield SourceRow(
                    cohort=cohort,
                    source_id=f"{label}:{ordinal}",
                    title=f"{label}/{row.get('language') or ''}",
                    url="",
                    text=text,
                    source_path=str(parquet_path),
                )


def tasksource_residual_filenames() -> set[str]:
    path = REPO / "legal/registers/dfm9-sapient-instruction-family-inventory.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        selected = {row["filename"] for row in rows if row["audit_bucket"] == "tasksource_residual_research_tdm"}
    if len(selected) != 84:
        raise RuntimeError(f"expected 84 Article-3 Tasksource files, found {len(selected)}")
    return selected


def iter_tasksource_residual(path: Path) -> Iterator[SourceRow]:
    import pyarrow.parquet as pq

    for filename in sorted(tasksource_residual_filenames()):
        parquet_path = path / filename
        parquet = pq.ParquetFile(parquet_path)
        columns = [name for name in ("instruction", "response", "condition") if name in parquet.schema_arrow.names]
        for batch in parquet.iter_batches(batch_size=4096, columns=columns):
            for ordinal, row in enumerate(batch.to_pylist()):
                text = str(row.get("instruction") or "").strip()
                if text:
                    yield SourceRow(
                        cohort="B-05-tasksource-residual",
                        source_id=f"{filename}:{ordinal}",
                        title=filename,
                        url="",
                        text=text,
                        source_path=str(parquet_path),
                    )


def category_b_rows() -> Iterator[SourceRow]:
    downloads = REPO / "data/downloads/datasets"
    yield from iter_rlve(downloads / "allenai_verifiable_reasoning_gpt41")
    yield from iter_rlve(downloads / "allenai_verifiable_reasoning_o4mini")
    yield from iter_longalign(Path("/work/dfm/.cache/legal-audit/zai-org__LongAlign-10k/long.jsonl"))
    yield from iter_euroblocks(Path("/work/dfm/.cache/legal-audit/utter-project__EuroBlocks-SFT-Synthetic-1124/data"))
    yield from iter_tasksource_residual(downloads / "sapient_cleaned/data_clustered/tasksource")


def parquet_messages(path: Path, cohort: str) -> Iterator[SourceRow]:
    """Read conversational parquet rows, retaining only user/source messages."""
    import pyarrow.parquet as pq

    parquet = pq.ParquetFile(path)
    names = set(parquet.schema_arrow.names)
    columns = [name for name in ("id", "row_id", "messages", "conversations", "conversation_a", "instruction", "prompt", "text", "opening_msg", "source") if name in names]
    for batch in parquet.iter_batches(batch_size=4096, columns=columns):
        for ordinal, row in enumerate(batch.to_pylist()):
            messages = row.get("messages") or row.get("conversations") or row.get("conversation_a") or []
            if isinstance(messages, list):
                text = first_message(messages, {"user", "human"})
            else:
                text = ""
            if not text:
                for key in ("instruction", "prompt", "text", "opening_msg"):
                    value = row.get(key)
                    if isinstance(value, str) and value.strip():
                        text = value.strip()
                        break
            if text:
                yield SourceRow(
                    cohort=cohort,
                    source_id=str(row.get("id") or row.get("row_id") or f"{path.name}:{ordinal}"),
                    title=str(row.get("source") or ""),
                    url="",
                    text=text,
                    source_path=str(path),
                )


def jsonl_messages(path: Path, cohort: str) -> Iterator[SourceRow]:
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for ordinal, line in enumerate(handle):
            try:
                row = json.loads(line, strict=False)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            messages = row.get("messages") or row.get("conversations") or []
            text = first_message(messages, {"user", "human"}) if isinstance(messages, list) else ""
            if not text:
                for key in ("instruction", "prompt", "text", "opening_msg"):
                    value = row.get(key)
                    if isinstance(value, str) and value.strip():
                        text = value.strip()
                        break
            if text:
                yield SourceRow(
                    cohort=cohort,
                    source_id=str(row.get("id") or row.get("row_id") or f"{path.name}:{ordinal}"),
                    title=str(row.get("source") or row.get("dataset") or ""),
                    url="",
                    text=text,
                    source_path=str(path),
                )


def flan_cohort(path: Path) -> str:
    name = path.name.lower()
    for marker, cohort in (("race", "C-01-race"), ("dream", "C-02-dream"), ("web_questions", "C-03-webquestions"), ("coqa", "C-04-coqa")):
        if marker in name:
            return cohort
    return "C-05-sapient-flan-residual"


def manifest_sources(category: str) -> Iterator[tuple[str, Path]]:
    manifest = REPO / "data/legal/dfm9_memorisation_sources/manifest.tsv"
    seen: set[tuple[str, str]] = set()
    with manifest.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row.get("category") != category:
                continue
            if row.get("source_kind") not in {"file", "directory"}:
                continue
            cohort = str(row.get("cohort") or "").strip()
            source = Path(str(row.get("source_path") or "").strip())
            key = (cohort, str(source))
            if cohort and source and key not in seen and source.exists():
                seen.add(key)
                yield cohort, source


def category_c_rows() -> Iterator[SourceRow]:
    for cohort, source in manifest_sources("C"):
        if source.is_dir():
            yield from iter_recursive_sources(source, cohort)
        elif source.suffix == ".parquet":
            yield from parquet_messages(source, cohort)
        else:
            yield from jsonl_messages(source, cohort)


def iter_recursive_sources(path: Path, cohort: str) -> Iterator[SourceRow]:
    if path.is_file():
        if path.suffix == ".parquet":
            yield from parquet_messages(path, cohort)
        elif path.suffix in {".jsonl", ".json"} or path.name.endswith(".jsonl.gz"):
            yield from jsonl_messages(path, cohort)
        return
    for source in sorted(path.rglob("*")):
        if not source.is_file():
            continue
        if source.suffix == ".parquet":
            yield from parquet_messages(source, cohort)
        elif source.suffix in {".jsonl", ".json"} or source.name.endswith(".jsonl.gz"):
            yield from jsonl_messages(source, cohort)


def category_d_rows() -> Iterator[SourceRow]:
    for cohort, source in manifest_sources("D"):
        if source.is_dir():
            yield from iter_recursive_sources(source, cohort)
        elif source.suffix == ".parquet":
            yield from parquet_messages(source, cohort)
        else:
                yield from jsonl_messages(source, cohort)


def iter_manifest_source(cohort: str, source: Path) -> Iterator[SourceRow]:
    if source.is_dir():
        yield from iter_recursive_sources(source, cohort)
    elif source.suffix == ".parquet":
        yield from parquet_messages(source, cohort)
    else:
        yield from jsonl_messages(source, cohort)


def scan_manifest_item(item: tuple[int, str, str, int, int, str]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
    """Scan one manifest path, atomically checkpointing its bounded candidates."""
    item_index, cohort, source_name, pool_limit, seed, checkpoint_name = item
    checkpoint_path = Path(checkpoint_name)
    if checkpoint_path.exists() and checkpoint_path.stat().st_size > 0:
        with gzip.open(checkpoint_path, "rt", encoding="utf-8") as handle:
            cached = json.load(handle)
        # A zero-row cache is stale when a source adapter has since learned
        # the source schema; all current manifest inputs are expected to have
        # at least one source-side record.
        if int(cached.get("scanned", 0)) > 0:
            if cohort != "D-04" or len(cached.get("candidates", {}).get(cohort, [])) >= pool_limit * 2:
                return cached["candidates"], {cohort: int(cached["scanned"])}
    local_pool_limit = pool_limit * 3 if cohort == "D-04" else pool_limit
    pools: dict[str, BottomK] = {cohort: BottomK(local_pool_limit)}
    scanned = 0
    for row in iter_manifest_source(cohort, Path(source_name)):
        scanned += 1
        pools[cohort].add(make_candidate(row, seed))
    candidates = {
        name: [
            {
                "rank": candidate.rank,
                "content_hash": candidate.content_hash,
                "row": asdict(candidate.row),
            }
            for candidate in pool.ordered()
        ]
        for name, pool in pools.items()
    }
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = checkpoint_path.with_suffix(checkpoint_path.suffix + ".tmp")
    with gzip.open(temporary_path, "wt", encoding="utf-8") as handle:
        json.dump({"item_index": item_index, "cohort": cohort, "source": source_name, "scanned": scanned, "candidates": candidates}, handle)
    temporary_path.replace(checkpoint_path)
    return candidates, {cohort: scanned}


def selected_rows(categories: str) -> Iterator[SourceRow]:
    requested = {item.strip().upper() for item in categories.split(",") if item.strip()}
    unknown = requested - {"A", "B", "C", "D"}
    if not requested or unknown:
        raise ValueError(f"categories must be A, B, C, and/or D, got {categories!r}")
    if "A" in requested:
        yield from category_a_rows()
    if "B" in requested:
        yield from category_b_rows()
    if "C" in requested:
        yield from category_c_rows()
    if "D" in requested:
        yield from category_d_rows()


def prepare(args: argparse.Namespace) -> None:
    from transformers import AutoTokenizer

    args.output_dir.mkdir(parents=True, exist_ok=True)
    pool_limit = args.samples_per_cohort * args.candidate_multiplier
    pools: dict[str, BottomK] = {}
    scanned = Counter()
    requested = {item.strip().upper() for item in args.categories.split(",") if item.strip()}
    if args.workers > 1 and requested <= {"C", "D"}:
        checkpoint_dir = args.output_dir / "candidate_checkpoints"
        source_items = [(cohort, source) for cohort, source in manifest_sources("C") if "C" in requested]
        source_items.extend((cohort, source) for cohort, source in manifest_sources("D") if "D" in requested)
        items = [
            (index, cohort, str(source), pool_limit, args.seed, str(checkpoint_dir / f"item_{index:04d}.json.gz"))
            for index, (cohort, source) in enumerate(source_items)
        ]
        print(f"parallel preparation: {len(items)} manifest items, workers={args.workers}", flush=True)
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(scan_manifest_item, item) for item in items]
            completed_items = 0
            for future in as_completed(futures):
                candidate_groups, counts = future.result()
                for cohort, values in counts.items():
                    scanned[cohort] += values
                for cohort, values in candidate_groups.items():
                    target = pools.setdefault(cohort, BottomK(pool_limit))
                    for value in values:
                        row = SourceRow(**value["row"])
                        target.add(Candidate(rank=value["rank"], content_hash=value["content_hash"], row=row))
                completed_items += 1
                if completed_items % 10 == 0 or completed_items == len(futures):
                    print(f"completed source items {completed_items}/{len(futures)}; scanned {sum(scanned.values()):,} rows", flush=True)
    else:
        for row in selected_rows(args.categories):
            scanned[row.cohort] += 1
            pools.setdefault(row.cohort, BottomK(pool_limit)).add(make_candidate(row, args.seed))
            total = sum(scanned.values())
            if total % 1_000_000 == 0:
                print(f"scanned {total:,} source rows", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    prepared: list[dict[str, Any]] = []
    preparation = {}
    for cohort in sorted(pools):
        candidates = pools[cohort].ordered()
        eligible = 0
        selected = 0
        for start in range(0, len(candidates), args.tokenizer_batch_size):
            chunk = candidates[start : start + args.tokenizer_batch_size]
            encoded = tokenizer(
                [candidate.row.text for candidate in chunk],
                add_special_tokens=False,
                return_attention_mask=False,
            )["input_ids"]
            for candidate, token_ids in zip(chunk, encoded, strict=True):
                if len(token_ids) < PREFIX_TOKENS + TARGET_TOKENS:
                    continue
                eligible += 1
                if selected >= args.samples_per_cohort:
                    continue
                row = candidate.row
                prepared.append(
                    {
                        "cohort": cohort,
                        "source_id": row.source_id,
                        "title": row.title,
                        "url": row.url,
                        "source_path": row.source_path,
                        "content_hash": candidate.content_hash,
                        "rank": candidate.rank,
                        "prefix_token_ids": token_ids[:PREFIX_TOKENS],
                        "target_token_ids": token_ids[PREFIX_TOKENS : PREFIX_TOKENS + TARGET_TOKENS],
                    }
                )
                selected += 1
            if selected >= args.samples_per_cohort:
                break
        preparation[cohort] = {
            "source_rows_scanned": scanned[cohort],
            "unique_bottom_k_candidates": len(candidates),
            "eligible_candidates_examined": eligible,
            "selected": selected,
            "candidate_pool_exhausted": selected < args.samples_per_cohort,
        }
        if selected < args.samples_per_cohort:
            print(
                f"{cohort}: only {selected:,} eligible examples; using all eligible candidates "
                f"(scanned={scanned[cohort]:,}, candidate_pool={len(candidates):,})",
                flush=True,
            )
        print(f"{cohort}: scanned={scanned[cohort]:,} selected={selected:,}", flush=True)

    # Deduplicate sampled texts across cohorts while retaining the first legal cohort.
    deduplicated = []
    seen_hashes = set()
    cross_cohort_duplicates = Counter()
    for row in sorted(prepared, key=lambda item: (item["cohort"], item["rank"])):
        if row["content_hash"] in seen_hashes:
            cross_cohort_duplicates[row["cohort"]] += 1
            continue
        seen_hashes.add(row["content_hash"])
        deduplicated.append(row)
    for cohort, count in cross_cohort_duplicates.items():
        preparation[cohort]["cross_cohort_duplicates_removed"] = count
        preparation[cohort]["selected_after_global_dedup"] = preparation[cohort]["selected"] - count
    for cohort in preparation:
        preparation[cohort].setdefault("cross_cohort_duplicates_removed", 0)
        preparation[cohort].setdefault("selected_after_global_dedup", preparation[cohort]["selected"])

    prepared_path = args.output_dir / "prepared.jsonl.gz"
    with gzip.open(prepared_path, "wt", encoding="utf-8") as handle:
        for row in deduplicated:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    metadata = {
        "model": str(Path(args.model).resolve()),
        "prefix_tokens": PREFIX_TOKENS,
        "target_tokens": TARGET_TOKENS,
        "samples_per_cohort": args.samples_per_cohort,
        "candidate_multiplier": args.candidate_multiplier,
        "seed": args.seed,
        "categories": args.categories,
        "protocol_id": PROTOCOL_ID,
        "prepared_examples": len(deduplicated),
        "generation_requests": len(deduplicated) * 2,
        "cohorts": preparation,
    }
    (args.output_dir / "preparation.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2), flush=True)
    print(f"wrote {prepared_path}", flush=True)


def prepare_exhaustive(args: argparse.Namespace) -> None:
    """Stream every remaining unique eligible source without retaining it in RAM."""
    from transformers import AutoTokenizer

    args.output_dir.mkdir(parents=True, exist_ok=True)
    exclude_hashes: set[str] = set()
    for path in args.exclude_prepared:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            exclude_hashes.update(json.loads(line)["content_hash"] for line in handle)

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    seen_hashes: set[str] = set(exclude_hashes)
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    pending: list[tuple[SourceRow, str, int]] = []
    output_path = args.output_dir / "prepared_exhaustive_remaining.jsonl.gz"
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")

    def flush(handle: Any) -> None:
        if not pending:
            return
        encoded = tokenizer(
            [row.text for row, _, _ in pending],
            add_special_tokens=False,
            return_attention_mask=False,
        )["input_ids"]
        for (row, content_hash, rank), token_ids in zip(pending, encoded, strict=True):
            if len(token_ids) < PREFIX_TOKENS + TARGET_TOKENS:
                counters[row.cohort]["short"] += 1
                continue
            counters[row.cohort]["eligible_written"] += 1
            payload = {
                "cohort": row.cohort,
                "source_id": row.source_id,
                "title": row.title,
                "url": row.url,
                "source_path": row.source_path,
                "content_hash": content_hash,
                "rank": rank,
                "prefix_token_ids": token_ids[:PREFIX_TOKENS],
                "target_token_ids": token_ids[PREFIX_TOKENS : PREFIX_TOKENS + TARGET_TOKENS],
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        pending.clear()

    with gzip.open(temporary_path, "wt", encoding="utf-8") as handle:
        for row in selected_rows(args.categories):
            counters[row.cohort]["scanned"] += 1
            canonical = normalized_text(row.text)
            content_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if content_hash in seen_hashes:
                key = "excluded_sample" if content_hash in exclude_hashes else "duplicate"
                counters[row.cohort][key] += 1
                continue
            seen_hashes.add(content_hash)
            candidate = make_candidate(row, args.seed)
            pending.append((row, content_hash, candidate.rank))
            if len(pending) >= args.tokenizer_batch_size:
                flush(handle)
            total = sum(item["scanned"] for item in counters.values())
            if total and total % 1_000_000 == 0:
                print(f"exhaustive scan {total:,} rows", flush=True)
        flush(handle)
    temporary_path.replace(output_path)
    metadata = {
        "model": str(Path(args.model).resolve()),
        "protocol_id": PROTOCOL_ID,
        "categories": args.categories,
        "prefix_tokens": PREFIX_TOKENS,
        "target_tokens": TARGET_TOKENS,
        "seed": args.seed,
        "excluded_prepared_files": [str(path.resolve()) for path in args.exclude_prepared],
        "excluded_content_hashes": len(exclude_hashes),
        "cohorts": {cohort: dict(values) for cohort, values in sorted(counters.items())},
    }
    (args.output_dir / "preparation_exhaustive_remaining.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2), flush=True)
    print(f"wrote {output_path}", flush=True)


def render_chat_header(template_path: Path, tokenizer: Any) -> list[int]:
    import jinja2

    template = jinja2.Environment().from_string(template_path.read_text(encoding="utf-8"))
    rendered = template.render(
        messages=[
            {
                "role": "user",
                "content": (
                    "Continue the following text verbatim in its original language. "
                    "Output only the continuation, without explanation or repetition."
                ),
            }
        ],
        tools=None,
        add_generation_prompt=True,
        enable_thinking=False,
        bos_token=tokenizer.bos_token or "",
        eos_token=tokenizer.eos_token or "",
    )
    return tokenizer(rendered, add_special_tokens=False, return_attention_mask=False)["input_ids"]


def longest_common_prefix(expected: list[int], actual: list[int]) -> int:
    for index, (left, right) in enumerate(zip(expected, actual, strict=False)):
        if left != right:
            return index
    return min(len(expected), len(actual))


def request_key(model: Path, content_hash: str, mode: str) -> str:
    identity = f"{PROTOCOL_ID}\0{model.resolve()}\0{content_hash}\0{mode}"
    return hashlib.sha256(identity.encode()).hexdigest()


def load_completed_request_keys(paths: list[Path], model: Path) -> set[str]:
    completed: set[str] = set()
    for root in paths:
        candidates = [root] if root.is_file() else sorted(root.rglob("results*.jsonl.gz"))
        for path in candidates:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                for line in handle:
                    row = json.loads(line)
                    key = row.get("request_key")
                    if key:
                        completed.add(str(key))
                    elif row.get("content_hash") and row.get("mode"):
                        completed.add(request_key(model, row["content_hash"], row["mode"]))
    return completed


def run_shard(args: argparse.Namespace) -> None:
    os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams
    from vllm.inputs import TokensPrompt

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if tokenizer.bos_token_id is None:
        raise RuntimeError("export tokenizer has no BOS token")
    chat_header = render_chat_header(args.chat_template, tokenizer)

    prepared_file = args.prepared_file or (args.output_dir / "prepared.jsonl.gz")
    examples = []
    with gzip.open(prepared_file, "rt", encoding="utf-8") as handle:
        for ordinal, line in enumerate(handle):
            if ordinal % args.num_shards == args.shard_index:
                examples.append(json.loads(line))

    completed_keys = load_completed_request_keys(args.skip_results, Path(args.model))
    requests = []
    for example in examples:
        prefix = [int(token) for token in example["prefix_token_ids"]]
        if request_key(Path(args.model), example["content_hash"], "raw") not in completed_keys:
            requests.append(("raw", example, [tokenizer.bos_token_id, *prefix]))
        if request_key(Path(args.model), example["content_hash"], "assistant_prefill") not in completed_keys:
            requests.append(("assistant_prefill", example, [*chat_header, *prefix]))

    result_path = args.output_dir / f"{args.result_prefix}_shard_{args.shard_index:02d}_of_{args.num_shards:02d}.jsonl.gz"
    if not requests:
        with gzip.open(result_path, "wt", encoding="utf-8"):
            pass
        print(f"all requests already completed; wrote {result_path}", flush=True)
        return

    llm = LLM(
        model=str(args.model),
        dtype="bfloat16",
        max_model_len=args.max_model_len,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_num_seqs=args.max_num_seqs,
        max_num_batched_tokens=args.max_num_batched_tokens,
        disable_log_stats=not args.log_stats,
        enforce_eager=True,
        trust_remote_code=False,
        attention_backend="FLASH_ATTN",
    )
    params = SamplingParams(temperature=0.0, max_tokens=TARGET_TOKENS, skip_special_tokens=False)
    completed = 0
    temporary_path = result_path.with_suffix(result_path.suffix + ".tmp")
    with gzip.open(temporary_path, "wt", encoding="utf-8") as handle:
        for start in range(0, len(requests), args.batch_size):
            batch = requests[start : start + args.batch_size]
            outputs = llm.generate(
                [TokensPrompt(prompt_token_ids=item[2]) for item in batch],
                params,
                use_tqdm=False,
            )
            for (mode, example, prompt_ids), output in zip(batch, outputs, strict=True):
                target = [int(token) for token in example["target_token_ids"]]
                generated = [int(token) for token in output.outputs[0].token_ids]
                lcp = longest_common_prefix(target, generated)
                aligned = sum(left == right for left, right in zip(target, generated, strict=False))
                row = {
                    **{key: value for key, value in example.items() if not key.endswith("_token_ids")},
                    "mode": mode,
                    "protocol_id": PROTOCOL_ID,
                    "request_key": request_key(Path(args.model), example["content_hash"], mode),
                    "prefix_tokens": PREFIX_TOKENS,
                    "target_tokens": TARGET_TOKENS,
                    "matching_prefix_tokens": lcp,
                    "aligned_token_accuracy": aligned / TARGET_TOKENS,
                    "exact_target": len(generated) >= TARGET_TOKENS and generated[:TARGET_TOKENS] == target,
                    "generated_token_count": len(generated),
                    "source_prefix": tokenizer.decode(example["prefix_token_ids"], skip_special_tokens=False),
                    "reference_continuation": tokenizer.decode(target, skip_special_tokens=False),
                    "generated_continuation": tokenizer.decode(generated, skip_special_tokens=False),
                    "reference_token_ids": target,
                    "generated_token_ids": generated,
                }
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            completed += len(batch)
            print(f"shard {args.shard_index}: completion={completed}/{len(requests)}", flush=True)
    temporary_path.replace(result_path)
    print(f"wrote {result_path}", flush=True)


def percentile(values: list[int], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = fraction * (len(ordered) - 1)
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def metric_row(group: list[dict[str, Any]]) -> dict[str, Any]:
    lcps = [int(row["matching_prefix_tokens"]) for row in group]
    return {
        "n": len(group),
        "exact_64": sum(bool(row["exact_target"]) for row in group),
        "exact_64_rate": sum(bool(row["exact_target"]) for row in group) / len(group),
        "mean_lcp": statistics.fmean(lcps),
        "median_lcp": statistics.median(lcps),
        "p95_lcp": percentile(lcps, 0.95),
        "p99_lcp": percentile(lcps, 0.99),
        "p999_lcp": percentile(lcps, 0.999),
        "max_lcp": max(lcps),
        "at_least_10": sum(value >= 10 for value in lcps),
        "at_least_20": sum(value >= 20 for value in lcps),
        "at_least_50": sum(value >= 50 for value in lcps),
        "mean_aligned_accuracy": statistics.fmean(float(row["aligned_token_accuracy"]) for row in group),
    }


def merge(args: argparse.Namespace) -> None:
    paths = sorted(args.output_dir.glob("results*_shard_*_of_*.jsonl.gz"))
    if not paths:
        raise RuntimeError("no shard results found")
    rows = []
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle)

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    categories: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    modes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["cohort"], row["mode"])].append(row)
        categories[(row["cohort"].split("-", 1)[0], row["mode"])].append(row)
        modes[row["mode"]].append(row)
    summary = {
        "overall": {mode: metric_row(group) for mode, group in sorted(modes.items())},
        "categories": {
            f"{category}/{mode}": metric_row(group)
            for (category, mode), group in sorted(categories.items())
        },
        "cohorts": {
            f"{cohort}/{mode}": metric_row(group)
            for (cohort, mode), group in sorted(groups.items())
        },
        "shard_files": len(paths),
        "result_rows": len(rows),
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    high_matches = sorted(rows, key=lambda row: int(row["matching_prefix_tokens"]), reverse=True)[:100]
    with (args.output_dir / "top_matches.jsonl").open("w", encoding="utf-8") as handle:
        for row in high_matches:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    lines = [
        "# DFM9 Category A/B Prefix-Extraction Probe",
        "",
        f"- Model: `{Path(args.model).resolve()}`",
        "- Prefix: 64 original-source tokens",
        "- Generation/reference: at most 64 tokens, greedy",
        "- Modes: raw causal continuation and Gemma-chat assistant prefill",
        "- Sampling: deterministic content-hash sample of up to 10,000 eligible unique texts per cohort; smaller cohorts exhaustive within the available source",
        "",
        "| Cohort | Mode | N | Exact 64 | >=10 | >=20 | >=50 | Mean LCP | P95 | P99 | P99.9 | Max |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, metrics in summary["cohorts"].items():
        cohort, mode = key.split("/", 1)
        lines.append(
            f"| {cohort} | {mode} | {metrics['n']:,} | {metrics['exact_64']} "
            f"({metrics['exact_64_rate']:.3%}) | {metrics['at_least_10']} | "
            f"{metrics['at_least_20']} | {metrics['at_least_50']} | {metrics['mean_lcp']:.2f} | "
            f"{metrics['p95_lcp']:.1f} | {metrics['p99_lcp']:.1f} | {metrics['p999_lcp']:.1f} | {metrics['max_lcp']} |"
        )
    lines.extend(["", "## Overall", ""])
    for key, metrics in summary["categories"].items():
        lines.append(
            f"- Category `{key}`: N={metrics['n']:,}; exact-64={metrics['exact_64']} "
            f"({metrics['exact_64_rate']:.3%}); mean LCP={metrics['mean_lcp']:.2f}; "
            f"P99={metrics['p99_lcp']:.1f}; max={metrics['max_lcp']}."
        )
    lines.append("")
    for mode, metrics in summary["overall"].items():
        lines.append(
            f"- `{mode}`: N={metrics['n']:,}; exact-64={metrics['exact_64']} "
            f"({metrics['exact_64_rate']:.3%}); mean LCP={metrics['mean_lcp']:.2f}; "
            f"P99={metrics['p99_lcp']:.1f}; max={metrics['max_lcp']}."
        )
    lines.extend(
        [
            "",
            "Long exact spans can indicate extractable verbatim recall, but formulaic, duplicated, or highly constrained text must be adjudicated separately. `top_matches.jsonl` retains the 100 longest matches for that review.",
            "",
        ]
    )
    (args.output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    prepare_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    prepare_parser.add_argument("--samples-per-cohort", type=int, default=10_000)
    prepare_parser.add_argument("--candidate-multiplier", type=int, default=20)
    prepare_parser.add_argument("--tokenizer-batch-size", type=int, default=4096)
    prepare_parser.add_argument("--seed", type=int, default=1_650_000)
    prepare_parser.add_argument("--categories", default="A")
    prepare_parser.add_argument("--workers", type=int, default=1)
    prepare_parser.set_defaults(handler=prepare)

    exhaustive_parser = subparsers.add_parser("prepare-exhaustive")
    exhaustive_parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    exhaustive_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    exhaustive_parser.add_argument("--exclude-prepared", type=Path, action="append", default=[])
    exhaustive_parser.add_argument("--tokenizer-batch-size", type=int, default=4096)
    exhaustive_parser.add_argument("--seed", type=int, default=1_650_000)
    exhaustive_parser.add_argument("--categories", default="A")
    exhaustive_parser.set_defaults(handler=prepare_exhaustive)

    run_parser = subparsers.add_parser("run-shard")
    run_parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    run_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    run_parser.add_argument("--prepared-file", type=Path)
    run_parser.add_argument("--skip-results", type=Path, action="append", default=[])
    run_parser.add_argument("--result-prefix", default="results")
    run_parser.add_argument("--chat-template", type=Path, default=DEFAULT_TEMPLATE)
    run_parser.add_argument("--num-shards", type=int, default=8)
    run_parser.add_argument("--shard-index", type=int, required=True)
    run_parser.add_argument("--gpu-memory-utilization", type=float, default=0.12)
    run_parser.add_argument("--max-model-len", type=int, default=4096)
    run_parser.add_argument("--max-num-seqs", type=int, default=256)
    run_parser.add_argument("--max-num-batched-tokens", type=int, default=65_536)
    run_parser.add_argument("--log-stats", action="store_true")
    run_parser.add_argument("--batch-size", type=int, default=128)
    run_parser.set_defaults(handler=run_shard)

    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    merge_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    merge_parser.set_defaults(handler=merge)
    return root


def main() -> None:
    args = parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
