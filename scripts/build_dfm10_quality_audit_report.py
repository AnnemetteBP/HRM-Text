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
DEFAULT_AUDITS = (
    ROOT / "logs/data_audits/dfm10_source_quality_a4b_20260826/dfm10_source_quality_audit.jsonl",
    ROOT / "logs/data_audits/dfm10_folketing_quality_a4b_20260827/folketing_quality_audit.jsonl",
)
DEFAULT_OUTPUT = ROOT / "docs/reports/dfm10-source-quality-audit.tex"
AUDIT_ROWS_PER_GPU_HOUR = (10_000, 40_000)
REPAIR_ROWS_PER_GPU_HOUR = (2_000, 4_000)


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
    category: str
    training_role: str
    quality_disposition: str


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


def mimir_category(source_id: str) -> str:
    """Map a source to the functional categories used by the DFM-Mimir report."""
    lower = source_id.lower()
    if "sapient" in lower:
        return "Sapient"
    if source_id in {
        "schneiderkamplab/opus-da-en-permissive",
        "oliverkinch/machine-translation-da-ar",
        "oliverkinch/machine-translation-da-en",
        "oliverkinch/machine-translation-da-uk",
        "synquid/translation-100k",
    }:
        return "Translation"
    if any(term in lower for term in ("tool", "agentic", "function-calling", "nemotron-sft-swe", "terminal-corpus", "deepdive")):
        return "Agent/tool"
    if any(
        term in lower
        for term in ("math", "reasoning", "numina", "algebra", "multilingual_gsm", "code_meta", "code-debugging")
    ):
        return "Math/reason."
    if any(term in lower for term in ("summar", "scientific", "sciriff", "megascience", "arxiv_papers", "wiki_cat_sum")):
        return "Sci./summary"
    if (
        source_id.startswith("schneiderkamplab/common-pile-")
        or source_id.startswith("schneiderkamplab/danish-dynaword-")
        or source_id.startswith("schneiderkamplab/transformations-")
        or source_id == "dfm-agreement/rigsarkivet-folketinget-14004"
    ):
        return "Synthetic"
    if (
        source_id.startswith(("oliverkinch/", "synquid/", "giannor/", "alexandrainst/"))
        or source_id.startswith("danish-foundation-models/")
        or source_id.startswith("dfm-agreement/")
        or source_id.startswith("kobprof/")
        or source_id.startswith("croco-munin/")
        or source_id == "schneiderkamplab/dfm8-openhermes-da"
    ):
        return "Danish"
    if source_id.startswith("schneiderkamplab/dfm8-synthetic-"):
        return "Synthetic"
    return "English"


def training_role(source_id: str, rows: list[dict]) -> str:
    """Classify task semantics independently of observed source quality."""
    task_names = {str(row.get("task_name", "")) for row in rows}
    if source_id == "dfm-agreement/rigsarkivet-folketinget-14004":
        return "Mixed"
    if source_id.endswith("prefix-continuation") or any(name.endswith("prefix-continuation") for name in task_names):
        return "Midtrain"
    if source_id.endswith(("denoising", "paragraph-reordering", "span-filling")):
        return "Aux-SFT"
    return "SFT"


def quality_disposition(
    usable_rate: float,
    coherence_mean: float,
    value_mean: float,
) -> str:
    """Classify measured viability independently of the task's training role."""
    if usable_rate < 0.5 or coherence_mean < 3.0:
        return "Repair"
    if usable_rate < 0.8 or coherence_mean < 4.0 or value_mean < 3.5:
        return "Filter"
    return "Use"


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
        category=mimir_category(source_id),
        training_role=training_role(source_id, rows),
        quality_disposition=quality_disposition(usable_rate, coherence_mean, value_mean),
    )


def load_summaries(paths: list[Path] | tuple[Path, ...]) -> tuple[list[SourceSummary], int]:
    grouped: dict[str, list[dict]] = collections.defaultdict(list)
    rows = 0
    for path in paths:
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


def remediation(summary: SourceSummary) -> tuple[str, bool]:
    """Return a source-level remediation and whether it requires LLM generation."""
    source = summary.source_id
    finding = summary.finding.lower()
    if source.startswith("oliverkinch/machine-translation-"):
        return (
            "Regenerate from the original source with explicit language-direction checks; reject language-ID, "
            "semantic-similarity, and round-trip failures.",
            True,
        )
    if source == "dfm-agreement/dbc":
        return (
            "Make the instruction language follow the target abstract language, or retain only Danish targets; "
            "then validate prompt/target language agreement.",
            False,
        )
    if source == "ccdv/govreport-summarization":
        return (
            "Rebuild from complete reports that fit context, or derive summaries grounded in retained chunks; "
            "drop targets containing unsupported facts.",
            False,
        )
    if source == "laion/Scientific-Summaries":
        return (
            "Reject truncated targets and rebuild only examples with complete source/summary boundaries and "
            "grounding checks.",
            False,
        )
    if source == "nvidia/Nemotron-SFT-SWE-v2":
        return (
            "Use context-aware complete trajectory windows with an answer inside each window; drop orphaned or "
            "mid-action targets and validate tool/patch structure.",
            False,
        )
    if source == "oliverkinch/dst-table-prompts-bt":
        return (
            "Repair table serialization and backtranslation, remove OCR/metadata fragments, and require that the "
            "target is derivable from the serialized table.",
            True,
        )
    if "tool-call" in finding:
        return (
            "Normalize native tool schemas/calls/results, reject unresolved references and invalid JSON, and retain "
            "only trajectories passing deterministic execution-shape checks.",
            False,
        )
    if "translation mismatch" in finding:
        return (
            "Apply source/target language identification and semantic-alignment filtering; regenerate only failed "
            "pairs if source text and licensing permit.",
            summary.quality_disposition == "Repair",
        )
    if "truncated or incomplete target" in finding:
        generated = "sapient-synth" in source or source.endswith("-bt")
        return (
            "Enforce complete target boundaries and prompt/target length contracts; drop incomplete rows"
            + (" and regenerate from the intact seed." if generated else "."),
            generated,
        )
    if "ungrounded or hallucinated content" in finding:
        return (
            "Filter with source-grounding or entailment checks and reject unsupported answers; regenerate only "
            "where an authoritative source target is available.",
            False,
        )
    if "incorrect answer or reasoning" in finding:
        return (
            "Run task-specific answer verification (execution, symbolic checking, labels, or reference matching) "
            "and retain only verified prompt/answer pairs.",
            False,
        )
    if "scraping, ocr, or encoding noise" in finding:
        return (
            "Apply document-type, OCR-quality, boilerplate, and encoding filters before conversion; audit each "
            "retained source stratum separately.",
            False,
        )
    if "grammar or fluency defect" in finding:
        return (
            "Filter malformed rows with language/fluency checks and rewrite only otherwise valuable examples with "
            "a provenance-preserving repair pass.",
            False,
        )
    return (
        "Validate the declared output contract, reject prompt/target mismatches, and re-audit a stratified holdout "
        "before restoring sampling weight.",
        False,
    )


def format_gpu_hours(value: float) -> str:
    if value < 0.1:
        return "<0.1"
    if value < 10:
        return f"{value:.1f}"
    if value < 1_000:
        return f"{value:.0f}"
    return f"{value / 1_000:.1f}k"


def gpu_hour_range(rows: int, throughput: tuple[int, int]) -> str:
    slow, fast = throughput
    return f"{format_gpu_hours(rows / fast)}--{format_gpu_hours(rows / slow)}"


def gpu_hour_estimate(summary: SourceSummary, llm_repair: bool) -> str:
    audit = gpu_hour_range(summary.available_rows, AUDIT_ROWS_PER_GPU_HOUR)
    if not llm_repair:
        return f"audit ~{audit}; repair CPU"
    repair = gpu_hour_range(summary.available_rows, REPAIR_ROWS_PER_GPU_HOUR)
    return f"audit ~{audit}; repair ~{repair}"


def build_tex(audit_paths: list[Path], summaries: list[SourceSummary], row_count: int) -> str:
    usable = sum(item.usable_rate * item.samples for item in summaries) / row_count
    weighted = lambda name: sum(getattr(item, name) * item.samples for item in summaries) / row_count
    bands = collections.Counter(severity_band(item.severity) for item in summaries)
    roles = collections.Counter(item.training_role for item in summaries)
    dispositions = collections.Counter(item.quality_disposition for item in summaries)
    categories = collections.Counter(item.category for item in summaries)
    affected = [item for item in summaries if item.quality_disposition != "Use"]
    generated_repairs = [item for item in affected if remediation(item)[1]]
    affected_rows = sum(item.available_rows for item in affected)
    repair_rows = sum(item.available_rows for item in generated_repairs)
    table_rows: list[str] = []
    for rank, item in enumerate(summaries, start=1):
        finding = latex_escape(item.finding)
        table_rows.append(
            f"{rank} & \\url{{{item.source_id}}} & {latex_escape(item.category)} & {item.samples} & "
            f"{100 * item.usable_rate:.0f} & {100 * item.issue_rate:.0f} & "
            f"{item.language_mean:.2f} & {item.coherence_mean:.2f} & {item.value_mean:.2f} & "
            f"{item.severity:.1f} & {latex_escape(item.training_role)} & "
            f"{latex_escape(item.quality_disposition)} & {finding} \\\\"
        )

    remedy_rows: list[str] = []
    for item in summaries:
        if item.quality_disposition == "Use":
            continue
        recommendation, llm_repair = remediation(item)
        remedy_rows.append(
            f"\\url{{{item.source_id}}} & {item.available_rows:,} & "
            f"{latex_escape(item.quality_disposition)} & {latex_escape(recommendation)} & "
            f"{latex_escape(gpu_hour_estimate(item, llm_repair))} \\\\"
        )

    source_paths = "\n".join(
        rf"\item \path{{{path.relative_to(ROOT)}}}" for path in audit_paths
    )
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
This report aggregates the completed source-level audits:
\begin{{itemize}}
{source_paths}
\end{{itemize}}
The inventory covers {len(summaries)} logical sources and
{row_count:,} exact prompt/assistant examples visible to the DFM10 training pipeline.
Sampling was deterministic (seed 20260826), uniform within each source's eligible
rows, and capped at 100 examples per source; sources with fewer eligible examples
contribute all available examples. The report therefore estimates per-source
quality, not token-weighted corpus quality.

The Folketing source is the documented exception: its 100 rows are stratified
equally across four task families and sampled from accepted rows in completed
acceptance-audit hash partitions 0--5. Partitions 6--7 and the merged accepted
tree were not complete, so this is an unbiased accepted-row subset of the six
complete partitions rather than a claim that the full acceptance campaign was
consolidated.

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

The two decision columns are deliberately independent. \textbf{{LLM role}} is
based only on task semantics: \textbf{{SFT}} denotes ordinary supervised
post-training, \textbf{{Aux-SFT}} denotes reconstruction objectives useful as
narrow post-training auxiliaries, and \textbf{{Midtrain}} denotes continuation
data better suited to continued pretraining or midtraining. \textbf{{Mixed}}
denotes a source, currently Folketing, that contains both auxiliary SFT and
midtraining task families. It does not encode quality. \textbf{{Quality}} is
based only on audit measurements:
\textbf{{Use}} requires at least 80\% usable rows, mean coherence at least 4.0,
and mean training value at least 3.5; \textbf{{Filter}} denotes an intermediate
source; and \textbf{{Repair}} applies below 50\% usability or 3.0 mean
coherence. It does not encode training stage. Both assessments are independent
of HRM's recurrent architecture.

The compact
\textbf{{Category}} labels follow the eight functional categories in the
DFM-Mimir technical report: Danish instruction \& knowledge (Danish), English
instruction (English), Sapient mixed (Sapient), Math \& reasoning
(Math/reason.), Mimir synthetic (Synthetic), Agentic \& tool use (Agent/tool),
Machine translation (Translation), and Science \& summarization
(Sci./summary). Each source receives its dominant intended category. See
\url{{https://arxiv.org/html/2608.13517}}.

\section*{{Aggregate results}}
Across all judgments, {100 * usable:.1f}\% were marked usable. Mean language,
coherence, and training-value scores were {weighted('language_mean'):.2f},
{weighted('coherence_mean'):.2f}, and {weighted('value_mean'):.2f}. Source counts
by severity were: {bands['critical']} critical, {bands['high']} high,
{bands['moderate']} moderate, and {bands['low']} low. Training roles were:
{roles['SFT']} SFT, {roles['Aux-SFT']} Aux-SFT, and {roles['Midtrain']} Midtrain.
Quality dispositions were: {dispositions['Use']} Use,
{dispositions['Filter']} Filter, and {dispositions['Repair']} Repair.
The role counts also include {roles['Mixed']} Mixed source.
Category counts were: {', '.join(f'{latex_escape(key)} {value}' for key, value in sorted(categories.items()))}.

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
\begin{{longtable}}{{r L{{4.0cm}} L{{1.65cm}} r r r r r r r L{{1.1cm}} L{{1.05cm}} L{{4.9cm}}}}
\toprule
Rank & Source & Category & $n$ & Usable\% & Issue\% & Lang. & Coher. & Value & Sev. & LLM role & Quality & Recurring qualitative findings \\
\midrule
\endfirsthead
\toprule
Rank & Source & Category & $n$ & Usable\% & Issue\% & Lang. & Coher. & Value & Sev. & LLM role & Quality & Recurring qualitative findings \\
\midrule
\endhead
\midrule
\multicolumn{{13}}{{r}}{{Continued on next page}} \\
\endfoot
\bottomrule
\endlastfoot
{chr(10).join(table_rows)}
\end{{longtable}}

\normalsize
\section*{{Repair and filtering plan}}
The following table covers every source whose current quality disposition is
Filter or Repair. Row counts are the full eligible source counts observed by the
DFM10 sampler, not the 100-row report samples. GPU-hour estimates are deliberately
coarse B200-equivalent planning ranges: full A4B re-audit assumes
10,000--40,000 judged rows per GPU-hour and LLM repair/regeneration assumes
2,000--4,000 rows per GPU-hour. Across the {len(affected)} affected sources,
full-row re-audit of {affected_rows:,} eligible rows is approximately
{gpu_hour_range(affected_rows, AUDIT_ROWS_PER_GPU_HOUR)} GPU-hours. Processing
all {repair_rows:,} rows in the {len(generated_repairs)} sources marked for LLM
repair would add approximately
{gpu_hour_range(repair_rows, REPAIR_ROWS_PER_GPU_HOUR)} GPU-hours. ``repair
CPU'' means the proposed converter/filter work is deterministic and does not
itself require GPUs; its engineering and human-review time is not included.
Estimates exclude server startup, data conversion, human labeling, and repeat
audits after additional failures.

\scriptsize
\rowcolors{{2}}{{gray!7}}{{white}}
\begin{{longtable}}{{L{{5.0cm}} r L{{1.2cm}} L{{13.0cm}} L{{3.3cm}}}}
\toprule
Source & Eligible rows & Quality & Recommended repair/filter & Estimated B200 GPU-hours \\
\midrule
\endfirsthead
\toprule
Source & Eligible rows & Quality & Recommended repair/filter & Estimated B200 GPU-hours \\
\midrule
\endhead
\midrule
\multicolumn{{5}}{{r}}{{Continued on next page}} \\
\endfoot
\bottomrule
\endlastfoot
{chr(10).join(remedy_rows)}
\end{{longtable}}

\normalsize
\section*{{Interpretation limits}}
The 100-example cap gives useful source-level triage but wide uncertainty for
rare defects and heterogeneous sources. Issue percentages can overlap because a
single row may exhibit multiple problems. The training-role and quality
assessments are pipeline decision aids, not license, privacy, or safety
determinations. Before exclusion or high-repeat sampling, inspect the underlying
rows and validate any converter repair on a fresh holdout sample.

\end{{document}}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, action="append", dest="audits")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    audit_paths = args.audits or [path for path in DEFAULT_AUDITS if path.is_file()]
    summaries, row_count = load_summaries(audit_paths)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_tex(audit_paths, summaries, row_count), encoding="utf-8")
    print(f"wrote {args.output} ({len(summaries)} sources, {row_count} judgments)")


if __name__ == "__main__":
    main()
