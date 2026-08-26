# DFM8 XL Step 1,650,000 Evaluation Metrics

Model export: `exports/dfm8_XL_step1650000_ema_hf`

These are the finalized local EMA results at epoch `6.564012269760203`. The
table contains one headline score per evaluated task. It omits sample counts,
standard errors, confidence intervals, invalid-rate diagnostics, and MMLU
subject-level expansion. Values are shown on their native logged scale:
standard and DFM metrics are generally in `[0, 1]`, while most EuroEval metrics
are percentages in `[0, 100]`.

| Suite | Task | Metric | Value |
|---|---|---|---:|
| Standard | ARC | Accuracy | 0.798600 |
| Standard | BoolQ | Accuracy | 0.878300 |
| Standard | DROP | F1 | 0.835275 |
| Standard | GSM8K | Accuracy | 0.869584 |
| Standard | HellaSwag | Accuracy | 0.672700 |
| Standard | MATH | Accuracy | 0.453005 |
| Standard | MMLU | Accuracy | 0.584650 |
| Standard | WinoGrande | Accuracy | 0.732400 |
| DFM | DaLA | Macro F1 | 0.961422 |
| DFM | Danish Citizen Tests | Accuracy | 0.746789 |
| DFM | GEC-DaLA | Exact match | 0.859375 |
| DFM | Generative Talemaader | Judge accuracy | 0.000000 |
| DFM | GovReport | BERTScore F1 | 0.859687 |
| DFM | HumanEval | Sanitized verify accuracy | 0.567073 |
| DFM | IFEval-DA | Final accuracy | 0.666767 |
| DFM | MultiWikiQA | Exact match | 0.648926 |
| DFM | NordjyllandNews | BERTScore F1 | 0.885657 |
| DFM | PIQA-DA | Accuracy | 0.537037 |
| DFM | WMT24++ EN-DA | chrF3++ | 0.538578 |
| EuroEval | Angry Tweets | Macro F1 | 71.075957 |
| EuroEval | BFCL v2 | Tool-calling accuracy | 0.560000 |
| EuroEval | CNN/DailyMail | chrF3++ | 35.240687 |
| EuroEval | CoNLL EN | Micro F1 | 68.512135 |
| EuroEval | Danish Citizen Tests | Accuracy | 64.555556 |
| EuroEval | DaNE | Micro F1 | 42.959231 |
| EuroEval | Danske Talemaader | Accuracy | 52.812500 |
| EuroEval | HellaSwag EN | Accuracy | 42.109375 |
| EuroEval | HellaSwag DA | Accuracy | 54.296875 |
| EuroEval | IFEval EN | Instruction accuracy | 74.349664 |
| EuroEval | IFEval DA | Instruction accuracy | 71.799882 |
| EuroEval | Life in the UK | Accuracy | 51.132812 |
| EuroEval | MultiWikiQA DA | F1 | 78.176976 |
| EuroEval | Nordjylland News | chrF3++ | 36.753586 |
| EuroEval | ScaLA DA | Macro F1 | 59.571365 |
| EuroEval | ScaLA EN | Macro F1 | 80.237952 |
| EuroEval | SQuAD | F1 | 75.383343 |
| EuroEval | SST-5 | Macro F1 | 66.423728 |
| EuroEval | VALUE EN | European values | 0.995094 |
| Expanded DFM | AGIEval | Choice accuracy | 0.375884 |
| Expanded DFM | BBH | Accuracy | 0.289124 |
| Expanded DFM | CommonsenseQA | Choice accuracy | 0.740377 |
| Expanded DFM | CoQA | F1 | 0.624518 |
| Expanded DFM | HumanEval+ | Verify accuracy | 0.493902 |
| Expanded DFM | MBPP | Verify accuracy | 0.533074 |
| Expanded DFM | MBPP+ | Verify accuracy | 0.611640 |
| Expanded DFM | MMLU-Pro | Choice accuracy | 0.248088 |
| Expanded DFM | Natural Questions Open | F1 | 0.125008 |
| Expanded DFM | OpenBookQA | Choice accuracy | 0.796000 |
| Expanded DFM | PIQA EN | Choice accuracy | 0.000000 |
| Expanded DFM | Social IQa | Choice accuracy | 0.504606 |
| Expanded DFM | SQuAD | F1 | 0.801401 |
| Expanded DFM | TriviaQA | F1 | 0.212209 |
| Expanded DFM / MC9 | ARC Challenge | Choice accuracy | 0.773038 |
| Expanded DFM / MC9 | ARC Easy | Choice accuracy | 0.874579 |
| Expanded DFM / MC9 | BoolQ | Pattern accuracy | 0.880428 |
| Expanded DFM / MC9 | HellaSwag | Choice accuracy | 0.621091 |
| Expanded DFM / MC9 | WinoGrande | Choice accuracy | 0.728493 |

Notes:

- The MBPP+ value is the corrected rerun (`0.611640`), replacing the initial
  broken result (`0.035979`).
- `Generative Talemaader=0` and expanded-DFM `PIQA EN=0` are the raw finalized
  local values and warrant scorer/judge validation before publication.
