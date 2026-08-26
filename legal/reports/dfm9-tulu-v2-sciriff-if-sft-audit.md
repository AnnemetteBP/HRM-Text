# DFM9 Tulu v2, SciRIFF Train Mix, and IF-SFT Audit

Status: completed source decomposition and engineering/legal triage on
2026-08-18; not legal advice or institutional approval.

## Local composition

The machine-readable inventory is
`legal/registers/dfm9-tulu-v2-sciriff-if-sft-component-audit.csv` and can be
reproduced with:

```bash
python legal/tools/audit_tulu_v2_sciriff_if_sft.py
```

| Effective source | Local rows | Finding |
|---|---:|---|
| `allenai/tulu-v2-sft-mixture` | 326,154 | 16 labels; 111,912 ShareGPT chunks |
| `allenai/tulu-v2-sft-long-mixture` | 288,554 | Same non-ShareGPT mixture; 74,312 Long ShareGPT rows, with 74,159 original IDs shared with the split artifact |
| `allenai/SciRIFF-train-mix` | 70,714 | 35,000 SciRIFF rows plus 35,714 sampled Tulu-v2 rows |
| `allenai/IF_sft_data_verified` | 31,751 | Every ID exactly matches a local Tulu-3 row across all 19 audited Tulu-3 labels |

The two Tulu-v2 artifacts have identical non-ShareGPT component counts: 98,870
FLAN/CoT, 29,810 WizardLM, 29,683 OpenOrca, 20,016 Code-Alpaca, 19,906
GPT4-Alpaca, 7,468 science rows, 7,331 OASST1, 1,018 LIMA, and 140
Ai2 hard-coded rows.

The ShareGPT variants are nearly, but not exactly, the same source set. The
111,912 split chunks map to 74,951 original IDs; Long has 74,312 rows and
74,307 unique original IDs. They share 74,159 IDs, while 792 are split-only
and 148 Long-only. This corrects the earlier shorthand that Long differed only
by chunking.

## Component findings

- FLAN/CoT and OpenOrca retain FLAN-family source expression. The existing
  MAN-013/MAN-019 Article 4 determination is applied consistently; direct
  component terms remain controlling where known.
- The six `science.*` labels are SciRIFF-related scientific task rows. MAN-014
  expressly covers SciRIFF retained in related mixtures.
- OASST1 is Apache-2.0. GPT4-Alpaca and Code-Alpaca are CC-BY-NC-4.0; LIMA is
  CC-BY-NC-SA. These terms fit the current academic/non-commercial purpose.
- OpenOrca is MIT at the package/response layer, subject to the retained FLAN
  basis. WizardLM EvolInstruct V2 is now published by the WizardLM Team with an
  MIT tag, superseding the Tulu card's historical “no license provided” note.
- The Tulu card and current ShareGPT repository display Apache-2.0, but the
  repository is an unofficial processed export of participant conversations.
  The tag does not establish that the uploader could license every user's
  expression. The focused audit found intentional public sharing and public-API
  collection, but also a first-day robots exclusion, no participant-content
  licence, official FastChat non-release due to legal concerns, and measurable
  privacy/credential indicators. **Superseding decision, 2026-08-18:** MAN-022
  accepts the deliberate publication flow as participant permission for the
  current academic/non-commercial research training. This provides the same
  operative cleared status as WildChat, but not the same explicit-consent
  evidence and not a blanket Apache-2.0 or raw-redistribution permission. See
  `legal/reports/dfm9-sharegpt-boundary-audit.md`.

Consequently both Tulu-v2 roots and SciRIFF Train Mix are **cleared for the
current research purpose**. The earlier partial status is superseded by
MAN-022. Privacy/credential safeguards and any future nonresearch use remain
separate decisions.

## IF-SFT Verified

The local IF-SFT artifact adds an instruction-following constraint to each
source prompt and replaces the response with a model-generated answer. Exact
ID joining found **31,751/31,751 matches** against the local Tulu-3 mixture and
no unmatched rows. It reaches all 19 already-audited Tulu-3 labels. The added
constraint and regenerated response are an Ai2 contribution; the retained
prompt inherits the Tulu-3 component basis.

The IF-SFT effective source is therefore **cleared by inheritance** from the
completed Tulu-3 audit, with no new Article 3 reliance. Existing Article 4
conditions for uncovered FLAN-v2 and SciRIFF expression remain applicable.

## Primary evidence

- Local cards and exact artifacts under
  `data/downloads/datasets/allenai_{tulu_v2_sft_mixture,tulu_v2_sft_long_mixture,sciriff_train_mix,if_sft_verified}`.
- Tulu v2 card: <https://huggingface.co/datasets/allenai/tulu-v2-sft-mixture>
- Tulu v2 Long card: <https://huggingface.co/datasets/allenai/tulu-v2-sft-long-mixture>
- SciRIFF Train Mix card: <https://huggingface.co/datasets/allenai/SciRIFF-train-mix>
- IF-SFT artifact: <https://huggingface.co/datasets/allenai/IF_sft_data_verified>
- WizardLM V2 release: <https://huggingface.co/datasets/WizardLMTeam/WizardLM_evol_instruct_V2_196k>
- ShareGPT export: <https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered>
- Focused ShareGPT evidence and local measurements:
  `legal/reports/dfm9-sharegpt-boundary-audit.md` and
  `legal/registers/dfm9-sharegpt-boundary-audit.csv`.
- Existing Tulu-3 audit: `legal/reports/dfm9-tulu3-mixture-audit.md`.
