# DFM Mimir v1 Energy Estimate

**Status:** Engineering estimate; actual metered energy unavailable  
**Estimate date:** 2026-08-15

## Evidence and Method

The released checkpoint was trained for 1,650,000 optimizer steps on eight
NVIDIA B200 GPUs. The technical report states an average step time below 1.1
seconds. Treating 1.1 seconds as an upper bound gives less than 1,815,000
seconds, or **504.17 active accelerator hours**. This is consistent with the
report's statement that active training took just under three weeks.

NVIDIA documents B200 SXM as configurable up to 1 kW per GPU. It documents a
DGX B200 maximum system input of approximately 14.3 kW. The actual UCloud node
is not established to be a DGX B200, so the system figure is an analogue, not a
claim about the allocated host.

| Scenario | Calculation | Energy upper bound |
|---|---:|---:|
| GPU-only nameplate | 8 GPUs x 1.0 kW x 504.17 h | **4,033 kWh** |
| DGX-B200 system analogue | 14.3 kW x 504.17 h | **7,210 kWh** |

Sources: [NVIDIA HGX B200 component specification](https://docs.nvidia.com/enterprise-reference-architectures/hgx-ai-factory-h100-h200-b200/latest/components.html),
[NVIDIA DGX B200 system specification](https://docs.nvidia.com/dgx/dgxb200-user-guide/introduction-to-dgxb200.html).

## Limitations

- These figures use maximum configured/nameplate power, not measured draw.
- The report's step time is rounded and does not provide segment-level timing.
- Failed/repeated work, compilation, checkpointing, evaluation, synthetic-data
  generation, storage, networking, and idle allocation are excluded.
- Host type, CPU power, cooling, facility overhead, PUE, and energy source are
  unknown.
- Checkpoint mtimes show a calendar span from at least 2026-06-20 (step 10,000)
  to 2026-07-21 (step 1,650,000), but interruptions and evaluations make that
  unsuitable as active-energy duration.

## Required Closure Evidence

Request job or facility telemetry from the infrastructure provider. If it is
unavailable, the accountable compliance owner must approve an estimate method,
state whether PUE is included, and decide whether the GPU-only or system-level
bound is reported. This document does not close LEG-028.
