# DFM9 Sapient Factual-FLAN Family Audit

Status: evidence-based engineering/legal triage, not legal advice or
institutional approval. Reviewed 2026-08-17.

## Scope and effective exposure

DFM9 samples 266 tokenized files under the `flan_factual__` prefix. They are
Open-Orca/FLAN task transformations produced by
`data_io/pipe_clustered/clean_flan.py`; DFM9 caps each file at 100,000 rows and
repeats the resulting slice twice. The transformations change instructions and
answer presentation, but ordinarily retain passages, questions, choices, and
answers. Upstream content rights therefore remain relevant.

The authoritative exposure is 10,199,566,222.4 tokens per epoch:

| Family | Files | Rows/epoch | Tokens/epoch | Current basis |
|---|---:|---:|---:|---|
| RACE | 72 | 6,064,572 | 5,928,810,490.0 | Article 4 / Danish section 11 b |
| SQuAD | 16 | 1,627,770 | 818,403,640.0 | CC-BY-SA-4.0 |
| QuAC | 4 | 643,736 | 712,351,845.8 | MIT plus Wikipedia terms |
| ROPES | 54 | 1,151,996 | 710,297,538.0 | CC-BY-4.0 |
| DROP | 10 | 716,698 | 617,533,186.8 | CC-BY-SA-4.0 |
| HotpotQA/KILT | 28 | 3,487,912 | 595,781,798.0 | CC-BY-SA-4.0 |
| WikiDialog | 4 | 800,000 | 366,934,118.2 | Wikipedia open terms plus synthetic layer |
| DREAM | 28 | 372,976 | 192,229,708.0 | Article 4 / Danish section 11 b |
| CoQA | 8 | 64,274 | 82,494,160.0 | Mixed direct terms plus Article 4 |
| TriviaQA | 8 | 673,106 | 61,108,488.2 | Apache-2.0 publisher representation; manual project-owner override |
| BoolQ | 8 | 126,662 | 50,877,384.0 | CC-BY-SA-3.0 |
| Natural Questions | 4 | 671,634 | 46,898,189.4 | CC-BY-SA-3.0 |
| WebQuestions | 22 | 181,016 | 15,845,676.0 | Article 4 / Danish section 11 b |
| **Total** | **266** |  | **10,199,566,222.4** |  |

All retained KILT-labelled factual tasks map to HotpotQA transformations, so
KILT does not add a fourteenth underlying corpus in this slice.

## Direct/open branches

The official or canonical dataset releases state open terms for SQuAD,
QuAC, ROPES, DROP, HotpotQA, BoolQ, and Natural Questions. WikiDialog is a
synthetic dialogue release grounded in English Wikipedia: one speaker's turns
are exact Wikipedia sentences, so Wikipedia attribution and ShareAlike duties
remain material even though the counterpart turns are generated.

These branches do not require Article 3 for the current use. Dataset and model
release documentation must nevertheless preserve source attribution, licence
notices, and a deliberate ShareAlike analysis rather than treating model
weights as a redistributed copy of the datasets.

## Project-owner Article 4 decision

Update, 2026-08-17: the project owner determined that RACE, DREAM,
WebQuestions, and the uncovered portions of CoQA are covered for this project
by Article 4 / Danish Copyright Act section 11 b. The decision rests on lawful,
long-running public distribution through the original research releases and
Hugging Face, no identified reservation, and no known challenge from a source
rightsholder. Acquisition-time machine-readable evidence remains incomplete,
but is treated as a documented evidentiary caveat rather than a blocker.

This supersedes the initial conservative Article 3 classification below. The
source facts and absence of an explicit open licence remain part of the record.

## Superseded initial Article 3 assessment

### RACE and DREAM

Both releases contain human-authored English examinations. Their papers and
project pages make the datasets publicly available for research, but the
review did not find an explicit open content licence granting general reuse of
the exam expression. Availability and a citation request are not substitutes
for such a licence. Because passages, questions, and choices remain in the
FLAN rows, the initial audit used the scientific-research TDM exception, with
lawful access, research-purpose, security, and retention conditions. This
classification was superseded by the project-owner Article 4 decision above.

RACE dominates this branch at 5.929B tokens per epoch. The initial assessment
is retained to explain why an exception is required despite public download.

### TriviaQA and WebQuestions

TriviaQA's official release expressly says that the University of Washington
does not own copyright in the included questions and documents. The public
release is useful lawful-access evidence, not an upstream copyright grant.
WebQuestions contains crowd-authored natural-language questions and Freebase
answers, but no explicit licence for the original question collection was
found. WebQuestions was subsequently moved to Article 4. TriviaQA was
decomposed by question source as described below.

### CoQA

CoQA documents a source-specific mixture: literature and Wikipedia under
CC-BY-SA, MCTest children's stories under MSR-LA, CNN news under Apache terms,
and examination passages inherited from RACE. The direct terms cover much of
the public release. The initial Article 3 fallback for RACE-derived and other
unresolved expression was superseded by the project-owner Article 4 decision.
This remains a component treatment, not a claim that all CoQA material needs a
statutory exception.

## TriviaQA source grouping

The retained eight factual-FLAN files contain trivia questions and short
answers. They do **not** retain TriviaQA's evidence documents, search-result
text, or source URLs. Exact normalized-question matching against the upstream
`rc.nocontext` train, validation, and test splits assigned 373,873 of 373,899
transformed rows (99.993%) to the upstream `question_source` field. Estimated
token allocations were reconciled proportionally to the authoritative
61,108,488.2 tokens/epoch.

Scope note, 2026-08-17: DFM9 does sample this branch. Its configured 100,000
row cap per file and repeat of two produce 673,106 TriviaQA-derived selections
and approximately 61.108M tokens per epoch across these eight files. DFM9 also
contains two separately converted Natural Instructions tasks derived from
TriviaQA (`task1564` and `task1565`), contributing another 217 records and
16,715 source tokens per epoch without repetition. Those files belong to the
Natural Instructions branch rather than the Sapient factual-FLAN totals in
this report. Neither route includes TriviaQA evidence documents.

| Question source | Tokens/epoch | Current basis | Reservation result |
|---|---:|---|---|
| sfquiz.org.uk | 14,802,302.4 | Article 4 | Domain expired; no known historical reservation |
| odquiz.org.uk | 8,050,401.7 | Article 4 | Current endpoint unavailable; no known reservation |
| quizwise.com | 7,891,549.9 | Article 4 | Robots allows all; no TDM signal found |
| quizballs.com | 5,867,137.4 | Article 4 | No TDM signal found |
| businessballs.com | 4,902,491.4 | Article 4 | Robots expressly allows named AI agents |
| derbyshirepubquizleague.wordpress.com | 3,185,242.6 | Article 4 | No TDM signal found |
| quizguy.wordpress.com | 2,640,613.5 | Article 4 | No TDM signal found |
| wrexhamquizleague.co.uk | 2,520,997.8 | Article 4 | No TDM signal found |
| jetpunk.com | 2,495,209.0 | Article 3 | Current robots expressly states `ai-train=no` |
| quiz-zone.co.uk | 2,242,050.0 | Article 4 | No TDM signal found |
| billturnbull.quiz4free.com | 2,129,594.0 | Article 4 | No TDM signal found |
| quiz4free.com | 1,732,267.8 | Article 4 | No TDM signal found |
| triviacountry.com | 1,547,787.3 | Article 3 | Robots disallows all; effectiveness as an Article 4 reservation is uncertain |
| triviabug.com | 1,100,843.6 | Article 4 | Generic All Rights Reserved notice but no express TDM reservation |

The source-level assessment produced approximately **57,065,491.9
tokens/epoch under Article 4** and **4,042,996.3 under Article 3** before the
later dataset-level manual override described below. The detailed
machine-readable allocation and decision record are
`legal/registers/dfm9-triviaqa-source-grouping.json` and
`legal/registers/dfm9-triviaqa-source-rights.csv`.

The TriviaQA paper does not identify exact crawl dates. The collection was
complete no later than its 9 May 2017 arXiv submission; version 1.0 and the ACL
paper followed in July 2017. Current JetPunk and TriviaCountry robots signals
therefore establish current reservation evidence but do not prove that the
same signals existed when TriviaQA gathered the questions in 2016 or early
2017. Historical acquisition-time status remains unresolved.

The ACL paper itself makes only availability and research-use statements. It
says that the "dataset and code are available" from the project site, describes
the unfiltered dataset as released "to support research," and explains that
the questions were gathered from 14 trivia and quiz-league websites while the
evidence documents were collected from web search and Wikipedia. It does not
state a data licence, claim ownership of the source questions or documents,
record permission from the source sites, or discuss copyright, database
rights, terms of use, robots exclusions, or TDM reservations. The separate
repository statement that Apache-2.0 applies to code and data must therefore
be read together with the separate project-site notice that the University of
Washington does not own copyright in the included questions and documents;
neither statement appears in the ACL paper itself.

**Manual policy override, 2026-08-17:** Professor Peter Schneider-Kamp, as
project owner, accepts the official TriviaQA repository's express statement
that Apache-2.0 applies to both code and data as the operative basis for the
TriviaQA-derived training rows. This supersedes Article 3/4 as the effective
DFM9 basis for all 14 TriviaQA question-source groups, including JetPunk and
TriviaCountry. The UW ownership disclaimer, current robots findings, and
source-site provenance remain recorded as legal evidence rather than being
deleted. The source-site DAG edges are consequently informational and
non-blocking. The override covers the sampled question/short-answer
transformations, not the omitted TriviaQA evidence-document corpus.

## Result

The factual-FLAN branch is complete in the dependency DAG and cleared. Of its
10.200B tokens per epoch, approximately 3.980B are in families with a
direct/open or accepted publisher-licence basis, 6.137B are allocated wholly
to Article 4 families, no factual-FLAN family now depends on Article 3 as its
effective basis, and 82.494M belong to CoQA's mixed direct/Article 4 family.
This audit did not itself resolve the remaining Sapient branches. Superseding
update, 2026-08-18: Platypus, non-factual FLAN, and Tasksource were resolved in
`legal/reports/dfm9-sapient-flan-tasksource-platypus-audit.md`; the aggregate
retains Article 3 only for the Tasksource residual.

This conclusion is purpose-limited. It does not establish a commercial reuse
right, permission to redistribute source records, or completion of privacy,
attribution, ShareAlike, retention, or information-security controls.

## Superseded conditional Article 4 assessment

The initial audit stated that Article 4 / Danish Copyright Act section 11 b
could replace Article 3 for a
family only where the project can evidence lawful access and the absence of an
effective rights reservation at the relevant acquisition. Copies may then be
kept only as long as necessary for the TDM purpose. The project did not retain
complete acquisition-time reservation evidence and therefore did not initially
clear the alternatives. This conclusion was superseded by the project-owner
decision above for RACE, DREAM, WebQuestions, and uncovered CoQA material.

| Family | Article 4 assessment | Reason |
|---|---|---|
| RACE | plausible, conditional | Public research download and no reservation identified in the reviewed card/project material; acquisition-time machine-readable and terms evidence is missing |
| DREAM | plausible, conditional | Public research download and no reservation identified in the reviewed project material; acquisition-time evidence is missing |
| CoQA uncovered portion | plausible source-by-source | Directly licensed components do not need Article 4; the RACE-derived portion follows the RACE assessment and any other unresolved source layer must be checked separately |
| TriviaQA | weak/expensive conditional candidate | The publisher disclaims ownership of questions and documents; each third-party web source may carry its own effective reservation, which the aggregate card cannot waive |
| WebQuestions | plausible, conditional | Public research distribution and no reservation identified in reviewed metadata; acquisition-time evidence for the crowd-authored question collection is missing |

Before the later manual Apache-2.0 override, Article 3 remained the basis for
the JetPunk and TriviaCountry groups. The evidentiary cautions in this
superseded assessment remain useful for later releases and retraining.

## Evidence

- Local source mapping and sampling: `data_io/pipe_clustered/clean_flan.py`,
  `config/data/dfm9.yaml`, `data/show_analytics_dfm9.md`, and
  `wiki/pages/dfm9-plan.md`.
- RACE: <https://arxiv.org/abs/1704.04683> and
  <https://huggingface.co/datasets/EleutherAI/race>.
- SQuAD: <https://huggingface.co/datasets/rajpurkar/squad> and
  <https://huggingface.co/datasets/rajpurkar/squad_v2>.
- QuAC: <https://huggingface.co/datasets/allenai/quac>.
- ROPES: <https://huggingface.co/datasets/allenai/ropes>.
- DROP: <https://huggingface.co/datasets/ucinlp/drop>.
- HotpotQA: <https://huggingface.co/datasets/hotpotqa/hotpot_qa>.
- WikiDialog: <https://www.tensorflow.org/datasets/catalog/wiki_dialog> and
  <https://github.com/google-research/dialog-inpainting>.
- DREAM: <https://dataset.org/dream/>.
- CoQA: <https://huggingface.co/datasets/stanfordnlp/coqa>.
- TriviaQA: <https://nlp.cs.washington.edu/triviaqa/>.
- BoolQ: <https://github.com/google-research-datasets/boolean-questions>.
- Natural Questions: <https://ai.google.com/research/NaturalQuestions/download>.
- WebQuestions: <https://huggingface.co/datasets/stanfordnlp/web_questions>.
