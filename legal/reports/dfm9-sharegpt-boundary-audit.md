# DFM9 ShareGPT Boundary Audit

Status: completed source, transformation, copyright, and privacy triage on
2026-08-18. This is engineering evidence for qualified legal/DPO review, not
legal advice or institutional approval.

## Superseding project decision, 2026-08-18

MAN-022 resolves the training decision for this project. Professor Peter
Schneider-Kamp accepts users' deliberate one-click publication to a service
designed for public sharing, browsing, and public-API access as participant
permission for the current academic/non-commercial research training. The
ShareGPT dependency therefore has the same **operative cleared status** as
WildChat in DFM9.

This does not make the underlying evidence equivalent. WildChat documented an
explicit two-stage consent for research/product-development use and third-party
publication; no equivalent ShareGPT model-training wording was found. MAN-022
also does not treat participant text as Apache-2.0, authorize raw
redistribution or nonresearch use, or resolve privacy/GDPR and credential
controls. The pre-decision analysis below is retained as the evidence and
scope boundary underlying that decision.

## Executive finding

Pre-decision triage found ShareGPT to be a defensible **Article 3 / Danish section 11 c candidate for the
current SDU scientific-research use**, but the evidence does not support
treating the participant conversations as Apache-2.0 or as generally licensed
for model training. Users deliberately published conversations through a
one-click sharing service with public pages, browsing, and a documented read
API. That supports lawful public availability. It does not by itself prove a
copyright licence from every participant to an anonymous dataset mirror.

Article 4 is a materially weaker fallback. ShareGPT shipped a machine-readable
`robots.txt` with `Disallow: /` from its first day, while also documenting a
public conversation API. Whether that site-level robots rule was an effective
TDM reservation by the relevant conversation rightholders, and whether it
covered public-API access, is not resolved here. Article 4 should therefore not
be used for this source without a specific qualified decision.

Privacy remains independent. The retained rows contain real user prompts and
heuristic PII/credential indicators. Intentional publication is not consent to
all later personal-data processing.

## Exact local lineage

AllenAI's historical preparation script downloaded these two files from the
anonymous mirror:

- `HTML_cleaned_raw_dataset/sg_90k_part1_html_cleaned.json`
- `HTML_cleaned_raw_dataset/sg_90k_part2_html_cleaned.json`

It then used the Llama tokenizer to split conversations at 4,096 tokens,
discarded overlong turn pairs and invalid role sequences, mapped
`human`/`user` to `user` and `gpt`/`chatgpt` to `assistant`, and wrote the Tulu
records. The inspected pipeline contains no rights-authority, PII, credential,
or privacy filter. The current mirror's later “unfiltered” refusal/moralizing
filter is not the path used by Tulu; Tulu starts from the HTML-cleaned raw
files.

The reproducible local audit is
`legal/tools/audit_sharegpt_boundary.py`; aggregate output is
`legal/registers/dfm9-sharegpt-boundary-audit.csv`.

| Local artifact | Rows/chunks | Original IDs | Messages | User chars | Assistant chars |
|---|---:|---:|---:|---:|---:|
| Tulu v2 split at 4,096 | 111,912 | 74,951 | 1,071,964 | 145,408,147 | 619,662,368 |
| Tulu v2 Long | 74,312 | 74,307 | 1,028,846 | 147,467,840 | 597,209,338 |

The artifacts share **74,159 original IDs**. The split artifact has 792 IDs
absent from Long; Long has 148 absent from the split artifact. They are thus
near-duplicate source variants, not independent conversation collections. In
DFM9 they affect Tulu v2 SFT, Tulu v2 SFT Long, and the Tulu-v2 half of SciRIFF
Train Mix. The existing 1.577B-token/epoch figure is the total exposure of
those three affected effective datasets, not an exact allocation to their
ShareGPT rows.

The split artifact's median row has eight messages, with p95 24, p99 38, and a
maximum of 184. Long has median six, p95 48, p99 122, and maximum 844. This is
genuine multi-turn conversation data, often with substantial copied context,
not merely short factual prompts.

## Publication and collection evidence

The ShareGPT source repository describes a one-click extension, public
conversation pages, browsing/search, and a REST API that allowed conversations
to be written and read. The extension's share-button handler immediately
collected all visible turns and posted them to the API. The inspected code did
not display a downstream training licence or a separate publication-confirmation
dialog. Early code could also capture an avatar image, although AllenAI's
processed Tulu rows contain only messages and IDs.

The repository's first-day `robots.txt` commit on 2022-12-04 says:

```text
User-agent: *
Disallow: /
```

The original software repository did not begin with a licence file. It added
an MIT `license.md` on 2023-04-29; that licence applies to the software and
associated documentation and does not purport to license participant
conversation text.

FastChat's Vicuna documentation states that approximately 70,000 user-shared
conversations were gathered from ShareGPT with public APIs. The 2023-03-29
documentation also states that, due to legal concerns, the team might not
release the data. The anonymous HF mirror was populated on 2023-04-02 after
that documented concern. Its initial commit did not contain licence metadata;
commit `d0e706fa5cfac49bbcaf28dbdf8805f502e0e2d1` added
`license: apache-2.0` later that day at 23:43 UTC. This is historical evidence
that the mirror was presented under Apache-2.0 from its first day, but not
evidence that its uploader held participant rights.

## Copyright layers

1. **Participant prompts.** Users intentionally made conversations publicly
   viewable, but no captured ShareGPT term grants Apache-2.0 or an express model
   training right. Prompts can also embed third-party articles, emails, code,
   logs, and other works that the participant could not relicense.
2. **ChatGPT output.** OpenAI's terms captured in January through March 2023
   state that, as between OpenAI and the user, the user owned Input and OpenAI
   assigned its rights in Output to the user, subject to compliance. This
   reduces an OpenAI-ownership concern but does not transfer the user's rights
   onward to the anonymous mirror. Some machine output may not attract
   copyright at all; that is work- and jurisdiction-specific.
3. **Database and processing layers.** ShareGPT/FastChat/AllenAI selection,
   cleaning, and arrangement can have separate rights. Tulu's ODC-By release
   expressly warns that component licences continue to apply. The anonymous
   mirror's Apache tag is evidence about its asserted package terms, not proof
   of authority over every underlying work.

## Article 3 and Article 4

Directive (EU) 2019/790 Article 3 covers research organisations' reproductions
and extractions for scientific research from works to which they have lawful
access, with appropriate security and research-verification retention. Recital
14 expressly includes content freely available online as a form of lawful
access. Public pages and a documented read API make that route plausible for
the current university research, subject to institutional approval and the
project's security/retention controls.

Article 4 additionally requires that TDM use has not been expressly reserved
in an appropriate manner, including machine-readable means for online content.
The first-day robots exclusion is therefore adverse evidence. Its legal effect
is uncertain because the service simultaneously exposed a public API and the
individual conversation authors, not necessarily the platform, may hold the
relevant prompt rights. The uncertainty is enough that this audit does not
recommend Article 4 as the working basis.

## Privacy and security indicators

The audit counts matching **conversation rows**, without writing matched text
to the dossier. These are deliberately broad heuristics and include false
positives, examples, expired URLs, and synthetic credentials.

| Indicator in 74,312 Long rows | Matching rows |
|---|---:|
| Email-address pattern | 1,882 |
| Self-identification phrase | 677 |
| Public IPv4 pattern | 522 |
| Private IPv4 pattern | 683 |
| Phone-like number | 7,775 |
| Password-assignment pattern | 522 |
| Private-key block marker | 13 |
| AWS access-key pattern | 4 |
| OpenAI-style key pattern | 0 |
| Prompt apparently asking transformation of supplied source text | 2,664 |

Manual inspection of the four AWS-pattern rows found signed-resource URLs and
one row with a paired secret-looking value. Validity was not tested. This is
enough to reject any claim that HTML cleaning established privacy or secret
safety. It also supports source-specific memorisation tests and a future
credential/PII exclusion pass if this data is resampled.

## Operational decision boundary

- `LEG-046` is resolved by MAN-022 for the current academic/non-commercial
  research training. No Article 3 reliance is needed for this source under the
  project's operative classification.
- Do not describe ShareGPT participant text as Apache-2.0 in public
  documentation. Attribute the mirror and Tulu processing separately.
- Do not redistribute raw ShareGPT rows from this project.
- Treat model release as a separate output-risk question. Run canary,
  rare-string, credential-pattern, and prefix-extraction tests on ShareGPT
  cohorts before release; avoid publishing extracted examples.
- For a future nonresearch/general-use corpus, prefer replacing these rows with
  explicitly consented sources or audited synthetic conversations. Regenerating
  assistant responses alone would not resolve retained prompt rights or
  personal data.
- If retained in a later corpus, deduplicate the split and Long variants by
  original ShareGPT ID and filter likely credentials/PII before tokenization.

## Primary evidence

- ShareGPT source and API documentation:
  <https://github.com/samsumon/sharegpt/blob/main/README.md>
- First-day robots exclusion:
  <https://github.com/samsumon/sharegpt/commit/90bbf8151b76181b4022c8bea4dbc5238dd4b790>
- FastChat's contemporaneous Vicuna data statement:
  <https://github.com/lm-sys/FastChat/blob/020f6ae7569876a5cc80f06e655bdd375e42ffb5/README.md>
- Anonymous mirror metadata/history:
  <https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered>
- Anonymous mirror commit adding Apache-2.0 metadata:
  <https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered/commit/d0e706fa5cfac49bbcaf28dbdf8805f502e0e2d1>
- Original ShareGPT repository commit adding the MIT software licence:
  <https://github.com/samsumon/sharegpt/commit/9baf90ac273807693a603c35f77bce4314ee70c3>
- AllenAI preparation code:
  <https://github.com/allenai/open-instruct/blob/main/scripts/data/sft_v1_v2/prepare_tulu_v1_v2.sh>
- Archived OpenAI terms captured 2023-03-01:
  <https://web.archive.org/web/20230301000000id_/https://openai.com/terms/>
- Directive (EU) 2019/790 Articles 3 and 4:
  <https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L0790>
