# DFM9 SmolTalk and SmolTalk2 Component Audit

Status: evidence-based engineering/legal triage, not legal advice. Audit date:
2026-08-17.

## Result

SmolTalk is not one rights boundary. Its 13 train subsets resolve as follows:

- eleven have direct open or current-scope non-commercial terms; among these,
  MetaMath and NuminaMath retain mathematical problem wording, so notices and
  downstream provenance remain relevant;
- the 95,000-row OpenHermes subset follows the recorded component terms plus
  Article 4 decision, while only the 3,547-row LongAlign subset retains the
  component-level Article 3 fallback used by this project.

SmolTalk2 is likewise a mixture rather than a blanket-licensed dataset. The
published SFT recipe has 25 rows in its statistics table. Most are generated
or directly licensed. Its current Article 3 dependency is LongAlign source
documents. OpenHermes uses direct terms plus the recorded Article 4 decision;
Mixture-of-Thoughts uses the recorded residual-risk acceptance. The Tulu branch
uses separately recorded direct terms and Article 4 decisions.

The exact row-level decisions are in
`legal/registers/dfm9-smoltalk-component-audit.csv`. The SmolTalk2 card's prose
incorrectly repeats `244736` for three generated think subsets; this audit uses
the card's granular statistics table: 2,057 everyday rows, 27,436 SystemChat
rows, and 244,736 multilingual rows.

## Important qualifications

1. A generated answer does not erase rights in its prompt. This matters for
   Qwen-regenerated LongAlign, Aya, Table-GPT, Tulu, and SmolTalk rows.
2. Apache-2.0 for a newly generated layer does not automatically relicense an
   imported prompt or source document.
3. The exact 937,331-row SmolTalk2 allocation reported by the current Apertus
   statistics cannot be reconstructed from DFM's flattened local parquet:
   DFM rewrote every source label to `apertus-sft-mixture`. The upstream
   SmolTalk2 component table remains the best available lineage evidence.
4. The current Apertus Hub card reports 3,942,208 rows, while its currently
   exposed source statistics cover only 1,433,534 rows. This mismatch is an
   upstream evidence limitation, not a claim that the other rows are absent.

## Primary evidence

- `HuggingFaceTB/smoltalk` card and exact Hub size endpoint at revision
  `5feaf2fd3ffca7c237fc38d1861bc30365d48ffa`.
- `HuggingFaceTB/smoltalk2` composition and statistics at revision
  `fc6cc2103c066455aade5d7fbb346039ae36ca5e`.
- Original source cards and current declared terms listed in the component
  register.
