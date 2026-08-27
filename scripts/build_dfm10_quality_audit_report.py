#!/usr/bin/env python3
"""Build a severity-ranked LaTeX report from the DFM10 source audit."""

from __future__ import annotations

import argparse
import collections
import json
import statistics
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT = ROOT / "logs/data_audits/dfm10_source_quality_a4b_20260826/dfm10_source_quality_audit.jsonl"
DEFAULT_OUTPUT = ROOT / "docs/reports/dfm10-source-quality-audit.tex"


ISSUE_TAXONOMY: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("translation mismatch or failure", ("translation", "translate", "target language")),
    ("truncated or incomplete target", ("truncat", "incomplete", "ends abruptly", "mid-sentence", "fragment")),
    ("ungrounded or hallucinated content", ("hallucin", "not present", "unsupported", "grounding", "external information")),
    ("incorrect answer or reasoning", ("incorrect", "wrong answer", "false", "logical error", "reasoning error", "contradict")),
    ("instruction or output-format mismatch", ("instruction", "format mismatch", "fails to", "failed to", "does not follow")),
    ("prompt/target language mismatch", ("language mismatch", "responded in english", "response is in english")),
    ("scraping, OCR, or encoding noise", ("ocr", "scrap", "mojibake", "encoding", "corrupt", "boilerplate", "metadata")),
    ("tool-call or agent-trajectory defect", ("tool call", "tool-call", "tool selection", "agent trace", "trajectory")),
    ("low-value, ambiguous, or overly narrow signal", ("low value", "low-value", "ambiguous", "too short", "bare number", "trivial")),
    ("repetition or excessive verbosity", ("repet", "verbose", "redundan")),
    ("grammar or fluency defect", ("grammar", "ungrammat", "fluency", "awkward", "typo")),
    ("safety, privacy, or offensive-content concern", ("unsafe", "privacy", "personal data", "offensive", "toxic", "slur")),
)


@dataclass
class SourceSummary:
    source_id: str
    generation: str
    form: str
    samples: int
    available_rows: int
    usable_rate: float
    issue_rate: float
    language_mean: float
    coherence_mean: float
    value_mean: float
    severity: float
    finding: str
    posttraining: str


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def issue_text(judgment: dict) -> str:
    parts: list[str] = []
    for key in ("language_quality", "instruction_answer_coherence", "training_value"):
        parts.extend(str(item) for item in judgment[key].get("issues", []))
    if not judgment["usable_for_training"]:
        parts.append(str(judgment.get("assessment", "")))
        parts.append(str(judgment.get("primary_problem", "")))
    return " ".join(parts).lower()


def issue_categories(judgment: dict) -> set[str]:
    text = issue_text(judgment)
    return {
        label
        for label, needles in ISSUE_TAXONOMY
        if any(needle in text for needle in needles)
    }


def posttraining_suitability(
    source_id: str,
    usable_rate: float,
    coherence_mean: float,
    value_mean: float,
) -> str:
    if usable_rate < 0.5 or coherence_mean < 3.0:
        return "No--repair"
    if source_id.endswith("prefix-continuation"):
        return "No--midtrain"
    transformation = (
        source_id.startswith("schneiderkamplab/common-pile-")
        or source_id.startswith("schneiderkamplab/danish-dynaword-")
        or source_id.startswith("schneiderkamplab/transformations-")
        or source_id == "common-pile/arxiv_papers_filtered"
    )
    if transformation or usable_rate < 0.8 or coherence_mean < 4.0 or value_mean < 3.5:
        return "Conditional"
    return "Yes"


def summarize_source(source_id: str, rows: list[dict]) -> SourceSummary:
    judgments = [row["judgment"] for row in rows]
    samples = len(rows)
    usable_rate = sum(bool(item["usable_for_training"]) for item in judgments) / samples
    score = lambda key: statistics.mean(float(item[key]["score"]) for item in judgments)
    language_mean = score("language_quality")
    coherence_mean = score("instruction_answer_coherence")
    value_mean = score("training_value")
    has_issue = [bool(issue_text(item).strip()) for item in judgments]
    issue_rate = sum(has_issue) / samples
    severity = 100 * (
        0.50 * (1 - usable_rate)
        + 0.15 * (5 - language_mean) / 4
        + 0.20 * (5 - coherence_mean) / 4
        + 0.15 * (5 - value_mean) / 4
    )

    category_rows: collections.Counter[str] = collections.Counter()
    for judgment in judgments:
        category_rows.update(issue_categories(judgment))
    top = category_rows.most_common(2)
    if top:
        finding = "; ".join(f"{label} ({count / samples:.0%})" for label, count in top)
    elif issue_rate:
        finding = f"Scattered judge complaints without a recurring taxonomy category ({issue_rate:.0%} of rows)."
    else:
        finding = "No issue identified in the sample."

    return SourceSummary(
        source_id=source_id,
        generation=str(rows[0]["generation"]),
        form=str(rows[0]["form"]),
        samples=samples,
        available_rows=max(int(row.get("source_available_rows", 0)) for row in rows),
        usable_rate=usable_rate,
        issue_rate=issue_rate,
        language_mean=language_mean,
        coherence_mean=coherence_mean,
        value_mean=value_mean,
        severity=severity,
        finding=finding,
        posttraining=posttraining_suitability(source_id, usable_rate, coherence_mean, value_mean),
    )


def load_summaries(path: Path) -> tuple[list[SourceSummary], int]:
    grouped: dict[str, list[dict]] = collections.defaultdict(list)
    rows = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            grouped[str(row["source_id"])].append(row)
            rows += 1
    summaries = [summarize_source(source_id, source_rows) for source_id, source_rows in grouped.items()]
    summaries.sort(key=lambda item: (-item.severity, item.source_id.lower()))
    return summaries, rows


def severity_band(value: float) -> str:
    if value >= 50:
        return "critical"
    if value >= 30:
        return "high"
    if value >= 15:
        return "moderate"
    return "low"


def build_tex(audit_path: Path, summaries: list[SourceSummary], row_count: int) -> str:
    usable = sum(item.usable_rate * item.samples for item in summaries) / row_count
    weighted = lambda name: sum(getattr(item, name) * item.samples for item in summaries) / row_count
    bands = collections.Counter(severity_band(item.severity) for item in summaries)
    suitability = collections.Counter(item.posttraining for item in summaries)
    table_rows: list[str] = []
    for rank, item in enumerate(summaries, start=1):
        finding = latex_escape(item.finding)
        table_rows.append(
            f"{rank} & \\url{{{item.source_id}}} & {item.samples} & "
            f"{100 * item.usable_rate:.0f} & {100 * item.issue_rate:.0f} & "
            f"{item.language_mean:.2f} & {item.coherence_mean:.2f} & {item.value_mean:.2f} & "
            f"{item.severity:.1f} & {latex_escape(item.posttraining)} & {finding} \\\\"
        )

    source_path = latex_escape(str(audit_path.relative_to(ROOT)))
    return rf"""\documentclass[10pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage[margin=12mm,landscape]{{geometry}}
\usepackage{{booktabs,longtable,array,xurl}}
\usepackage[table]{{xcolor}}
\usepackage[scaled=0.92]{{helvet}}
\renewcommand{{\familydefault}}{{\sfdefault}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{4pt}}
\setlength{{\tabcolsep}}{{2.2pt}}
\newcolumntype{{L}}[1]{{>{{\raggedright\arraybackslash}}p{{#1}}}}
\title{{DFM10 Source-Level Training Data Quality Audit}}
\author{{Danish Foundation Models / HRM-Text data pipeline}}
\date{{27 August 2026}}

\begin{{document}}
\maketitle

\section*{{Audit method}}
This report aggregates the completed source-level audit in
\texttt{{{source_path}}}. The inventory covers {len(summaries)} logical sources and
{row_count:,} exact prompt/assistant examples visible to the DFM10 training pipeline.
Sampling was deterministic (seed 20260826), uniform within each source's eligible
rows, and capped at 100 examples per source; sources with fewer eligible examples
contribute all available examples. The report therefore estimates per-source
quality, not token-weighted corpus quality.

Each example was judged by Gemma 4 26B-A4B-it using an explicit JSON schema on
three 1--5 dimensions: language quality, instruction/answer coherence, and
training value. The judge also supplied issue lists and a binary
\emph{{usable-for-training}} decision. The run contains zero judge errors. These
are model-based screening results, not substitutes for human review, provenance
review, contamination analysis, or task-specific correctness tests.

The severity index ranks the table as
\[
100\left[0.50(1-u)+0.15\frac{{5-L}}{{4}}+0.20\frac{{5-C}}{{4}}+
0.15\frac{{5-V}}{{4}}\right],
\]
where $u$ is usable rate and $L,C,V$ are the three mean scores. Thus unusable
examples dominate, coherence is next, and language/training-value deficits break
ties. Bands are critical $\geq50$, high $\geq30$, moderate $\geq15$, and low
$<15$. Qualitative findings report the two most frequent issue categories per
source and the percentage of sampled rows exhibiting each category.

The post-training column assesses the \emph{{current converted source}} for
supervised post-training of a conventional pretrained decoder-only LLM:
\textbf{{Yes}} means directly relevant and sufficiently coherent;
\textbf{{Conditional}} means useful after filtering or as a narrow auxiliary task;
\textbf{{No--repair}} means conceptually relevant but the current conversion is too
broken; and \textbf{{No--midtrain}} denotes continuation-style data better treated
as midtraining or continued pretraining. This assessment is independent of HRM's
recurrent architecture.

\section*{{Aggregate results}}
Across all judgments, {100 * usable:.1f}\% were marked usable. Mean language,
coherence, and training-value scores were {weighted('language_mean'):.2f},
{weighted('coherence_mean'):.2f}, and {weighted('value_mean'):.2f}. Source counts
by severity were: {bands['critical']} critical, {bands['high']} high,
{bands['moderate']} moderate, and {bands['low']} low. Post-training assessments
were: {suitability['Yes']} Yes, {suitability['Conditional']} Conditional,
{suitability['No--repair']} No--repair, and {suitability['No--midtrain']}
No--midtrain.

The strongest immediate exclusions are the sources at the top of the table.
In particular, the Arabic and Ukrainian machine-translation conversions show
systematic target mismatch; DBC has a prompt/target language-policy defect;
GovReport targets are frequently unsupported by truncated prompts; and
Scientific-Summaries contains widespread truncated targets. These are actionable
conversion or source-filtering defects rather than evidence that the underlying
task families are intrinsically unsuitable.

\section*{{All audited sources, most severe first}}
\scriptsize
\rowcolors{{2}}{{gray!7}}{{white}}
\begin{{longtable}}{{r L{{5.0cm}} r r r r r r r L{{1.6cm}} L{{7.2cm}}}}
\toprule
Rank & Source & $n$ & Usable\% & Issue\% & Lang. & Coher. & Value & Sev. & Posttrain & Recurring qualitative findings \\
\midrule
\endfirsthead
\toprule
Rank & Source & $n$ & Usable\% & Issue\% & Lang. & Coher. & Value & Sev. & Posttrain & Recurring qualitative findings \\
\midrule
\endhead
\midrule
\multicolumn{{11}}{{r}}{{Continued on next page}} \\
\endfoot
\bottomrule
\endlastfoot
{chr(10).join(table_rows)}
\end{{longtable}}

\normalsize
\section*{{Interpretation limits}}
The 100-example cap gives useful source-level triage but wide uncertainty for
rare defects and heterogeneous sources. Issue percentages can overlap because a
single row may exhibit multiple problems. The post-training assessment is a
pipeline decision aid, not a license, privacy, or safety determination. Before
exclusion or high-repeat sampling, inspect the underlying rows and validate any
converter repair on a fresh holdout sample.

\end{{document}}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    summaries, row_count = load_summaries(args.audit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_tex(args.audit, summaries, row_count), encoding="utf-8")
    print(f"wrote {args.output} ({len(summaries)} sources, {row_count} judgments)")


if __name__ == "__main__":
    main()
