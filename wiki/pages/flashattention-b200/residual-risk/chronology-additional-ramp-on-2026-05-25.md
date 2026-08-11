---
type: Technical Reference
title: Additional ramp on (2026-05-25)
description: 'Chronological record from Residual Risk: Additional ramp on (2026-05-25).'
tags:
- flashattention
- b200
- cuda
- performance
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/flashattention-b200/residual-risk.md
---
# Additional ramp on (2026-05-25)

Part of [Residual Risk](/pages/flashattention-b200/residual-risk.md).

Additional ramp on 2026-05-25:

`scripts/debug_mps_prefixlm_kernel.py` now has `--forward-only`, which skips backward parity/timing so larger forward candidates can be tested without the known slow custom backward dominating runtime.

```text
1024 tokens, 8 seqs x 128 tokens, heads=2, head_dim=128:
dense forward-only best of 5: 7.666 ms
kernel forward-only best of 5: 2.277 ms
tiled_q4_hdim128 forward-only best of 5: 2.692 ms
dense backward-only best of 5: 2.346 ms
kernel backward-only best of 5: 2.594 ms
dense forward+backward best of 5: 11.340 ms
kernel forward+backward best of 5: 4.986 ms

2048 tokens, 16 seqs x 128 tokens, heads=2, head_dim=128:
dense forward-only best of 3: 15.469 ms
kernel forward-only best of 3: 3.671 ms
tiled_q4_hdim128 forward-only best of 3: 4.826 ms
dense backward-only best of 3: 4.142 ms
kernel backward-only best of 3: 4.487 ms
dense forward+backward best of 3: 23.458 ms
kernel forward+backward best of 3: 9.056 ms

4096 tokens, 16 seqs x 256 tokens, heads=2, head_dim=128:
dense forward-only best of 5: 16.973 ms
kernel forward-only best of 5: 15.398 ms
tiled_q4_hdim128 forward-only best of 5: 20.431 ms

8192 tokens, 16 seqs x 512 tokens, heads=2, head_dim=128:
dense forward-only best of 3: 20.453 ms
kernel forward-only best of 3: 67.972 ms
tiled_q4_hdim128 forward-only best of 3: 83.531 ms
```

Conclusion: the current custom kernel is useful only as a correctness/memory prototype for short sequences. The q4 tiled-forward experiment shares K loads across query rows, but it is not a real FlashAttention-style key/value block tile; the extra barriers outweigh the reuse at realistic context lengths. The next viable MPS kernel must tile over key/value blocks and maintain online softmax state (`m`, `l`, and output accumulators) per query, then redesign backward around the same block structure. Confidence: high for the measured ramp; confidence: medium for the specific next-kernel design direction.
