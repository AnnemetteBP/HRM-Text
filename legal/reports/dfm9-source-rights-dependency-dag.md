# DFM9 Source-Rights Dependency DAG

Status: engineering/legal triage, not legal advice. Generated from the authoritative declarative node and edge specifications.

## DFM Dyna Instruct

The subtree has **135 canonical nodes** and **154 dependency edges**. Computed status: **cleared**.

| Computed status | Nodes |
|---|---:|
| cleared | 135 |
| partial | 0 |
| unresolved | 0 |

### Component status

| Component | Tokens/epoch | Status |
|---|---:|---|
| Agentic Code SFT | 34,769,924 | cleared |
| Apertus SFT mixture | 3,033,512,464 | cleared |
| DA Refusals | 17,706 | cleared |
| Danish Verifiable Reasoning | 9,064,406 | cleared |
| IFBench Train | 1,262,590 | cleared |
| MT-DA DeepSeek | 8,883,200 | cleared |
| Translation 100K | 98,008,752 | cleared |
| When2Call | 3,797,583 | cleared |
| Wiki Instruct DA | 164,686,585 | cleared |
| WildChat Qwen | 189,868,452 | cleared |

### Unresolved leaves and audit boundaries

| Node | Basis / remaining issue | Completeness |
|---|---|---|

### Highest immediate resolution leverage

This simulates clearing one unresolved leaf while holding every other node constant.

| Leaf | Computed statuses changed | Effective sources reached | Tokens/epoch reached |
|---|---:|---:|---:|
| `work:sapient-upstream:task909-dialogre-prevalent-speakers` | 1 | 0 | 0.0 |
| `work:sapient-upstream:task908-dialogre-identify-familial-relationships` | 1 | 0 | 0.0 |
| `work:sapient-upstream:task907-dialogre-identify-relationships` | 1 | 0 | 0.0 |
| `work:sapient-upstream:task906-dialogre-identify-names` | 1 | 0 | 0.0 |
| `work:sapient-upstream:task903-deceptive-opinion-spam-classification` | 1 | 0 | 0.0 |
| `work:sapient-upstream:task902-deceptive-opinion-spam-classification` | 1 | 0 | 0.0 |
| `work:sapient-upstream:task871-msmarco-question-generation` | 1 | 0 | 0.0 |
| `work:sapient-upstream:task870-msmarco-answer-generation` | 1 | 0 | 0.0 |
| `work:sapient-upstream:task672-amazon-yelp-summarization` | 1 | 0 | 0.0 |
| `work:sapient-upstream:task635-allegro-reviews-answer-generation` | 1 | 0 | 0.0 |

## Whole-DFM9 expansion state

All **161 effective DFM9 sources** are present as canonical effective-dataset nodes. Some are also reused as dependencies and therefore are not graph roots. The DFM Dyna subtree is decomposed to its documented source boundaries; remaining top-level-only sources retain their current audited status until their dependencies are added.

| Dependency completeness | Nodes |
|---|---:|
| complete | 350 |
| partial | 63 |
| top_level_only | 11 |

### Next roots to expand

| Effective source | Tokens/epoch | Current status |
|---|---:|---|
| `hf:schneiderkamplab/opus-da-en-permissive` | 2,903,437,259 | cleared |
| `hf:allenai/big-reasoning-traces` | 1,656,898,949 | cleared |
| `hf:oliverkinch/danish-summarization` | 168,358,988 | cleared |
| `hf:common-pile/arxiv_papers_filtered` | 129,586,132 | cleared |
| `hf:danish-foundation-models/ai_arena_udtraek` | 45,690,600 | cleared |
| `hf:oliverkinch/danish-university-portals-bt` | 21,765,750 | cleared |
| `hf:oliverkinch/eur-lex-bt` | 16,694,550 | cleared |
| `hf:oliverkinch/instruct-bt` | 13,460,570 | cleared |
| `hf:allenai/RLVR-MATH` | 8,067,070 | cleared |
| `hf:ccdv/govreport-summarization` | 4,412,302 | cleared |
| `hf:oliverkinch/eur-lex-sum-instruct` | 2,628,790 | cleared |

The complete **11-row** work queue is `legal/registers/dfm9-source-dag-expansion-queue.csv`.

## Status semantics

- `cleared`: the node's own layer is resolved and all required children are cleared.
- `unresolved`: the node itself needs a rights/terms decision, or an inherited node lacks children.
- `partial`: the node's own layer is clear/inherited but at least one required descendant is unresolved.
- `dependency_completeness` is independent: `partial` or `top_level_only` means more lineage expansion is still required even if a current working status is recorded.

## Maintenance

Edit the declarative files under `legal/specs/dfm9-source-dag/` or use `set-status`, then rebuild:

```bash
python legal/tools/manage_dfm9_source_dag.py build
```

A source is cleared upward automatically only after every required child resolves. Shared nodes are resolved once and affect every parent path.
