---
type: Knowledge Collection
title: Residual Risk
description: 'Part of FlashAttention on B200: Residual Risk.'
tags:
- flashattention
- b200
- cuda
- performance
status: stable
last_updated: '2026-08-11'
confidence: high
part_of: /pages/flashattention-b200.md
collection_type: Technical Reference
---
# Residual Risk

Part of [FlashAttention on B200](/pages/flashattention-b200.md).

The MPS path uses dense SDPA, so large physical microbatches can still OOM even when the effective batch size is valid. Use gradient accumulation to keep the physical microbatch within the tested range.

## Chronological Records

### Update on (2026-05-26)

[Open the chronological record](residual-risk/chronology-update-on-2026-05-26.md).

### Update later on (2026-05-25)

[Open the chronological record](residual-risk/chronology-update-later-on-2026-05-25.md).

### Safety update on (2026-05-25)

[Open the chronological record](residual-risk/chronology-safety-update-on-2026-05-25.md).

### Superseded on (2026-05-29)

[Open the chronological record](residual-risk/chronology-superseded-on-2026-05-29.md).

### First cautious XXS-geometry ramp test, also run outside the sandbox on (2026-05-25)

[Open the chronological record](residual-risk/chronology-first-cautious-xxs-geometry-ramp-test-also-run-outside-the-sandbox-on-2026-05-25.md).

### MPS kernel benchmark harness update on (2026-05-25)

[Open the chronological record](residual-risk/chronology-mps-kernel-benchmark-harness-update-on-2026-05-25.md).

### Additional ramp on (2026-05-25)

[Open the chronological record](residual-risk/chronology-additional-ramp-on-2026-05-25.md).

### Online-softmax forward update on (2026-05-25)

[Open the chronological record](residual-risk/chronology-online-softmax-forward-update-on-2026-05-25.md).

### Backward update on (2026-05-25)

[Open the chronological record](residual-risk/chronology-backward-update-on-2026-05-25.md).

### XL-geometry experiment on (2026-05-25)

[Open the chronological record](residual-risk/chronology-xl-geometry-experiment-on-2026-05-25.md).

### True Q/K block experiments on (2026-05-25)

[Open the chronological record](residual-risk/chronology-true-q-k-block-experiments-on-2026-05-25.md).

### MPS SDPA implementation inspection on (2026-05-25)

[Open the chronological record](residual-risk/chronology-mps-sdpa-implementation-inspection-on-2026-05-25.md).

### Direct internal MPS SDPA test on (2026-05-25)

[Open the chronological record](residual-risk/chronology-direct-internal-mps-sdpa-test-on-2026-05-25.md).

### Backward-part timing update on (2026-05-25)

[Open the chronological record](residual-risk/chronology-backward-part-timing-update-on-2026-05-25.md).

### Dense-math backward experiment on (2026-05-25)

[Open the chronological record](residual-risk/chronology-dense-math-backward-experiment-on-2026-05-25.md).

### SIMD32 forward update on (2026-05-26)

[Open the chronological record](residual-risk/chronology-simd32-forward-update-on-2026-05-26.md).

### SIMD32 backward update on (2026-05-26)

[Open the chronological record](residual-risk/chronology-simd32-backward-update-on-2026-05-26.md).

### Model-path diagnostic after SIMD32 backward (2026-05-26)

[Open the chronological record](residual-risk/chronology-model-path-diagnostic-after-simd32-backward-2026-05-26.md).

### Memory readout for the same diagnostic, rerun on (2026-05-26)

[Open the chronological record](residual-risk/chronology-memory-readout-for-the-same-diagnostic-rerun-on-2026-05-26.md).

### XL model-path diagnostic on (2026-05-26)

[Open the chronological record](residual-risk/chronology-xl-model-path-diagnostic-on-2026-05-26.md).

### XL full-model dense-vs-custom timing on (2026-05-26)

[Open the chronological record](residual-risk/chronology-xl-full-model-dense-vs-custom-timing-on-2026-05-26.md).

### Five-step XL dense-vs-custom timing on (2026-05-26)

[Open the chronological record](residual-risk/chronology-five-step-xl-dense-vs-custom-timing-on-2026-05-26.md).

### Ten-step XL dense-vs-custom timing on (2026-05-26)

[Open the chronological record](residual-risk/chronology-ten-step-xl-dense-vs-custom-timing-on-2026-05-26.md).

### Ten-step L dense-vs-custom timing on (2026-05-26)

[Open the chronological record](residual-risk/chronology-ten-step-l-dense-vs-custom-timing-on-2026-05-26.md).

### Ten-step B dense-vs-custom timing on (2026-05-26)

[Open the chronological record](residual-risk/chronology-ten-step-b-dense-vs-custom-timing-on-2026-05-26.md).

### Ten-step S dense-vs-custom timing on (2026-05-26)

[Open the chronological record](residual-risk/chronology-ten-step-s-dense-vs-custom-timing-on-2026-05-26.md).

### Ten-step XS dense-vs-custom timing on (2026-05-26)

[Open the chronological record](residual-risk/chronology-ten-step-xs-dense-vs-custom-timing-on-2026-05-26.md).

### XS target-batch dense diagnostic on (2026-05-26)

[Open the chronological record](residual-risk/chronology-xs-target-batch-dense-diagnostic-on-2026-05-26.md).

### XS target-batch custom-kernel diagnostic on (2026-05-26)

[Open the chronological record](residual-risk/chronology-xs-target-batch-custom-kernel-diagnostic-on-2026-05-26.md).

### XXS full smoke run metric dip on (2026-05-26)

[Open the chronological record](residual-risk/chronology-xxs-full-smoke-run-metric-dip-on-2026-05-26.md).

### Correction on (2026-05-26)

[Open the chronological record](residual-risk/chronology-correction-on-2026-05-26.md).

### Follow-up diagnostic on (2026-05-26)

[Open the chronological record](residual-risk/chronology-follow-up-diagnostic-on-2026-05-26.md).

### Full rerun on (2026-05-26)

[Open the chronological record](residual-risk/chronology-full-rerun-on-2026-05-26.md).

### XXSwide custom rerun on (2026-05-26)

[Open the chronological record](residual-risk/chronology-xxswide-custom-rerun-on-2026-05-26.md).

### Single-step XXSwide dense-vs-custom diagnostic on (2026-05-26)

[Open the chronological record](residual-risk/chronology-single-step-xxswide-dense-vs-custom-diagnostic-on-2026-05-26.md).

### XXS FLOP estimate on (2026-05-29)

[Open the chronological record](residual-risk/chronology-xxs-flop-estimate-on-2026-05-29.md).

### XL full-run worked example on (2026-05-29)

[Open the chronological record](residual-risk/chronology-xl-full-run-worked-example-on-2026-05-29.md).

### XXL doubled-dataset worked example on (2026-05-29)

[Open the chronological record](residual-risk/chronology-xxl-doubled-dataset-worked-example-on-2026-05-29.md).

### Size-ladder update on (2026-05-29)

[Open the chronological record](residual-risk/chronology-size-ladder-update-on-2026-05-29.md).

### Parameter and FLOP estimates for the new non-wide sizes on (2026-05-29)

[Open the chronological record](residual-risk/chronology-parameter-and-flop-estimates-for-the-new-non-wide-sizes-on-2026-05-29.md).

### Ten-step XXS dense-vs-custom timing on (2026-05-26)

[Open the chronological record](residual-risk/chronology-ten-step-xxs-dense-vs-custom-timing-on-2026-05-26.md).
