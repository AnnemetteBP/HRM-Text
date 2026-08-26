---
type: Technical Reference
title: HRM-Text XL Training FLOPs
description: Recurrence-aware upper-bound calculation for HRM-Text XL training compute.
tags: [architecture, hrm, xl, training, flops]
status: stable
last_updated: 2026-08-15
confidence: high
---
# HRM-Text XL Training FLOPs

## Reference Calculation

For the DFM8 XL architecture, use `D=1536`, `I=4096`, 16 layers in each
distinct H/L recurrent module, vocabulary 262,144, `H_cycles=2`, `L_cycles=3`,
and context length 4,096. Count one multiply-add as two FLOPs and assume
`bp_steps=5` from the first optimizer step.

Five BP steps retain gradients through two H calls and three L calls. Every
token still executes all two H and six L forward calls. With backward matrix
work approximated as twice its corresponding forward matrix work, H contributes
`2 + 2*2 = 6` forward-equivalent calls and L contributes
`6 + 2*3 = 12`, for 18 recurrent forward equivalents in total.

Each transformer layer has `5*D^2 + 3*D*I = 30,670,848` matrix parameters.
The resulting dominant work per token is:

| Component | FLOPs/token |
| --- | ---: |
| Recurrent transformer linear layers | 17,666,408,448 |
| Untied vocabulary head, forward and backward | 2,415,919,104 |
| Dense attention upper bound at length 4,096 | 7,247,757,312 |
| Major operations total | 27,330,084,864 |

At 262,144 tokens per optimizer step for 1,650,000 steps, the run processes
432,537,600,000 token positions. Major operations are therefore bounded by
`1.182128931e22` FLOPs. Rounding up for RMSNorm, RoPE, activations, softmax,
loss, residuals, and other elementwise work gives a tight conservative budget
of **`1.19e22` FLOPs, or 11.9 zettaFLOPs**.

The linear/head portion alone is `8.686e21` FLOPs. Actual packed examples are
usually much shorter than 4,096 tokens, so actual attention work and total
algorithmic FLOPs should be below the 11.9-ZFLOP bound. This accounting excludes
optimizer updates, distributed communication, checkpointing, evaluation,
compiler work, and inefficiency relative to peak hardware throughput.

