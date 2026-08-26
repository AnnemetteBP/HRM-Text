#!/usr/bin/env python3
"""Convert approved Alexandra Institute DFM10 train splits to chat JSONL."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
import zipfile
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


DANE_URL = "https://danlp-downloads.alexandra.dk/datasets/ddt.zip"
DANE_LABELS = ("PER", "ORG", "LOC", "MISC")
MULTI_ZEBRA_CONFIGS = (
    "dataset_da_huse_2x3_5rh",
    "dataset_da_huse_4x5_5rh",
    "dataset_da_smoerrebroed_2x3_5rh",
    "dataset_da_smoerrebroed_4x5_5rh",
    "dataset_en_houses_2x3_5rh",
    "dataset_en_houses_4x5_5rh",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--download-dir", type=Path, default=Path("data/downloads/datasets")
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/dfm10_alexandra_sources")
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def chat_row(
    *, source: str, source_id: str, user: str, assistant: str
) -> dict[str, Any]:
    if not user.strip() or not assistant.strip():
        raise ValueError(f"{source}:{source_id}: empty chat content")
    return {
        "messages": [
            {"role": "user", "content": user.strip()},
            {"role": "assistant", "content": assistant.strip()},
        ],
        "source": source,
        "source_id": source_id,
        "split": "train",
    }


def parquet_rows(path: Path) -> Iterator[dict[str, Any]]:
    for batch in pq.ParquetFile(path).iter_batches(batch_size=2048):
        yield from batch.to_pylist()


def nordjylland_rows(path: Path) -> Iterator[dict[str, Any]]:
    for index, row in enumerate(parquet_rows(path)):
        yield chat_row(
            source="alexandrainst/nordjylland-news-summarization",
            source_id=str(index),
            user=(
                "Skriv et kort og præcist resumé af følgende danske nyhedsartikel. "
                "Medtag kun oplysninger, der fremgår af artiklen.\n\n"
                f"Artikel:\n{row['text']}"
            ),
            assistant=str(row["summary"]),
        )


def scandi_qa_rows(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            has_answer = bool(row.get("has_answer"))
            answer = str(row.get("answer") or "").strip()
            if has_answer and not answer:
                raise ValueError(f"{path}:{line_number}: answerable row has no answer")
            target = answer if has_answer else "Kan ikke besvares ud fra konteksten."
            yield chat_row(
                source="alexandrainst/scandi-qa",
                source_id=str(row.get("id", line_number)),
                user=(
                    "Besvar spørgsmålet kort ud fra den givne kontekst. Hvis svaret "
                    "ikke fremgår af konteksten, svar præcis: \"Kan ikke besvares ud "
                    "fra konteksten.\"\n\n"
                    f"Kontekst:\n{row['context']}\n\nSpørgsmål:\n{row['question']}"
                ),
                assistant=target,
            )


def multi_zebra_rows(path: Path, config: str) -> Iterator[dict[str, Any]]:
    for index, row in enumerate(parquet_rows(path)):
        clues = "\n".join(str(clue) for clue in row["clues"])
        prompt = "\n\n".join(
            part.strip()
            for part in (
                str(row["introduction"]),
                clues,
                str(row["question"]),
                str(row["format_instructions"]),
                str(row["format_example"]),
            )
            if part.strip()
        )
        target = json.dumps(
            row["solution"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        yield chat_row(
            source=f"alexandrainst/multi-zebra-logic/{config}",
            source_id=str(index),
            user=prompt,
            assistant=target,
        )


def extract_bio_entities(tokens: list[str], tags: list[str]) -> dict[str, list[str]]:
    if len(tokens) != len(tags):
        raise ValueError("DaNE token/tag lengths differ")
    entities = {label: [] for label in DANE_LABELS}
    active_label: str | None = None
    active_tokens: list[str] = []

    def flush() -> None:
        nonlocal active_label, active_tokens
        if active_label is not None and active_tokens:
            entities[active_label].append(" ".join(active_tokens))
        active_label = None
        active_tokens = []

    for token, tag in zip(tokens, tags, strict=True):
        if tag == "O" or "-" not in tag:
            flush()
            continue
        prefix, label = tag.split("-", 1)
        if label not in entities:
            raise ValueError(f"unsupported DaNE label: {label}")
        if prefix == "B" or label != active_label:
            flush()
            active_label = label
        elif prefix != "I":
            raise ValueError(f"unsupported BIO prefix: {prefix}")
        active_tokens.append(token)
    flush()
    return entities


def parse_dane_train(path: Path) -> Iterator[dict[str, Any]]:
    sent_id = ""
    text = ""
    tokens: list[str] = []
    tags: list[str] = []

    def emit() -> dict[str, Any] | None:
        if not tokens:
            return None
        entities = extract_bio_entities(tokens, tags)
        return chat_row(
            source="alexandrainst/dane",
            source_id=sent_id,
            user=(
                "Find alle navngivne entiteter i teksten. Returnér kun et JSON-objekt "
                "med nøglerne \"PER\", \"ORG\", \"LOC\" og \"MISC\". Hver værdi "
                "skal være en liste af entiteternes ordrette tekst i den rækkefølge, "
                f"de forekommer. Brug en tom liste, hvis typen ikke findes.\n\nTekst:\n{text}"
            ),
            assistant=json.dumps(
                entities, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        )

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if line.startswith("# sent_id = "):
                sent_id = line.removeprefix("# sent_id = ").strip()
            elif line.startswith("# text = "):
                text = line.removeprefix("# text = ").strip()
            elif not line:
                row = emit()
                if row is not None:
                    yield row
                sent_id, text, tokens, tags = "", "", [], []
            elif not line.startswith("#"):
                fields = line.split("\t")
                if len(fields) != 10 or not fields[0].isdigit():
                    continue
                tokens.append(fields[1])
                tags.append(fields[9].replace("name=", "").split("|", 1)[0])
    row = emit()
    if row is not None:
        yield row


def contiguous_mentions(tokens: list[str], indices: list[int]) -> list[str]:
    if not indices:
        return []
    ordered = sorted(set(int(index) for index in indices))
    if ordered[0] < 0 or ordered[-1] >= len(tokens):
        raise ValueError("DaCoref cluster index outside token sequence")
    mentions: list[str] = []
    start = previous = ordered[0]
    for index in ordered[1:]:
        if index != previous + 1:
            mentions.append(" ".join(tokens[start : previous + 1]))
            start = index
        previous = index
    mentions.append(" ".join(tokens[start : previous + 1]))
    return mentions


def dacoref_rows(path: Path) -> Iterator[dict[str, Any]]:
    for row in parquet_rows(path):
        clusters = [contiguous_mentions(row["tokens"], cluster) for cluster in row["clusters"]]
        yield chat_row(
            source="alexandrainst/dacoref",
            source_id=str(row["sent_id"]),
            user=(
                "Find koreferencer i teksten. Returnér kun et JSON-objekt med nøglen "
                "\"clusters\". Værdien skal være en liste af klynger, hvor hver klynge "
                "er en liste af de ordrette omtaler i den rækkefølge, de forekommer.\n\n"
                f"Tekst:\n{row['text']}"
            ),
            assistant=json.dumps(
                {"clusters": clusters},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )


def ensure_dane_archive(dataset_dir: Path) -> Path:
    archive = dataset_dir / "ddt.zip"
    if archive.is_file():
        return archive
    dataset_dir.mkdir(parents=True, exist_ok=True)
    temporary = archive.with_suffix(".zip.partial")
    request = urllib.request.Request(DANE_URL, headers={"User-Agent": "HRM-Text-DFM10/1"})
    with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as output:
        shutil.copyfileobj(response, output)
    temporary.replace(archive)
    return archive


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def main() -> None:
    args = parse_args()
    if args.output_dir.exists():
        if not args.force:
            raise FileExistsError(f"{args.output_dir} exists; pass --force to rebuild")
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True)

    nord = args.download_dir / "alexandra_nordjylland_news/data/train-00000-of-00001-4fb110c0f6314175.parquet"
    scandi = args.download_dir / "alexandra_scandi_qa/data/da/train.jsonl"
    zebra_root = args.download_dir / "alexandra_multi_zebra_logic"
    dacoref = args.download_dir / "alexandra_dacoref/data/train-00000-of-00001-ffdeed5775622c14.parquet"
    required = [nord, scandi, dacoref] + [
        zebra_root / config / "train-00000-of-00001.parquet"
        for config in MULTI_ZEBRA_CONFIGS
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing downloaded DFM10 sources:\n" + "\n".join(missing))

    files: dict[str, tuple[Path, Iterable[dict[str, Any]]]] = {
        "alexandra_nordjylland_original__train.jsonl": (nord, nordjylland_rows(nord)),
        "alexandra_scandi_qa_da__train.jsonl": (scandi, scandi_qa_rows(scandi)),
        "alexandra_dacoref__train.jsonl": (dacoref, dacoref_rows(dacoref)),
    }
    for config in MULTI_ZEBRA_CONFIGS:
        source = zebra_root / config / "train-00000-of-00001.parquet"
        files[f"alexandra_multi_zebra__{config}.jsonl"] = (
            source,
            multi_zebra_rows(source, config),
        )

    archive = ensure_dane_archive(args.download_dir / "alexandra_dane")
    extracted = args.download_dir / "alexandra_dane/ddt.train.conllu"
    with zipfile.ZipFile(archive) as zipped, zipped.open("ddt.train.conllu") as source, extracted.open("wb") as output:
        shutil.copyfileobj(source, output)
    files["alexandra_dane__train.jsonl"] = (extracted, parse_dane_train(extracted))

    manifest_files: dict[str, Any] = {}
    for filename, (source, rows) in files.items():
        output = args.output_dir / filename
        count = write_jsonl(output, rows)
        manifest_files[filename] = {
            "rows": count,
            "source": str(source.resolve()),
            "source_sha256": sha256(source),
        }
    manifest = {
        "split_policy": (
            "Only train rows are converted. HF validation/test artifacts are not "
            "downloaded; the upstream DaNE ddt.zip contains all splits, but only "
            "ddt.train.conllu is extracted into the source directory and converted."
        ),
        "files": manifest_files,
        "total_rows": sum(item["rows"] for item in manifest_files.values()),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
