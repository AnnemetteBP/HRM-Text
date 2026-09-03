---
type: Runbook
title: Commercial-Release Long-Context Data Pilot
description: Provenance-first profiling and admission workflow for native Danish and Nordic 16K--60K source documents.
tags: [data, long-context, danish, licensing, provenance]
status: draft
last_updated: 2026-08-31
confidence: high
---
# Commercial-Release Long-Context Data Pilot

## Scope

This pilot is a separate, stricter lane from the current Article 3 research
corpus. Its goal is to identify native Danish and Nordic source documents that
can support a model intended for both commercial and research use. A source is
not admitted merely because it is publicly accessible, appears in a data
portal, or has a permissive top-level dataset card.

The candidate register is
`legal/registers/long-context-commercial-source-candidates.csv`. Only a human
review may change `commercial_release_status` to `green`. The profiling tool
refuses to emit full-text candidate documents for any other status. Profiling
lengths while a source remains `review` is allowed and does not admit the
source to training.

## First source and boundary

The first technical target is Rigsarkivet handover 14004 / Folketinget because
the repository already has an ingestion path and records a CC BY 4.0 source
claim and publisher-side pseudonymization. The new pilot does not reuse
`prepare_dfm10_folketing_tasks.py` for long-context material: that converter
intentionally splits documents into approximately 2,200-character windows.
The profiler preserves complete documents.

The register initially leaves this source at `review`. Confirm at minimum:

1. that the licence applies to the retained document content rather than only
   catalogue metadata or the collection arrangement;
2. required attribution wording and whether it can be satisfied in a dataset
   card/model source manifest;
3. treatment of embedded or attached third-party works;
4. whether the publisher's pseudonymization statement and the project's own
   sampling review are sufficient for the intended release.

This is engineering/legal triage, not legal advice.

## Profile command

On the training machine, use the exact tokenizer of the checkpoint family:

```bash
python scripts/profile_long_context_documents.py \
  --input data/downloads/datasets/folketingets_dokumenter_14004/14004.zip \
  --source-id rigsarkivet-folketinget-14004 \
  --tokenizer-path /work/dfm/brainsurgery/models/gemma4_31b \
  --output-dir data/long_context_pilots/folketing_profile
```

The profile records complete-document counts and tokens in `<4K`, `4K--8K`,
`8K--16K`, `16K--32K`, `32K--60K`, and `60K+` bins. These are raw source
tokens, not final rendered prompt lengths. Instruction framing, evidence, and
the answer budget must later be subtracted from the model context limit.

### Local macOS verification

The profiler is CPU-only and does not require a training GPU. On the local Mac,
`/Users/ampirchert/miniconda3/envs/hrm-interp-env/bin/python` provides the
required `pyarrow`, `transformers`, and `tokenizers` packages. A complete CLI
smoke test with a disposable tokenizer and three Danish JSONL documents passed
on 2026-08-31, placing 480-, 4,800-, and 9,600-token documents in the expected
three bins.

**Superseded 2026-08-31:** the actual MiMir/Gemma tokenizer snapshot and
Folketing archive were initially absent from the workstation.

The tokenizer/configuration files from pinned MiMir revision
`2844f0178e695d7d9ce182cb660671fd34c76ce5` are now present under
`data/tokenizers/dfm-mimir`. Local-only loading in the Python 3.13
`hrm-text-env` succeeded with vocabulary size 262,144. The complete profiler
also passed against the Danish fixture using this tokenizer, measuring 879,
8,799, and 17,599 tokens in the expected `<4K`, `8K--16K`, and `16K--32K`
bins. The Folketing archive remains absent locally. Running the full profile
remotely is operationally simpler if that artifact already exists there; it is
not a GPU requirement.

Download only the tokenizer/configuration files from the released MiMir
revision; do not download the model weights for profiling:

```bash
conda activate hrm-text-env
hf auth login  # only if the repository requires authentication
hf download danish-foundation-models/DFM-Mimir \
  tokenizer.json tokenizer_config.json config.json chat_template.jinja \
  --revision 2844f0178e695d7d9ce182cb660671fd34c76ce5 \
  --local-dir data/tokenizers/dfm-mimir

python -c "from transformers import AutoTokenizer; t=AutoTokenizer.from_pretrained('data/tokenizers/dfm-mimir', local_files_only=True); print(type(t).__name__)"
```

The local profiling command must then use
`--tokenizer-path data/tokenizers/dfm-mimir`. A literal example placeholder
such as `/path/to/local/mimir-tokenizer` is not a usable filesystem path.

As checked on 2026-08-31, the official Rigsarkivet download endpoint returns
the archive with chunked transfer encoding, does not advertise a total content
length, and ignored a byte-range size probe. Do not use a range request to
estimate its size: it begins streaming the full archive. Obtain the complete
ZIP either through a normal download or by copying the already downloaded
artifact from the project server. `--max-docs` limits profiling work only; it
does not permit use of a partial ZIP.

After a responsible human changes the exact source row to `green`, add
`--emit-candidates` to write a deterministic, provenance-rich sample to
`source_documents.jsonl`. The output is explicitly marked
`source_document_not_instruction_data`; it must not be tokenized as SFT data.

## Admission stages

1. Preserve the exact source and licence evidence.
2. Profile complete documents with the target tokenizer.
3. Approve or reject the source rights and privacy boundary.
4. Freeze evaluation source IDs before task generation.
5. Generate grounded Danish tasks around admitted source documents.
6. Verify answers against evidence spans or deterministic calculations.
7. Run native-Danish quality review and PII/third-party-content checks.
8. Convert accepted examples through the MiMir chat template.
9. Recalculate final rendered prompt/target lengths and decontaminate against
   every evaluation split.

The initial implementation deliberately stops after stage 3. It establishes
the source supply and length distribution without committing to a generator,
prompt schema, training mixture, or 32K/60K training configuration.

## CC0 candidates absent from the MiMir v1 report

A 2026-08-31 comparison against the complete named training-source list in
MiMir v1 Appendix A and evaluation-source list in Appendix B identified four
official Danish resources that are not named in either list:

1. Digitaliseringsstyrelsen's municipal council and environment/technical
   committee minutes: 9 million Danish words from five municipalities, CC0.
   The publisher reports that attachments were excluded, documents containing
   sensitive personal data were removed, and direct identifiers were
   pseudonymized. This is the preferred first new corpus for a commercial-use
   pilot.
2. Det Kgl. Bibliotek's *Statslige Digitale Publikationer*: 14,465
   publications, CC0, created for Danish language-model training. It is a
   promising source of native Danish documents, but mixes born-digital and
   uncorrected OCR text and needs document-level quality and rights screening.
3. Det Kgl. Bibliotek's *Danmarks Breve*: 13,516 CC0/public-domain historical
   letters created for Danish language-model training. It is useful for
   historical Danish coverage but contains uncorrected OCR and is not the
   primary modern long-context reasoning source.
4. Dansk Sprognævn's COR: a CC0 Danish lemma, spelling, inflection, and
   compound index. It is suitable for lexical/morphology task construction,
   not for long-context document training.

“Absent from the report” means absent as a named source. It does not prove
that no document occurred inside a broad web-derived corpus such as DynaWord,
nor that no semantically similar text was used. Before admission, run exact
hash and near-duplicate checks against available MiMir training manifests and
all frozen evaluation sets. CC0 also does not waive privacy, confidentiality,
or rights in material accidentally included outside the publisher's stated
scope. Consequently all four rows remain `review` until file-level evidence
and sample inspection support a human `green` decision.

## First real profile and ordered-row correction

The initial `--max-docs 1000` run used the original first-row behavior and is
not representative. It measured 523 rows at 60K+ tokens, p50 78,009 tokens,
and a maximum of 9,644,400 tokens. Metadata inspection established that these
were chronologically early annual bound `Rigsdagstidende` volumes rather than
ordinary modern documents; examples contain 15--24 million characters and are
OCR-derived.

Collection-wide metadata contains 125,406 rows: 123,341 are dated 2004 or
later, and 123,292 are marked `dannet ved OCR = Nej`. The profiler now defaults
to deterministic collection-wide hash sampling whenever `--max-docs` is used.
Use an explicit modern, non-OCR pilot:

```bash
python scripts/profile_long_context_documents.py \
  --input data/downloads/datasets/folketingets_dokumenter_14004/14004.zip \
  --source-id rigsarkivet-folketinget-14004 \
  --tokenizer-path data/tokenizers/dfm-mimir \
  --output-dir data/long_context_pilots/folketing_modern_nonocr_1000 \
  --max-docs 1000 \
  --sample-mode hash \
  --year-min 2004 \
  --ocr-value Nej
```

Hash sampling first scans only identifiers and filter metadata, then reads the
selected full documents in a second pass. This avoids retaining the large
historical text rows merely to choose a representative sample. The older
volume material may later support separately segmented historical/OCR tasks;
it must not determine the main modern-Danish corpus profile.

The corrected run completed locally in roughly three minutes. Of 123,292
eligible rows dated 2004+ and marked non-OCR, the stable hash sample selected
1,000. Eighteen rows were shorter than the 200-character admission floor and
982 were profiled. Exact MiMir-tokenizer results were:

| Bin | Documents |
| --- | ---: |
| `<4K` | 892 |
| `4K--8K` | 22 |
| `8K--16K` | 30 |
| `16K--32K` | 11 |
| `32K--60K` | 6 |
| `60K+` | 21 |

The median was 549 tokens, p95 was 12,071, p99 was 97,809, and the maximum
was 645,866. Thus naturally long modern documents exist but are a minority:
17/982 profiled documents fell directly in the 16K--60K target range and 21
more exceeded 60K. Treat extrapolations to the full collection as rough supply
estimates until the complete eligible stratum is profiled. Documents above the
target limit require structure-aware segmentation, not blind truncation.

Every profile now writes `profiled_documents.jsonl` alongside `profile.json`.
It contains document IDs, selected metadata, exact token length, length bin,
and a content hash, but explicitly contains no source text. This metadata-only
artifact is permitted while the source remains `review`; it is not a training
dataset or a release approval.

Create a deterministic human-review sheet with up to 20 rows from each long
bin:

```bash
python scripts/create_long_context_review_sheet.py \
  --profiled-documents data/long_context_pilots/folketing_modern_nonocr_1000/profiled_documents.jsonl \
  --output data/long_context_pilots/folketing_modern_nonocr_1000/quality_review.csv \
  --per-bin 20
```

The sheet contains six 1--5 quality fields, privacy/rights disposition,
use/filter/segment/reject decision, and free-text segmentation/review notes.
It does not contain the document body; human reviewers must inspect the named
source document internally before scoring it.
