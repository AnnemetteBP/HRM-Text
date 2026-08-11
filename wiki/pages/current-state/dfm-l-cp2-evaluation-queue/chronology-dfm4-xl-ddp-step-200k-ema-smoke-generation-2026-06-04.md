---
type: Operational Record
title: DFM4 XL-DDP step 200K EMA smoke generation (2026-06-04)
description: 'Chronological record from DFM L CP2 Evaluation Queue: DFM4 XL-DDP step
  200K EMA smoke generation (2026-06-04).'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state/dfm-l-cp2-evaluation-queue.md
---
# DFM4 XL-DDP step 200K EMA smoke generation (2026-06-04)

Part of [DFM L CP2 Evaluation Queue](/pages/current-state/dfm-l-cp2-evaluation-queue.md).

DFM4 XL-DDP step 200K EMA smoke generation, 2026-06-04. Confidence: high.

The `step_200000` checkpoint was smoke-tested locally with the normal eval
loader and EMA enabled:

```bash
CUDA_VISIBLE_DEVICES=7 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python - <<'PY'
from evaluation.engines import SimpleEngine

prompts = [
    "Answer with only the letter. Which is larger? A. 3 B. 7",
    "Translate to Danish: The book is on the table.",
    "Solve the arithmetic problem and answer with only the number: 17 + 25 =",
    "Svar kort på dansk: Hvad er hovedstaden i Danmark?",
]

engine = SimpleEngine(
    ckpt_path="checkpoints/dfm4/XL-ddp",
    ckpt_tag="step_200000",
    ckpt_use_ema=True,
)
outputs = engine.generate(
    prompts,
    batch_size=2,
    max_context=512,
    max_tokens=96,
    temperature=0.0,
    condition="direct",
)
for prompt, output in zip(prompts, outputs):
    print(prompt, repr(output))
PY
```

The checkpoint loaded successfully and generated coherent text with EMA:
translation produced `Bogen er på bordet.`, arithmetic produced `42`, and the
Danish capital prompt produced `København`. The simple multiple-choice prompt
answered `A.` even though the correct option was `B`, so the result verifies
that EMA is no longer token-salad at 200K, but it is not evidence of benchmark
quality. This supersedes the earlier 50K/100K observation only for the 200K
checkpoint after the DDP EMA reset/resume changes.
