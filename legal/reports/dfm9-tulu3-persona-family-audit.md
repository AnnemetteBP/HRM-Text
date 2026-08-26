# DFM9 Tulu 3 Persona Family Audit

Status: engineering/legal evidence triage, not legal advice. Audit date:
2026-08-17.

## Result

The four directly sampled Tulu 3 Persona datasets contribute 234,939 rows and
251,016,144 tokens per DFM9 epoch. The same family is reused through DOLCI,
Tulu/OLMo mixtures, and DFM Dyna under older aliases, filtered subsets, and the
49,980-row grade-school-math variant.

The family is cleared for current academic/non-commercial scientific-research
training without Article 3 reliance. This conclusion combines:

- Ai2's ODC-By release of the five Persona subsets in the Tulu 3 mixture;
- PersonaHub's CC-BY-NC-SA-4.0 release, which permits the present
  non-commercial research use subject to attribution and ShareAlike scope;
- Ai2's 33 manually authored instruction-following seeds and the openly
  released IFEval constraint taxonomy;
- customer ownership/assignment of GPT-4o and Claude 3.5 Sonnet outputs under
  the provider terms applicable to the generation period.

The public artifacts do not preserve Ai2's account-specific service agreement
or a generation ledger proving compliance for each call. That contractual
evidence limitation remains recorded, but it does not create a source-work TDM
problem or block the current research use. Reassess commercial use and retain
all ODC-By, PersonaHub NonCommercial/ShareAlike, IFEval, and model-output
notices.

## Construction lineage

The Tulu 3 report states that all persona synthesis used
`GPT-4o-2024-08-06` unless otherwise noted. Approximately 250,000 PersonaHub
personas conditioned generation:

| Subset | Rows | Construction |
|---|---:|---|
| Persona MATH | 149,960 | GPT-4o generated zero-shot persona-grounded problems and multistep solutions |
| Persona GSM/grade | 49,980 | GPT-4o generated persona-grounded grade-school problems and solutions |
| Persona Algebra | 20,000 | GPT-4o persona-grounded algebra generation; released as a named ODC-By Tulu subset |
| Persona Python | 34,999 | GPT-4o generated problems; Claude 3.5 Sonnet generated Python programs |
| Persona IF | 29,980 | GPT-4o expanded 33 Ai2-authored examples spanning 25 IFEval constraint types and generated responses |

The `math-filtered` and `math-grade-filtered` releases only retain examples for
which GPT-4o reached a majority vote over five completions. Filtering does not
introduce a new source-rights layer. The older `tulu-3-personas-math` and
`tulu-3-personas-algebra` labels are treated as aliases of the corresponding
SFT releases.

## Generator terms

OpenAI's terms assign its right, title, and interest in output to the customer,
subject to input rights and service-policy compliance. Anthropic's January 2024
commercial terms likewise state that the customer owns outputs and assign any
Anthropic output rights to the customer. Ai2 then released the resulting
datasets under ODC-By while explicitly warning that third-party model terms
also apply.

These clauses support Ai2's ability to release the generated layer. They do not
prove that every generation request complied with account-specific contractual
conditions, and they do not erase rights in conditioning material. PersonaHub
and IFEval are therefore represented as separate required DAG children rather
than being absorbed into a generic synthetic-data label.

## Evidence

- Tulu 3 report, especially sections 3.1 and 4.1.1 and footnote 6.
- Tulu 3 SFT mixture and individual subset cards.
- `proj-persona/PersonaHub` card and Tencent PersonaHub repository.
- Google Research IFEval repository and repository-wide data/code terms.
- OpenAI output-ownership terms and Anthropic January 2024 commercial terms.
- Local DFM9 parquet row and token counts.
