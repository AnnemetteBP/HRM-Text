#!/usr/bin/env python3
"""Judge exact-prefix memorisation matches with OpenAI-compatible servers.

The tool preserves every protocol occurrence while judging identical source
evidence only once. Outputs are resumable JSONL files written atomically.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable


DEFAULT_CATEGORY_DIRS = {
    category: Path(f"logs/analysis/dfm9_memorisation_category_{category.lower()}_exhaustive_step1650000")
    for category in "ABCD"
}
CONTENT_FORMS = {
    "expressive_prose",
    "factual_prose",
    "dialogue",
    "code",
    "math",
    "list_or_table",
    "boilerplate",
    "repeated_pattern",
    "markup_or_metadata",
    "other",
}
LEVELS = {"low", "medium", "high"}


def open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open(encoding="utf-8")


def iter_jsonl(paths: Iterable[Path]):
    for path in paths:
        with open_text(path) as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def evidence_key(row: dict[str, Any]) -> str:
    payload = "\0".join(
        (
            str(row.get("content_hash", "")),
            str(row.get("source_prefix", "")),
            str(row.get("reference_continuation", "")),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def scan_result_shard(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if '"exact_target": true' not in line:
                continue
            row = json.loads(line)
            if row.get("exact_target"):
                rows.append(row)
    return rows


def atomic_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(temporary, path)


def prepare(args: argparse.Namespace) -> None:
    reused: dict[str, Path] = {}
    for value in args.reuse_exact:
        category, separator, path = value.partition("=")
        if not separator or category.upper() not in DEFAULT_CATEGORY_DIRS:
            raise SystemExit(f"Invalid --reuse-exact value: {value!r}; expected C=/path")
        reused[category.upper()] = Path(path)

    category_dirs = dict(DEFAULT_CATEGORY_DIRS)
    for value in args.category_dir:
        category, separator, path = value.partition("=")
        if not separator or category.upper() not in category_dirs:
            raise SystemExit(f"Invalid --category-dir value: {value!r}; expected A=/path")
        category_dirs[category.upper()] = Path(path)

    rows: list[dict[str, Any]] = []
    scan_jobs: list[tuple[str, Path]] = []
    for category, directory in category_dirs.items():
        if category in reused:
            paths = sorted(reused[category].glob("*.jsonl")) + sorted(reused[category].glob("*.jsonl.gz"))
            for row in iter_jsonl(paths):
                row["audit_category"] = category
                rows.append(row)
        else:
            scan_jobs.extend((category, path) for path in sorted(directory.glob("results_shard_*.jsonl.gz")))

    with ThreadPoolExecutor(max_workers=args.scan_workers) as pool:
        futures = {pool.submit(scan_result_shard, path): (category, path) for category, path in scan_jobs}
        for future in as_completed(futures):
            category, path = futures[future]
            found = future.result()
            for row in found:
                row["audit_category"] = category
                rows.append(row)
            print(f"scanned {path.name}: exact={len(found)}", flush=True)

    rows.sort(key=lambda row: (row["audit_category"], row.get("cohort", ""), row.get("source_id", ""), row.get("mode", "")))
    for row in rows:
        row["evidence_key"] = evidence_key(row)
    atomic_jsonl(args.output_dir / "exact_matches.jsonl", rows)

    unique: dict[str, dict[str, Any]] = {}
    occurrences: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = row["evidence_key"]
        unique.setdefault(
            key,
            {
                "evidence_key": key,
                "source_prefix": row.get("source_prefix", ""),
                "reference_continuation": row.get("reference_continuation", ""),
                "content_hash": row.get("content_hash", ""),
            },
        )
        occurrences[key].append(
            {
                "category": row["audit_category"],
                "cohort": row.get("cohort", ""),
                "mode": row.get("mode", ""),
                "source_id": row.get("source_id", ""),
                "source_path": row.get("source_path", ""),
            }
        )
    unique_rows = []
    for key, row in unique.items():
        row["occurrences"] = occurrences[key]
        row["occurrence_count"] = len(occurrences[key])
        unique_rows.append(row)
    unique_rows.sort(key=lambda row: row["evidence_key"])
    atomic_jsonl(args.output_dir / "unique_evidence.jsonl", unique_rows)
    print(f"prepared occurrences={len(rows)} unique_evidence={len(unique_rows)}", flush=True)


def judge_prompt(row: dict[str, Any]) -> tuple[str, str]:
    system = (
        "You are adjudicating exact-continuation evidence from a memorisation probe. "
        "Classify the textual form and whether the matched continuation contains human-authored, "
        "potentially copyrightable expression. Do not decide whether model memorisation legally occurred. "
        "Be conservative: ordinary coherent sentences can be copyright-relevant even if factual; headings, "
        "short stock phrases, mechanical lists, repeated strings, code, formulae, and metadata usually are not. "
        "Expressive prose includes narrative, commentary, distinctive exposition, reviews, or creative writing. "
        "Return only one compact JSON object with exactly the requested fields."
    )
    user = json.dumps(
        {
            "source_prefix": row["source_prefix"],
            "exactly_generated_continuation": row["reference_continuation"],
            "required_fields": {
                "content_form": sorted(CONTENT_FORMS),
                "coherent_prose": "boolean",
                "expressive_prose": "boolean",
                "formulaic_or_constrained": "boolean",
                "copyright_expression_level": sorted(LEVELS),
                "review_priority": sorted(LEVELS),
                "reason": "one precise sentence, maximum 35 words",
            },
        },
        ensure_ascii=False,
    )
    return system, user


def parse_json_object(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match is None:
        raise ValueError("judge response has no JSON object")
    value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("judge response is not an object")
    return value


def validate_judgment(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("content_form") not in CONTENT_FORMS:
        raise ValueError(f"invalid content_form: {value.get('content_form')!r}")
    for key in ("coherent_prose", "expressive_prose", "formulaic_or_constrained"):
        if not isinstance(value.get(key), bool):
            raise ValueError(f"invalid boolean {key}: {value.get(key)!r}")
    for key in ("copyright_expression_level", "review_priority"):
        if value.get(key) not in LEVELS:
            raise ValueError(f"invalid level {key}: {value.get(key)!r}")
    reason = str(value.get("reason", "")).strip()
    if not reason:
        raise ValueError("empty reason")
    value["reason"] = reason
    return value


def call_judge(endpoint: str, model: str, row: dict[str, Any], timeout: int, retries: int) -> dict[str, Any]:
    system, user = judge_prompt(row)
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 220,
    }
    request = urllib.request.Request(
        endpoint.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer EMPTY"},
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            text = payload["choices"][0]["message"]["content"]
            return validate_judgment(parse_json_object(text))
        except (OSError, KeyError, ValueError, json.JSONDecodeError, urllib.error.HTTPError) as error:
            last_error = error
            if attempt < retries:
                time.sleep(min(10, 2**attempt))
    raise RuntimeError(f"judge failed after {retries} attempts: {last_error}")


def load_existing(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    return {row["evidence_key"]: row for row in iter_jsonl([path]) if row.get("status") == "ok"}


def judge(args: argparse.Namespace) -> None:
    evidence_path = args.output_dir / "unique_evidence.jsonl"
    rows = list(iter_jsonl([evidence_path]))
    output_path = args.output_dir / "judgments.jsonl"
    completed = load_existing(output_path)
    pending = [row for row in rows if row["evidence_key"] not in completed]
    print(f"judge unique={len(rows)} complete={len(completed)} pending={len(pending)}", flush=True)

    results = dict(completed)
    workers = len(args.endpoint) * args.concurrency_per_endpoint
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}
        for index, row in enumerate(pending):
            endpoint = args.endpoint[index % len(args.endpoint)]
            future = pool.submit(call_judge, endpoint, args.model, row, args.timeout, args.retries)
            futures[future] = (row, endpoint)
        finished = 0
        for future in as_completed(futures):
            row, endpoint = futures[future]
            try:
                decision = future.result()
                result = {**row, "status": "ok", "judge_endpoint": endpoint, "judgment": decision}
            except Exception as error:  # preserve failure evidence for a resumable retry
                result = {**row, "status": "failed", "judge_endpoint": endpoint, "error": repr(error)}
            results[row["evidence_key"]] = result
            finished += 1
            if finished % 100 == 0 or finished == len(pending):
                atomic_jsonl(output_path, (results[key] for key in sorted(results)))
                print(f"judged {finished}/{len(pending)}", flush=True)
    atomic_jsonl(output_path, (results[key] for key in sorted(results)))
    report(args.output_dir)


def report(output_dir: Path) -> None:
    exact_rows = list(iter_jsonl([output_dir / "exact_matches.jsonl"]))
    judgments = {row["evidence_key"]: row for row in iter_jsonl([output_dir / "judgments.jsonl"])}
    form_counts: Counter[str] = Counter()
    level_counts: Counter[str] = Counter()
    priority_counts: Counter[str] = Counter()
    category_counts: dict[str, Counter[str]] = defaultdict(Counter)
    prose_counts: Counter[str] = Counter()
    category_prose_counts: dict[str, Counter[str]] = defaultdict(Counter)
    high_rows: list[dict[str, Any]] = []
    adjudicated_rows: list[dict[str, Any]] = []
    failed = 0
    for row in exact_rows:
        judged = judgments.get(row["evidence_key"], {})
        if judged.get("status") != "ok":
            failed += 1
            continue
        decision = judged["judgment"]
        adjudicated_rows.append({**row, "judgment": decision})
        form_counts[decision["content_form"]] += 1
        level_counts[decision["copyright_expression_level"]] += 1
        priority_counts[decision["review_priority"]] += 1
        category_counts[row["audit_category"]][decision["content_form"]] += 1
        for key in ("coherent_prose", "expressive_prose", "formulaic_or_constrained"):
            label = f"{key}={str(decision[key]).lower()}"
            prose_counts[label] += 1
            category_prose_counts[row["audit_category"]][label] += 1
        if decision["review_priority"] == "high" or decision["expressive_prose"]:
            high_rows.append({**row, "judgment": decision})

    summary = {
        "occurrences": len(exact_rows),
        "unique_evidence": len(judgments),
        "unjudged_or_failed_occurrences": failed,
        "content_forms": dict(form_counts),
        "copyright_expression_levels": dict(level_counts),
        "review_priorities": dict(priority_counts),
        "content_forms_by_category": {key: dict(value) for key, value in category_counts.items()},
        "text_characteristics": dict(prose_counts),
        "text_characteristics_by_category": {
            key: dict(value) for key, value in category_prose_counts.items()
        },
        "high_priority_or_expressive_occurrences": len(high_rows),
    }
    temporary = output_dir / "summary.json.tmp"
    temporary.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, output_dir / "summary.json")
    atomic_jsonl(output_dir / "adjudicated_occurrences.jsonl", adjudicated_rows)
    atomic_jsonl(output_dir / "high_priority_or_expressive.jsonl", high_rows)
    print(json.dumps(summary, indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "judge", "report", "all"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("logs/analysis/dfm9_memorisation_exact_match_judge_step1650000"),
    )
    parser.add_argument("--category-dir", action="append", default=[], metavar="A=PATH")
    parser.add_argument("--reuse-exact", action="append", default=[], metavar="C=PATH")
    parser.add_argument("--scan-workers", type=int, default=8)
    parser.add_argument(
        "--endpoint",
        action="append",
        default=[],
        help="OpenAI-compatible /v1 endpoint; repeat for load balancing",
    )
    parser.add_argument("--model", default="posttrain-gemma-teacher")
    parser.add_argument("--concurrency-per-endpoint", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--retries", type=int, default=4)
    args = parser.parse_args()
    if not args.endpoint:
        args.endpoint = [f"http://127.0.0.1:{port}/v1" for port in range(8500, 8508)]
    if args.command in {"prepare", "all"}:
        prepare(args)
    if args.command in {"judge", "all"}:
        judge(args)
    if args.command == "report":
        report(args.output_dir)


if __name__ == "__main__":
    main()
