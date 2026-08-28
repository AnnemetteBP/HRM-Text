---
type: Runbook
title: DFM10 Source Quality Audit
description: Deterministic Gemma 4 26B-A4B review of up to 100 exact training examples from every logical DFM10 source.
tags: [dfm10, data-quality, audit, gemma4, vllm]
status: draft
last_updated: 2026-08-27
confidence: high
---
# DFM10 Source Quality Audit

## Scope and authority

The source-quality campaign audits the complete logical DFM10 inventory rather
than only the new DFM10 additions. Its `178` source definitions comprise `161`
sources documented in `docs/dfm8-datasets.md`, nine DFM9 additions, and eight
DFM10 additions. The tokenized DFM10 union and
`data_io/prefix_config_dfm10.yaml` determine which examples are training
eligible. This preserves the sampler's default inclusion of unmatched tasks and
its explicit `max_per_file: 0` exclusions.

For the 177 sources already tokenized, sampling decodes the exact prompt and
assistant token spans visible to training. Each source receives a deterministic
uniform sample of 100 eligible examples, or every example when fewer than 100
exist.

**Superseded 2026-08-27:** the original plan required the fully merged
Folketing accepted tree. The acceptance campaign's stable-hash partitions 0--5
were complete while partitions 6--7 and the merged tree were not. The report
therefore adds a deterministic, task-stratified sample of 100 accepted rows
from the six complete partitions: 25 each from denoising, error correction,
prefix continuation, and span filling. This is an unbiased accepted-row subset
of those six partitions, not a claim that the full acceptance campaign was
consolidated.

## Review dimensions

Gemma 4 26B-A4B-it scores each example from 1 to 5 for:

1. language quality and absence of corruption;
2. instruction/answer or tool-call coherence;
3. meaningful ability to contribute to model training.

The rubric is task-aware: short labels, translation, reconstruction, synthetic
reasoning, structured output, and native tool calls are judged against their
declared purpose rather than rejected for their format.

The OpenAI-compatible request uses an explicit JSON Schema response format.
Generic JSON-object constraints reduced malformed responses but still allowed
missing nested scores; the explicit schema is required for reliable resumable
audits. Retry-exhausted rows are regenerated with a larger output allowance
before merge rather than accepted as audit results.

## Race and failure safety

`scripts/dfm10_quality_audit.py` writes deterministic samples once, gives each
sample a stable ID, and assigns IDs to a configured number of disjoint partitions. Each GPU
writes only its own resumable JSONL. Retry-exhausted API records are removed
from completed resume state and retried on the next invocation. The final
merger takes an exclusive file lock, rejects duplicates/missing/unexpected IDs,
and publishes the single result JSONL with `fsync` plus atomic rename.

On 2026-08-26, the original queued eight-GPU E4B plan was superseded by
`scripts/run_dfm10_quality_audit_4gpu_a4b.sh`. Folketing partitions 0 through 3
had completed, so their exact E4B server PIDs were terminated and GPUs 0 through
3 were reassigned to four A4B audit partitions. The launcher owns only the
server/worker PIDs it creates and frees them on completion or interruption.

The A4B vLLM launch uses the complete Hugging Face snapshot rather than the
incomplete weights-only copy, disables all multimodal inputs for this text-only
audit, uses `gpu_memory_utilization=0.90`, `max_num_seqs=64`, and client
concurrency 64. `CUDA_HOME=/usr/local/cuda` is required: pointing at the conda
environment prefix omitted CUDA headers from FlashInfer's host C++ compilation.
Warm `fused_moe_100` once with one server before parallel startup; the first
build compiles 266 CUDA objects, links the extension, and populates the shared
MoE autotune cache. Starting several cold servers against that cache is unsafe.

## Active paths

```text
logs/data_audits/dfm10_source_quality_a4b_20260826/
  inventory.json
  samples.jsonl
  partitions/partition_{0..3}.jsonl
  dfm10_source_quality_audit.jsonl
  dfm10_source_quality_audit.summary.json
```

The base 177-source artifact is
`logs/data_audits/dfm10_source_quality_a4b_20260826/dfm10_source_quality_audit.jsonl`.
The Folketing assessment is
`logs/data_audits/dfm10_folketing_quality_a4b_20260827/folketing_quality_audit.jsonl`.
The report builder combines these two immutable audit results rather than
rewriting the completed base artifact.

The ready-source pass completed on 2026-08-26 with 17,455 judgments across 177
sources, zero judge errors, and 15,044 rows (`86.2%`) marked usable for training.
All A4B servers owned by the pass were torn down after the merge.

The Folketing pass completed on 2026-08-27 with zero judge errors. It marked 87
of 100 accepted examples usable, with mean language, coherence, and training
value scores of 4.38, 4.59, and 4.48. Usable counts by task were 22/25
denoising, 18/25 error correction, 23/25 prefix continuation, and 24/25 span
filling. Error correction is the weakest family because residual OCR damage can
make even an acceptance-audited reconstruction target unreliable.

## Ranked PDF report

The reproducible report builder is
[`scripts/build_dfm10_quality_audit_report.py`](/../scripts/build_dfm10_quality_audit_report.py).
It reads the authoritative merged JSONL and produces both the LaTeX source and
the compiled report at:

- [`docs/reports/dfm10-source-quality-audit.tex`](/../docs/reports/dfm10-source-quality-audit.tex)
- [`docs/reports/dfm10-source-quality-audit.pdf`](/../docs/reports/dfm10-source-quality-audit.pdf)

Rebuild the committed artifacts with:

```bash
python scripts/build_dfm10_quality_audit_report.py
cd docs/reports
pdflatex -interaction=nonstopmode -halt-on-error dfm10-source-quality-audit.tex
pdflatex -interaction=nonstopmode -halt-on-error dfm10-source-quality-audit.tex
```

The report ranks all 178 audited sources and 17,555 judgments from most to least
severe. Its severity
index gives 50% weight to the unusable-row rate, 20% to coherence deficit, and
15% each to language-quality and training-value deficits. The table also gives
sample counts, usable and issue rates, all three mean scores, and the two most
frequent qualitative issue categories for every source.

**Superseded 2026-08-27:** the first report revision used one `Posttrain`
column whose labels combined task role and observed quality. That conflated two
independent decisions and must not be used.

The corrected report has two columns. `LLM role` depends only on task semantics:
`SFT` is ordinary supervised post-training, `Aux-SFT` is a reconstruction-style
auxiliary objective, and `Midtrain` is continuation data better suited to
continued pretraining or midtraining. `Quality` depends only on the audit:
`Use` requires at least 80% usable rows, mean coherence of at least 4.0, and
mean training value of at least 3.5; `Filter` is the intermediate disposition;
and `Repair` applies below 50% usability or 3.0 mean coherence. Thus a source
can be semantically appropriate for SFT while still requiring repair, or be a
high-quality source whose semantics make it midtraining data.

The combined report yields 169 `SFT`, 6 `Aux-SFT`, 2 `Midtrain`, and 1 `Mixed`
role classifications, independently of 136 `Use`, 32 `Filter`, and 10 `Repair`
quality dispositions. `Mixed` applies to the combined Folketing source because
it contains both reconstruction and continuation families. These are pipeline
triage judgments, not licensing, privacy, provenance, or safety determinations.

The brief category column uses the eight functional categories from the
[DFM-Mimir technical report](https://arxiv.org/html/2608.13517): Danish
instruction and knowledge, English instruction, Sapient mixed, math and
reasoning, Mimir synthetic, agentic and tool use, machine translation, and
science and summarization. Compact labels in the PDF assign each source its
dominant intended category.

The report also contains a remediation table for every `Filter` or `Repair`
source. It gives full eligible row counts, source-specific filtering or repair
steps, and coarse B200-equivalent GPU-hour estimates. Planning ranges are
10,000--40,000 A4B audit decisions per GPU-hour and 2,000--4,000 LLM
repair/regeneration rows per GPU-hour, reflecting substantial prompt-length
variance. Full-row re-audit of the 147,266,048 eligible rows in all 42 affected
sources is estimated at about 3.7k--14.7k B200 GPU-hours. Processing all
35,263,154 rows in the 14 sources marked for LLM repair would add about
8.8k--17.6k B200 GPU-hours. Deterministic converter/filter work is marked
`repair CPU`; the table still estimates the full re-audit cost. Startup,
engineering, human review, and repeat passes after further failures are
excluded.

## Initial source-level finding

The `dfm-agreement/dbc` sample had 73 of 100 rows marked unusable and 97 of 100
rows carrying at least one complaint. Inspection found a systematic conversion
policy mismatch in `dbc-abstracts_0011.parquet`: the prompt always requests a
Danish abstract (`Skriv et kort abstract eller resume ...`) while many source
abstracts and assistant targets are English. Treat this primarily as a converter
language-selection defect. Before retaining these rows, either preserve the
source language in the instruction or restrict the Danish instruction variant
to Danish targets; do not infer that the underlying English abstracts are
intrinsically unusable.

The `ccdv/govreport-summarization` sample had 73 of 100 rows marked unusable.
This is also a conversion defect, but one that breaks grounding rather than
only language selection. `scripts/generate_dfm4_tasks.py` keeps the complete
GovReport reference summary while trimming the report from its beginning to
`3000 - 300 - len(summary)` characters. In the audited sample, prompts averaged
only `1113` characters while targets averaged `1590` characters. The references
therefore routinely summarize facts absent from the model input, and some
targets are longer than the purported concise source summary. Do not retain the
current converted rows unchanged. Regenerate using token-aware admission of
only complete reports that fit the training context, move complete long reports
to an adequate long-context regime, or create genuinely chunk-grounded summary
targets. Merely increasing the prefix truncation limit does not establish that
the target is supported by the retained chunk.
