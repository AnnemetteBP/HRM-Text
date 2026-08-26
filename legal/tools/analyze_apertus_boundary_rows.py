#!/usr/bin/env python3
"""Reproduce row-level LongAlign and EuroBlocks boundary summaries."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.dataset as ds


LONGALIGN_GROUPS = {
    "public-domain/library": ["project gutenberg", "public domain", "hathitrust", "internet archive"],
    "books/literary/publisher": [
        "copyright page", "isbn", "ebook", "chapter i", "chapter 1", "chapter one",
        "table of contents", "all rights reserved", "publisher", "printed in the",
    ],
    "government/legal/procurement": [
        "government of", "ministry of", "department of", "constitution", "public law",
        "regulation", "tender", "procurement", "bidder", "招标", "投标", "政府", "采购",
        "中华人民共和国", "标准（", "报告书",
    ],
    "scholarly/research": [
        "abstract", "introduction", "references", "doi", "arxiv", "et al.", "journal of",
        "research was supported", "研究报告",
    ],
    "software/code/technical-QA": [
        "// language:", "<!--language:", "#include <", "#include \"", "package ",
        "public class", "q:", "stackoverflow", "stack overflow", "github.com", "```",
        "function(", "const ",
    ],
    "manual/technical documentation": [
        "user's guide", "user’s guide", "installation guide", "reference manual",
        "operator manual", "deployment guide", "manual", "configuration guide",
        "api reference", "手册", "使用指南", "技术文档", "目录第一章",
    ],
    "encyclopedia/reference": [
        "category:", "categoria:", "externí odkazy", "references extern", "encyclop",
        "wikipedia", "coordinates:", "行政区划", "历史沿革",
    ],
    "education/course/textbook": [
        "course disclaimer", "course objectives", "lesson plan", "curriculum", "textbook",
        "workbook", "课程标准", "教材", "chapter review",
    ],
    "corporate/financial/ESG": [
        "annual report", "esg report", "environmental, social and governance",
        "financial statements", "shareholder", "banking", "corporation", "公司", "银行",
        "年度报告", "社会及治理报告",
    ],
    "news/blog/general web": [
        "posted on", "originally published", "blog", "上一篇", "下一篇", "转载", "author:",
        "原文地址", "news", "press release",
    ],
}

COPYRIGHT_MARKERS = re.compile(r"copyright|all rights reserved|©|版权所有|著作权", re.I)
URL_RE = re.compile(
    r"(?:https?://|www\.)(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,63}",
    re.I,
)
DOCUMENT_RE = re.compile(r"<document>\s*(.*?)\s*</document>", re.I | re.S)

PUBLIC_DOMAIN_RE = re.compile(
    r"project gutenberg|public domain|copyright (?:has )?expired|not protected by copyright",
    re.I,
)
OPEN_LICENCE_RE = re.compile(
    r"creative commons|cc[- ]by|apache(?: software)? licen[cs]e|mit licen[cs]e|"
    r"gnu (?:general public|free documentation) licen[cs]e|licensed under",
    re.I,
)
RESTRICTIVE_RE = re.compile(
    r"all rights reserved|no part.{0,160}(?:reproduced|transmitted|copied)|"
    r"without (?:the )?(?:prior )?written permission|may not be (?:reproduced|copied|distributed)|"
    r"permission (?:is )?required|版权所有|未经.{0,80}(?:许可|授权).{0,80}不得",
    re.I | re.S,
)
GOVERNMENT_NOTICE_RE = re.compile(r"crown copyright|government copyright|©\s*(?:the )?government", re.I)


def classify_longalign(text: str) -> tuple[str, bool]:
    sample = text[:120_000].lower()
    scores = {
        group: sum(3 if 0 <= sample.find(term) < 2_000 else 1 if term in sample else 0 for term in terms)
        for group, terms in LONGALIGN_GROUPS.items()
    }
    top = max(scores.values())
    if not top:
        return "unclassified/mixed", False
    winners = [group for group, score in scores.items() if score == top]
    return winners[0], len(winners) > 1


def marker_profile(text: str) -> dict[str, object]:
    public_domain = bool(PUBLIC_DOMAIN_RE.search(text))
    open_licence = bool(OPEN_LICENCE_RE.search(text))
    restrictive = bool(RESTRICTIVE_RE.search(text))
    government = bool(GOVERNMENT_NOTICE_RE.search(text))
    copyright_marker = bool(COPYRIGHT_MARKERS.search(text))
    positive = public_domain or open_licence
    if restrictive and positive:
        stratum = "mixed_restrictive_and_open_or_public"
    elif restrictive:
        stratum = "explicit_restrictive_notice"
    elif public_domain:
        stratum = "explicit_public_domain_marker"
    elif open_licence:
        stratum = "explicit_open_licence_marker"
    elif government:
        stratum = "government_copyright_notice"
    elif copyright_marker:
        stratum = "generic_copyright_or_bibliographic_marker"
    else:
        stratum = "no_explicit_marker"
    return {
        "marker_stratum": stratum,
        "restrictive_notice": restrictive,
        "open_licence_marker": open_licence,
        "public_domain_marker": public_domain,
        "government_copyright_marker": government,
        "copyright_marker": copyright_marker,
    }


def script_group(text: str) -> str:
    sample = text[:100_000]
    letters = sum(ch.isalpha() for ch in sample) or 1
    scripts = {
        "han": sum("\u4e00" <= ch <= "\u9fff" for ch in sample),
        "cyrillic": sum("\u0400" <= ch <= "\u04ff" for ch in sample),
        "arabic": sum("\u0600" <= ch <= "\u06ff" for ch in sample),
    }
    name, count = max(scripts.items(), key=lambda item: item[1])
    return name if count / letters >= 0.1 else "latin_or_other"


def domains(text: str) -> str:
    values: set[str] = set()
    for match in URL_RE.findall(text):
        value = re.sub(r"^https?://", "", match, flags=re.I)
        value = re.sub(r"^www\.", "", value, flags=re.I)
        host = value.rstrip(".,;:")
        if host and "." in host:
            values.add(host.lower())
    return ";".join(sorted(values))


def normalize_document(text: str) -> str:
    return " ".join(text.split())


def summarize_longalign(path: Path) -> list[dict[str, object]]:
    counts: Counter[str] = Counter()
    lengths: dict[str, list[int]] = defaultdict(list)
    copyright_counts: Counter[str] = Counter()
    ties: Counter[str] = Counter()
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            prompt = row["messages"][0]["content"]
            group, tied = classify_longalign(prompt)
            counts[group] += 1
            lengths[group].append(len(prompt))
            copyright_counts[group] += bool(COPYRIGHT_MARKERS.search(prompt))
            ties[group] += tied
    total = sum(counts.values())
    return [
        {
            "group": group,
            "rows": count,
            "share_percent": round(100 * count / total, 3),
            "median_prompt_chars": int(statistics.median(lengths[group])),
            "explicit_copyright_marker_rows": copyright_counts[group],
            "tied_top_score_rows": ties[group],
        }
        for group, count in counts.most_common()
    ]


def summarize_euroblocks(path: Path) -> list[dict[str, object]]:
    table = ds.dataset(path, format="parquet").to_table(columns=["dataset", "language"])
    counts = Counter(table["dataset"].to_pylist())
    return [{"subset": subset, "rows": rows} for subset, rows in counts.most_common()]


def longalign_marker_rows(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open() as handle:
        for source_offset, line in enumerate(handle):
            row = json.loads(line)
            prompt = row["messages"][0]["content"]
            profile = marker_profile(prompt)
            if not profile["copyright_marker"]:
                continue
            first_marker = COPYRIGHT_MARKERS.search(prompt)
            group, tied = classify_longalign(prompt)
            rows.append(
                {
                    "source_offset": source_offset,
                    "source_id": row.get("id", ""),
                    "content_group": group,
                    **profile,
                    "first_marker_offset": first_marker.start(),
                    "marker_within_initial_120k": first_marker.start() < 120_000,
                    "classification_tied": tied,
                    "script_group": script_group(prompt),
                    "prompt_chars": len(prompt),
                    "domains": domains(prompt),
                }
            )
    return rows


def euroblocks_seed_documents(path: Path) -> list[dict[str, object]]:
    dataset = ds.dataset(path, format="parquet")
    wanted = ["instruction-generation", "instruction-generation-ifeval"]
    table = dataset.to_table(
        filter=ds.field("dataset").isin(wanted),
        columns=["conversations", "dataset", "language"],
    )
    grouped: dict[str, dict[str, object]] = {}
    missing = 0
    for row in table.to_pylist():
        prompt = row["conversations"][0]["value"]
        match = DOCUMENT_RE.search(prompt)
        if not match:
            missing += 1
            continue
        document = match.group(1).strip()
        normalized = normalize_document(document)
        digest = hashlib.sha256(normalized.encode()).hexdigest()
        if digest not in grouped:
            group, tied = classify_longalign(document)
            grouped[digest] = {
                "document_sha256": digest,
                "occurrences": 0,
                "instruction_generation_rows": 0,
                "instruction_generation_ifeval_rows": 0,
                "languages": set(),
                "document_chars": len(document),
                "content_group": group,
                **marker_profile(document),
                "classification_tied": tied,
                "script_group": script_group(document),
                "domains": domains(document),
            }
        item = grouped[digest]
        item["occurrences"] += 1
        key = row["dataset"].replace("-", "_") + "_rows"
        item[key] += 1
        item["languages"].add(row["language"] or "")
    if missing:
        raise RuntimeError(f"{missing} source-retaining rows lacked a <document> block")
    rows = []
    for item in grouped.values():
        item["languages"] = ";".join(sorted(item["languages"]))
        rows.append(item)
    return sorted(rows, key=lambda item: (-item["occurrences"], item["document_sha256"]))


def write_csv(rows: list[dict[str, object]], output: Path | None = None) -> None:
    handle = output.open("w", newline="") if output else sys.stdout
    try:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if output:
            handle.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    longalign = subparsers.add_parser("longalign")
    longalign.add_argument("jsonl", type=Path)
    euroblocks = subparsers.add_parser("euroblocks")
    euroblocks.add_argument("parquet_path", type=Path)
    longalign_markers = subparsers.add_parser("longalign-markers")
    longalign_markers.add_argument("jsonl", type=Path)
    longalign_markers.add_argument("--output", type=Path)
    euroblocks_seeds = subparsers.add_parser("euroblocks-seeds")
    euroblocks_seeds.add_argument("parquet_path", type=Path)
    euroblocks_seeds.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "longalign":
        write_csv(summarize_longalign(args.jsonl))
    elif args.command == "euroblocks":
        write_csv(summarize_euroblocks(args.parquet_path))
    elif args.command == "longalign-markers":
        write_csv(longalign_marker_rows(args.jsonl), args.output)
    else:
        write_csv(euroblocks_seed_documents(args.parquet_path), args.output)


if __name__ == "__main__":
    main()
