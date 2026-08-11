#!/usr/bin/env python3
"""Split oversized OKF concepts into indexed section concepts."""

from __future__ import annotations

import argparse
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LINK_RE = re.compile(r"(!?\[[^\]]*\]\()([^)]+)(\))")
TYPE_MAP = {
    "Operational Journal": "Operational Record",
    "Software Catalog": "Software Reference",
    "Policy": "Policy Record",
    "Training Data Plan": "Plan Record",
    "Technical Reference": "Technical Reference",
    "Experiment Runbook": "Experiment Record",
}


@dataclass
class Section:
    title: str
    body: str
    slug: str = ""


def parse_concept(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if match is None:
        raise ValueError(f"{path}: missing frontmatter")
    metadata = yaml.safe_load(match.group(1))
    if not isinstance(metadata, dict):
        raise ValueError(f"{path}: frontmatter is not a mapping")
    return metadata, text[match.end() :]


def dump_concept(metadata: dict[str, Any], body: str) -> str:
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).rstrip()
    return f"---\n{frontmatter}\n---\n{body.rstrip()}\n"


def split_h2(body: str, raw_headings: bool = False) -> tuple[str, list[Section]]:
    lines = body.splitlines(keepends=True)
    starts: list[tuple[int, str]] = []
    fence: str | None = None
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        marker = stripped[:3]
        if not raw_headings and marker in {"```", "~~~"}:
            fence = None if fence == marker else marker if fence is None else fence
            continue
        if (raw_headings or fence is None) and line.startswith("## "):
            starts.append((index, line[3:].strip()))
    if not starts:
        return body, []
    preamble = "".join(lines[: starts[0][0]])
    sections = []
    for position, (start, title) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        sections.append(Section(title=title, body="".join(lines[start + 1 : end])))
    return preamble, sections


def slugify(value: str) -> str:
    value = re.sub(r"`|\*|_", "", value)
    value = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", value)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value[:96] or "section"


def assign_unique_slugs(sections: list[Section]) -> None:
    counts: dict[str, int] = {}
    for section in sections:
        base = slugify(section.title)
        counts[base] = counts.get(base, 0) + 1
        section.slug = base if counts[base] == 1 else f"{base}-{counts[base]}"


def chronology_title(paragraph: str) -> str:
    plain = " ".join(paragraph.split())
    plain = re.sub(r"[`*_]", "", plain)
    date_match = re.search(r"2026-\d{2}-\d{2}", plain)
    assert date_match is not None
    date = date_match.group(0)
    prefix = plain[: date_match.start()].strip(" ,:.-")
    generic = {
        "update",
        "updated",
        "runtime update",
        "operational update",
        "later update",
        "follow-up",
        "superseded",
        "correction",
    }
    if prefix.lower() not in generic and 3 <= len(prefix) <= 100:
        return f"{prefix} ({date})"
    remainder = re.sub(r"^.*?Confidence:\s*(?:high|medium|low)[^A-Za-z0-9]*", "", plain, flags=re.I)
    if remainder == plain:
        remainder = plain[date_match.end() :].lstrip(" .:-")
    words = remainder.split()
    detail = " ".join(words[:10]).rstrip(".,:;")
    label = prefix.title() if prefix else "Update"
    return f"{label} {date}: {detail}".rstrip(": ")


def split_chronology(body: str, all_dated_paragraphs: bool) -> tuple[str, list[Section], str]:
    generated_marker = "\nThe detailed sections of this collection are maintained as separate OKF concepts."
    marker_index = body.find(generated_marker)
    suffix = ""
    if marker_index >= 0:
        body, suffix = body[:marker_index], body[marker_index:]
    parts = re.split(r"(\n\s*\n)", body)
    paragraphs = ["".join(parts[index : index + 2]) for index in range(0, len(parts), 2)]
    starts: list[int] = []
    for index, paragraph in enumerate(paragraphs):
        plain = " ".join(paragraph.split())
        if not plain or len(plain) > 800 or not re.search(r"2026-\d{2}-\d{2}", plain):
            continue
        if plain.startswith(("```", "~~~", "|", "- ")) or re.match(r"^2026-\d{2}-\d{2}T", plain):
            continue
        if all_dated_paragraphs or re.search(r"Confidence:\s*(?:high|medium|low)", plain, re.I):
            starts.append(index)
    if len(starts) < 2:
        return body, [], suffix
    preamble = "".join(paragraphs[: starts[0]])
    sections: list[Section] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(paragraphs)
        section_body = "".join(paragraphs[start:end])
        sections.append(Section(title=chronology_title(paragraphs[start]), body=section_body))
    return preamble, sections, suffix


def shift_headings(body: str) -> str:
    output: list[str] = []
    fence: str | None = None
    for line in body.splitlines(keepends=True):
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in {"```", "~~~"}:
            fence = None if fence == marker else marker if fence is None else fence
            output.append(line)
            continue
        if fence is None:
            match = re.match(r"^(#{3,6})(\s+.*)$", line)
            if match:
                line = f"{match.group(1)[1:]}{match.group(2)}"
        output.append(line)
    return "".join(output)


def relocate_links(body: str, old_parent: Path, new_parent: Path) -> str:
    output: list[str] = []
    fence: str | None = None

    def replace(match: re.Match[str]) -> str:
        raw = match.group(2)
        target = raw.strip().split(maxsplit=1)[0].strip("<>")
        if not target or target.startswith(("/", "#", "mailto:")) or "://" in target:
            return match.group(0)
        path_part, separator, fragment = target.partition("#")
        source_target = (old_parent / path_part).resolve()
        if not source_target.exists():
            return match.group(0)
        relocated = os.path.relpath(source_target, new_parent)
        if path_part.endswith("/"):
            relocated += "/"
        if separator:
            relocated += f"#{fragment}"
        replacement = raw.replace(target, relocated, 1)
        return f"{match.group(1)}{replacement}{match.group(3)}"

    for line in body.splitlines(keepends=True):
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in {"```", "~~~"}:
            fence = None if fence == marker else marker if fence is None else fence
            output.append(line)
            continue
        output.append(LINK_RE.sub(replace, line) if fence is None else line)
    return "".join(output)


def split_concept(path: Path, bundle: Path, apply: bool, raw_headings: bool = False) -> int:
    metadata, body = parse_concept(path)
    preamble, sections = split_h2(body, raw_headings=raw_headings)
    if len(sections) < 2:
        return 0
    collection_dir = path.with_suffix("")
    if collection_dir.exists():
        raise FileExistsError(f"refusing to replace existing collection directory: {collection_dir}")
    assign_unique_slugs(sections)
    print(f"{path.relative_to(bundle)} -> {len(sections)} concepts in {collection_dir.name}/")
    if not apply:
        return len(sections)

    collection_dir.mkdir()
    parent_title = str(metadata.get("title") or path.stem.replace("-", " ").title())
    original_type = str(metadata.get("type", "Reference"))
    child_type = TYPE_MAP.get(original_type, original_type)
    parent_relative = "/" + path.relative_to(bundle).as_posix()

    index_lines = [f"# {parent_title} Concepts", ""]
    parent_lines = [preamble.rstrip(), "", "The detailed sections of this collection are maintained as separate OKF concepts.", ""]
    for section in sections:
        child_metadata: dict[str, Any] = {
            "type": child_type,
            "title": section.title,
            "description": f"Part of {parent_title}: {section.title}.",
            "tags": metadata.get("tags", []),
            "status": metadata.get("status", "stable"),
            "last_updated": metadata.get("last_updated"),
            "confidence": metadata.get("confidence"),
            "part_of": parent_relative,
        }
        child_metadata = {key: value for key, value in child_metadata.items() if value not in (None, [], "")}
        child_body = shift_headings(section.body)
        child_body = relocate_links(child_body, path.parent, collection_dir)
        child_body = (
            f"# {section.title}\n\n"
            f"Part of [{parent_title}]({parent_relative}).\n\n"
            f"{child_body.lstrip()}"
        )
        child_path = collection_dir / f"{section.slug}.md"
        child_path.write_text(dump_concept(child_metadata, child_body), encoding="utf-8")
        description = child_metadata["description"]
        index_lines.append(f"* [{section.title}]({section.slug}.md) - {description}")
        parent_lines.extend(
            [
                f"## {section.title}",
                "",
                f"[Open the dedicated concept]({collection_dir.name}/{section.slug}.md).",
                "",
            ]
        )

    (collection_dir / "index.md").write_text("\n".join(index_lines).rstrip() + "\n", encoding="utf-8")
    parent_metadata = dict(metadata)
    parent_metadata["type"] = "Knowledge Collection"
    parent_metadata["collection_type"] = original_type
    parent_metadata["last_updated"] = "2026-08-11"
    path.write_text(dump_concept(parent_metadata, "\n".join(parent_lines)), encoding="utf-8")
    return len(sections)


def split_chronology_concept(
    path: Path,
    bundle: Path,
    apply: bool,
    all_dated_paragraphs: bool,
) -> int:
    metadata, body = parse_concept(path)
    preamble, sections, suffix = split_chronology(body, all_dated_paragraphs)
    if len(sections) < 2:
        return 0
    collection_dir = path.with_suffix("")
    assign_unique_slugs(sections)
    for section in sections:
        section.slug = f"chronology-{section.slug}"
    print(f"{path.relative_to(bundle)} -> {len(sections)} chronological concepts in {collection_dir.name}/")
    if not apply:
        return len(sections)

    collection_dir.mkdir(exist_ok=True)
    parent_title = str(metadata.get("title") or path.stem.replace("-", " ").title())
    original_type = str(metadata.get("collection_type") or metadata.get("type", "Operational Journal"))
    child_type = TYPE_MAP.get(original_type, "Operational Record")
    parent_relative = "/" + path.relative_to(bundle).as_posix()
    index_path = collection_dir / "index.md"
    if index_path.exists():
        index_text = index_path.read_text(encoding="utf-8").rstrip() + "\n\n## Chronological Records\n\n"
    else:
        index_text = f"# {parent_title} Concepts\n\n"

    parent_lines = [preamble.rstrip(), "", "## Chronological Records", ""]
    for section in sections:
        child_metadata: dict[str, Any] = {
            "type": child_type,
            "title": section.title,
            "description": f"Chronological record from {parent_title}: {section.title}.",
            "tags": metadata.get("tags", []),
            "status": metadata.get("status", "stable"),
            "last_updated": metadata.get("last_updated"),
            "confidence": metadata.get("confidence"),
            "part_of": parent_relative,
        }
        child_metadata = {key: value for key, value in child_metadata.items() if value not in (None, [], "")}
        child_body = relocate_links(section.body, path.parent, collection_dir)
        child_body = (
            f"# {section.title}\n\n"
            f"Part of [{parent_title}]({parent_relative}).\n\n"
            f"{child_body.lstrip()}"
        )
        child_path = collection_dir / f"{section.slug}.md"
        if child_path.exists():
            raise FileExistsError(f"refusing to overwrite chronological concept: {child_path}")
        child_path.write_text(dump_concept(child_metadata, child_body), encoding="utf-8")
        index_text += f"* [{section.title}]({section.slug}.md) - {child_metadata['description']}\n"
        parent_lines.extend(
            [
                f"### {section.title}",
                "",
                f"[Open the chronological record]({collection_dir.name}/{section.slug}.md).",
                "",
            ]
        )
    if suffix:
        parent_lines.extend([suffix.strip(), ""])
    index_path.write_text(index_text.rstrip() + "\n", encoding="utf-8")
    parent_metadata = dict(metadata)
    parent_metadata["type"] = "Knowledge Collection"
    parent_metadata.setdefault("collection_type", original_type)
    parent_metadata["last_updated"] = "2026-08-11"
    path.write_text(dump_concept(parent_metadata, "\n".join(parent_lines)), encoding="utf-8")
    return len(sections)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", nargs="?", type=Path, default=Path("wiki"))
    parser.add_argument("--threshold-bytes", type=int, default=50_000)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--raw-headings", action="store_true", help="Treat H2 lines inside malformed fences as headings.")
    parser.add_argument("--path", type=Path, action="append", help="Split only this bundle-relative concept; repeatable.")
    parser.add_argument("--chronology", action="store_true", help="Split on short dated update paragraphs.")
    parser.add_argument("--all-dated-paragraphs", action="store_true", help="Chronology mode: do not require a confidence marker.")
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    if args.path:
        candidates = [(bundle / path).resolve() for path in args.path]
    else:
        candidates = [
            path
            for path in sorted(bundle.rglob("*.md"))
            if path.name not in {"index.md", "log.md"}
            and path.stat().st_size >= args.threshold_bytes
            and not path.with_suffix("").is_dir()
        ]
    if args.chronology:
        total = sum(
            split_chronology_concept(path, bundle, args.apply, args.all_dated_paragraphs)
            for path in candidates
        )
    else:
        total = sum(split_concept(path, bundle, args.apply, raw_headings=args.raw_headings) for path in candidates)
    print(f"{'split' if args.apply else 'would split'} {len(candidates)} collections into {total} concepts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
