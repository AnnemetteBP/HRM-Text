---
type: Technical Reference
title: Optional Global Gradient Clipping
description: Configuration, scaling semantics, metrics, and parity evidence for conservative gradient clipping.
tags: [training, stability, gradients, fsdp]
status: stable
last_updated: 2026-08-30
confidence: high
sources:
  - id: adam-atan2-paper
    resource: https://arxiv.org/abs/2407.05872
    title: Scaling Exponents Across Parameterizations and Optimizers
  - id: adafactor-paper
    resource: https://arxiv.org/abs/1804.04235
    title: Adafactor - Adaptive Learning Rates with Sublinear Memory Cost
  - id: stable-adamw-paper
    resource: https://arxiv.org/abs/2304.13013
    title: Stable and low-precision training for large-scale vision-language models
  - id: spam-paper
    resource: https://arxiv.org/abs/2501.06842
    title: SPAM - Spike-Aware Adam with Momentum Reset for Stable LLM Training
  - id: adagc-paper
    resource: https://arxiv.org/abs/2502.11034
    title: AdaGC - Improving Training Stability for Large Language Model Pretraining
---
# Optional Global Gradient Clipping

Training supports `gradient_clip_norm`, a positive global L2 threshold in
mean-gradient units. Its default is `null`, which preserves the prior training
path and performs no gradient-norm calculation, collective, clipping, or extra
metric logging. Clipping is applied once after all gradient-accumulation
microbatches and before `optimizer.step()`.

Training also supports the independent null-default `gradient_skip_norm` guard.
When the pre-clip norm exceeds this mean-unit threshold, the data/global step
is consumed but `optimizer.step()` is not called. Parameters, decoupled weight
decay, AdamATan2's internal step and moments, and EMA therefore remain
unchanged. Gradients are cleared normally. `gradient_skip_max_consecutive`
defaults to three; reaching it writes a regular resumable step checkpoint at
the consumed data cursor and exits cleanly. The guard currently rejects models
with persistent carry because correct carry rollback has not been defined; all
current HRM `nocarry` training architectures are supported.

When enabled, training logs the pre-clipping norm as `train/grad_norm`, the
applied coefficient as `train/grad_clip_coefficient`, and a binary
`train/grad_clipped`. The threshold and logged norm use the same units. The
FSDP2 path divides the norm and threshold comparison by `WORLD_SIZE` because
this repository intentionally retains summed gradients after disabling FSDP's
default gradient division. This keeps the configured value independent of
world size and aligned with mean-gradient conventions.

## Verified XXL FSDP2 Behavior

On 2026-08-30, two non-W&B, eight-GPU XXL runs resumed independently from
`checkpoints/dfm8/XXL-1epoch/fsdp2_ephemeral_step_223500`. Both used
`fsdp_shard_degree=8`, global batch 262144, gradient accumulation 4, and ten
steps. The control used the default null setting. The diagnostic run used
`gradient_clip_norm=1e9`, exercising norm calculation without intentionally
clipping.

The diagnostic run reported norms from 0.1638 to 0.1995, with mean 0.1791.
Every coefficient was 1.0 and every `train/grad_clipped` value was 0. Median
step time was 2.645 seconds versus 2.591 seconds for the null control, about
2.1% overhead. The independently executed FSDP runs had closely matching but
not bit-identical metrics and state fingerprints, so this establishes
behavioral rather than exact-bit parity.

For this observed window, a threshold of 2.0 would be roughly ten times the
largest ordinary norm and therefore very lenient. It would target only major
gradient excursions, not routinely constrain training. A diagnostic run with
a high threshold can be used to collect a longer norm distribution before
choosing a production threshold.

Local artifacts from the parity check are under
`/tmp/hrm-gradclip-parity-20260830-{null,high-v3}*`; they are disposable and
were not logged to W&B.

## AdamATan2 limitation and the 226K excursion

Production evidence through step 228045 shows that global gradient clipping is
not, by itself, a sufficient stability mechanism for this optimizer and
architecture. The first abnormal norm appeared at step 226230 while loss was
still normal. Norms then rose from approximately 1 to 3, 198, and above 2,000
before loss collapsed roughly 20--25 steps later. The largest reported
pre-clip norm was about 3.66 million. Threshold 1.0 operated mechanically, but
the instability persisted until the last clipped measurement at step 227450.

`AdamATan2` updates first and second moments from the same globally scaled
gradient and applies `atan2(exp_avg, sqrt(exp_avg_sq))`. Scaling a gradient by
one global coefficient therefore scales its new first moment and squared scale
in related ways; the resulting adaptive update is substantially
scale-invariant. Global norm clipping changes interaction with historical
moments but does not directly cap the optimizer's parameter-update norm. A
threshold of 1.0 also permits an accepted norm about five times the ordinary
0.18--0.20 range. Repeated updates at that bound can still alter moments and
parameters materially.

Sampler-only replay from the exact step-220000 cursor found no sequence-length
distribution boundary around the event. Median sequence length remained about
141--143 tokens, p95 about 1,104--1,125, p99 about 2,811--2,872, and maximum
4096 before, during, and after the collapse. Inspection of long examples in
the triggering batches found the usual mixture of math reasoning, code,
Danish encyclopedic tasks, restoration tasks, and long agent/tool prompts, but
no single obvious malformed row. This weakens broad length or source-mixture
explanations without ruling out one sequence that triggers unstable recurrent
activations.

The next diagnostic should record, only when the pre-clip norm crosses a
trigger such as 0.5, per-module gradient norms, activation maxima by H/L cycle,
and optimizer update RMS/max. An exact replay from the step-220000 checkpoint
through approximately step 226500 can then compare threshold 1.0 with 0.5, an
optimizer-native guard, and/or a lower learning rate. Because the run recovered
after step 227500, do not attribute recovery causally to clipping without that
controlled replay.

## FSDP2 post-clip verification

Verified on 2026-08-30 with the installed PyTorch 2.11.0 FSDP2 and DTensor
implementations. A two-rank CPU/Gloo test used a real `fully_shard` module,
`set_gradient_divide_factor(1.0)`, and
`set_force_sum_reduction_for_comms(True)`. Its known sum-reduced gradient had a
raw global norm of `32.863353450`; the repository helper reported the expected
mean-gradient norm `16.431676865`. With `max_norm=1.0`, the independently
all-reduced post-clip norm was `1.999999934` raw, or `0.999999967` in mean
units. Both ranks reported the same replicated norm and coefficient.

The retained regression test is
`tests/test_gradient_clipping_fsdp.py`. It exercises PyTorch's actual DTensor
foreach norm and in-place multiply dispatch, not a local-tensor approximation.
Inspection of the installed FSDP2 reduction source also confirms that forcing
sum reduction with a divide factor of one applies neither pre- nor
post-division. Together, these results rule out an FSDP world-size scaling,
sharded-norm, or coefficient-application malfunction. A low-threshold
NCCL/GPU test when the training GPUs are free would close the much narrower
possibility of a backend-specific defect, but there is currently no evidence
for one.

The investigation found one telemetry-only discrepancy: the logged coefficient
originally reapplied PyTorch's `1e-6` denominator epsilon after converting the
norm to mean units. The actual clipping used the correct raw summed units. The
metric now derives from the raw norm and raw threshold, exactly matching the
coefficient PyTorch applies. The former sub-parts-per-million reporting
difference at ordinary norms did not affect gradients or training.

## Skip-before-moments implementation

Implemented on 2026-08-30 as an optional training guard. FSDP2's replicated
global norm supplies the decision, and a scalar distributed MAX enforces
identical control flow on every rank even at the threshold. Triggered steps are
logged immediately rather than waiting for `log_interval` and expose
`train/optimizer_step_skipped` plus `train/consecutive_gradient_skips` alongside
the pre-clip `train/grad_norm`. A below-threshold step follows the unchanged
optimizer path.

The integration test `tests/test_gradient_skip.py` verifies that a triggered
step leaves the parameter, AdamATan2 step counter, first moment, second moment,
and EMA unchanged byte-for-byte and clears the gradient. It also verifies the
normal below-threshold update and the explicit stateful-carry rejection.

The running DFM8 XXL process launched from step 223500 was deliberately not
restarted and therefore does not acquire code loaded after its launch. The
pending `step_250000` to `step_268857` row in scheduler plan
`logs/scheduler/dfm8_XXL_1epoch_steps50k_100k_persistent_vllm_20260725`
was updated under the plan lock to use `gradient_skip_norm=1.0` and
`gradient_skip_max_consecutive=3` together with the existing clip threshold
1.0.

## AdamATan2-native protection

Raw-gradient clipping is structurally weak for AdamATan2. In a local first-step
check with weight decay disabled, gradient magnitudes `1e-3`, `1`, `1e3`, and
`1e6` each produced the identical parameter delta `-2.990059e-4` at learning
rate `3e-4`. The first and second moments scale together, leaving the `atan2`
direction unchanged. Historical moments make later steps less exactly
scale-invariant, but do not turn raw clipping into a direct update bound.

The preferred optimizer-native safeguard is to clip the proposed adaptive
update, not the incoming gradient. For the current implementation, define the
dimensionless proposed direction per parameter as
`atan2(exp_avg, sqrt(exp_avg_sq) / sqrt(bias_correction2)) / bias_correction1`.
Measure its global RMS and maximum before applying `lr * direction`, and scale
the direction only when its RMS exceeds a calibrated threshold. RMS is more
portable than a global L2 norm because it does not grow with the square root of
the model's parameter count. A memory-conservative implementation can use two
optimizer passes: update moments and accumulate direction sum-of-squares,
globally reduce the scalar, then recompute and apply the scaled direction. It
does not need to retain a full extra update tensor.

Before selecting a threshold, collect proposed-update RMS/max during healthy
steps and around a replayed excursion. An arbitrary cap risks changing the
optimizer continuously. For rare gross anomalies, a pre-moment **skip-step
guard** is the simpler conservative protection: if the mean-unit gradient norm
exceeds a separately configured anomaly threshold, zero gradients and advance
the data step without updating parameters, moments, or EMA. This directly
prevents optimizer-state contamination, unlike rescaling. A temporary learning
rate backoff is another direct update bound. Keep ordinary gradient clipping as
a diagnostic and secondary guard, not the primary AdamATan2 stability control.

### Simulation refinement (2026-08-30)

**Superseded:** the preceding unqualified preference for clipping the global
RMS of AdamATan2's actual `atan2` direction is too broad. It remains useful
telemetry and may catch some stale-preconditioner failures, but it did not
detect a pure gradient-scale spike in the controlled simulation below.

`scripts/simulate_adam_atan2_stability.py` ran the repository's exact moment,
bias-correction, and `atan2` equations over 8,192 dimensions. It compared a
normal global norm of `0.2` with a `200.0` spike, matching the observed
three-order-of-magnitude early excursion ratio. Directions were 95% correlated
during healthy steps. Corrupted cases replaced the event direction with random
dense directions. Each guarded run was compared with a clean run using the
same guard. The retained result is
`logs/adam_atan2_stability_simulation_20260830.json`.

The update-RMS cap was calibrated to 110% of the healthy p99: healthy median
`0.5843`, cap `0.6453`. The spike's maximum actual AdamATan2 direction RMS was
only `0.5878`, so it never activated. This is expected: `atan2` already bounds
coordinate magnitudes, while a gradient spike can rotate many coordinates and
contaminate moments without increasing global direction RMS.

| Corrupted event | Guard | Final parameter divergence (LR units) | Direction recovery | Interpretation |
| --- | --- | ---: | ---: | --- |
| single step | none | 45.02 | 245 steps | One spike contaminated moments for hundreds of steps. |
| single step | current raw clip at 1.0 | 4.88 | 39 steps | Historical moments make raw clipping materially useful despite scale invariance. |
| single step | skip before moments | **0.69** | **1 step** | Strongest protection for an isolated detected outlier. |
| single step | global update-RMS cap | 45.02 | 245 steps | Did not trigger. |
| single step | 0.1x LR for 250 steps | 61.45 | 250 steps | Limited immediate motion but retained contaminated moments and training lag. |
| 100 steps | none | 73.15 | 299 steps | Sustained corruption caused persistent deviation. |
| 100 steps | current raw clip at 1.0 | 44.17 | 92 steps | Helped but continued updating on corrupted directions. |
| 100 steps | skip before moments | **38.15** | **33 steps** | No corrupt movement; divergence mainly represents 100 intentionally missed clean updates. |
| 100 steps | global update-RMS cap | 73.15 | 299 steps | Again did not trigger. |
| 100 steps | 0.1x LR for 250 steps | 77.04 | 299 steps | Backoff alone did not protect optimizer state. |

This synthetic state simulation cannot model recurrent activation feedback or
predict model loss. Its robust conclusions are narrower: skip-before-moments
is effective when a raw-norm detector has high precision; raw clipping still
reduces moment contamination; LR backoff alone is insufficient; and global
actual-update RMS is not a reliable detector for AdamATan2 scale spikes. For
several consecutive skips, stop and roll back rather than silently consuming a
long section of the corpus.

### Production skip-only trial at step 229500 (2026-08-30)

The DFM8 XXL run was stopped just after the complete
`ephemeral_step_229500` checkpoint and resumed with
`gradient_clip_norm=null`, `gradient_skip_norm=1.0`, and optimizer/EMA state
preserved. This was a direct production test of replacing clipping with the
pre-moment skip guard at the same threshold.

The replacement was not operationally equivalent at this data boundary. The
first attempt skipped steps 229501, 229503, 229504, and 229505; three
consecutive skips produced the protected regular checkpoint `step_229505`.
A second attempt skipped 229506--229508 consecutively and produced
`step_229508`. A bounded diagnostic continuation then skipped all twenty steps
229509--229528. Measured norms included `8.50684`, `9.16234`, `27.7486`,
`596.117`, `1260.95`, and `1375.56`. It saved `step_229528` and stopped without
allowing any of those gradients to update parameters, AdamATan2 moments,
weight decay, or EMA.

This was verified directly from the two production DCP checkpoints. SHA-256
comparisons for `H_level.core.layers.0.attn.o_proj.weight` and that parameter's
optimizer `step`, `exp_avg`, `exp_avg_sq`, and `param_ema` tensors were all
byte-identical between `step_229508` and `step_229528`. The advancing training
step therefore reflects consumed batches only; it does not conceal optimizer
or EMA updates.

The forward loss did **not** remain abnormally high during these skips. W&B
history for steps 229506--229528 has mean loss `1.075978`, range
`0.962230--1.161749`; the preceding sparse clipped samples at steps
229400--229505 have mean `1.096311`, range `1.016887--1.197025`. The anomaly is
therefore in the backward sensitivity, not the scalar objective value. For an
unrolled recurrent model, a normal averaged token loss can coexist with a very
large parameter gradient when products of recurrent Jacobians amplify the
backward signal. Skipping also freezes the model while moving to new batches,
so it cannot itself move the parameters out of such a locally unstable region.

By contrast, sparse five-step telemetry from the preceding clipped trajectory
reported norms of about `0.20--0.64` around steps 229400--229505. The new
evidence is consistent with a contiguous anomalous-data region whose clipped
updates helped the model cross the boundary, while strict skipping left the
model unchanged and caused later batches to remain over threshold. It does
not establish a gradient-scaling bug: the skip-only process reported the
actual pre-threshold global norms, and all ranks made the same decision.

**Superseded:** do not treat skip-before-moments at the clipping threshold as a
drop-in production replacement for clipping. Keep the circuit breaker bounded
and require a deliberate policy choice before continuing: use a separately
calibrated catastrophic skip threshold, use a hybrid clipping/skip policy, or
identify and filter the source region. The current scheduler row remains
failed at the protected `step_229528` boundary rather than automatically
consuming more data.

### Same-checkpoint clipping/hybrid comparison (2026-08-30)

Four non-W&B branches restarted from `ephemeral_step_229500`. Each requested
at most 50 steps, logged every step locally, and wrote no production
checkpoint. Results are retained under
`logs/training/dfm8_XXL_1epoch/gradient_guard_ab_229500`.

| Policy | Steps completed | Updates | Skips | Mean loss | Last-5 loss | Median raw norm | Maximum raw norm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clip 1 only | 50 | 50 | 0 | 1.175387 | 1.338697 | 6.135 | 1004.55 |
| clip 1, skip 10 | 12 | 2 | 10 | 1.086313 | 1.059792 | 675.004 | 10684.45 |
| clip 1, skip 100 | 9 | 2 | 7 | 1.112255 | 1.116856 | 1169.203 | 268866.66 |
| clip 1, skip 1000 | 14 | 7 | 7 | 1.100629 | 1.059434 | 2181.776 | 3042207.75 |

The first raw norm was about 880. In the clipping-only branch, accepting its
clipped update was followed by norms 1.873, 4.078, 1.024, 0.214, and 0.248.
Branches that skipped early large gradients instead remained in a
high-sensitivity state and eventually hit five consecutive skips. Even a
threshold of 1000 failed to cross the region. Skip decisions can therefore
create a self-sustaining cascade here; increasing the threshold does not yield
a robust catastrophic-only guard.

The production run was restarted from the untouched
`ephemeral_step_229500` with `lr=2.5e-4`, `gradient_clip_norm=1.0`, and
`gradient_skip_norm=null`. Both remaining scheduler training segments use
those settings. Further skip-policy work should be offline and should consider
source identification or an optimizer-native safeguard; it must not be
enabled on this production boundary without a successful longer replay.

### Thirty-minute production stability watch (2026-08-30)

The resumed W&B run `peter-sk-sdu/DFM5/40j5y877` is monitored every 30
minutes by `scripts/monitor_training_stability.py`. The watcher summarizes the
latest 100 W&B history steps, process presence, and aggregate GPU utilization;
it appends machine-readable snapshots to
`logs/training/dfm8_XXL_1epoch/stability_30m.jsonl`. It is visible in tmux
window `hrm-7:4` (`stability-30m`) and exits after observing target step
268857. Transient W&B failures are logged and retried rather than terminating
the watcher.

The first production snapshot at step 230050 was healthy: median loss 1.0421,
maximum loss 1.1537, median/p95/maximum raw gradient norms
0.1879/0.2115/0.2627, zero clipping events among 20 sampled W&B rows, and
100% mean utilization across eight GPUs. This is a short post-event window,
not evidence that the earlier instability cannot recur.

That caution was realized in the next interval. The 13:15 snapshot at step
230690 had median loss 7.0203, maximum loss 9.5234, median raw gradient norm
40.916, maximum norm 7510.15, and 19 clipped samples out of 20. By step 231335
the median loss had recovered to 1.2041, but 15 of 20 samples still clipped.
An additional live check at step 231405 reported median loss 1.2888, median
raw norm 16.146, maximum norm 844.94, and 17 of 20 samples clipped. The run is
therefore executing and partially recovered, but remains in an active
high-gradient episode; do not classify it as stable solely from its current
finite loss.

The recurrence persisted later on 2026-08-30. Step 231975 briefly returned to
an ordinary window with median loss 1.0870 and no clipping, but every sampled
update was clipped in the scheduled windows ending at steps 232610, 233245,
and 233880. A live check at step 234125 had median/maximum loss 2.6122/4.6813,
median/p95/maximum raw norms 196.70/923.53/1598.03, and 20 clipping events in
20 samples. The latest fully written ephemeral at that check was
`fsdp2_ephemeral_step_234000`. This trajectory is actively unstable despite
finite loss and continued throughput; stopping at a complete checkpoint is
preferable to assuming that clipping alone will restore durable stability.

Sampler replay from the regular step-230000 cursor again found no broad length
boundary. Across baseline (230001--230200), first-spike (230550--230750),
recovered (231850--232050), relapse (232500--232700), and current
(233900--234125) windows, median sequence length stayed 140--143 tokens, p95
stayed 1106--1118, p99 stayed 2845--2887, and every window reached 4096. Median
response length was 32 throughout, with response p95 610--620. The tokenized
source tree needed for task-family attribution is not present in the Mimir
workspace, so this result rules out only a broad length/target-length shift,
not an individual pathological row or source.

### Batch-size interpretation

The active geometry is global batch 262,144 tokens, eight ranks, and GAS 4,
which gives an 8,192-token physical microbatch per rank. Raising global batch
through additional accumulation can reduce ordinary gradient-direction noise
and dilute one exceptional microbatch. It does not change recurrent depth,
per-sequence activation stability, or BF16 behavior. The observed anomalous
norms are thousands of times the ordinary approximately 0.2 norm, so a 2x
batch increase cannot reliably average away a truly pathological sequence.

At fixed data volume, doubling global batch also halves optimizer-step count.
Any apparent stabilization then combines better averaging with fewer
AdamATan2 updates per token and may reduce learning progress. Do not scale LR
up with batch size during this incident. Treat global batch 524,288 at GAS 8
and unchanged physical microbatch/LR as a controlled replay arm, not as the
primary production remedy.

Follow-up at step 235155 still had 20 clipping events in 20 sampled rows,
median loss 1.5106, and median raw norm 92.59. A live window at step 235720
showed partial recovery: median/maximum loss 1.2186/1.3197 and median raw norm
1.593, but 14 of 20 rows still clipped and maximum norm remained 171.54. The
latest complete ephemeral was step 235500. Treat this as improving but not yet
stable; an ordinary window should return near the historical approximately
0.2 norm with clipping frequency near zero.

The run subsequently reached that recovery criterion. The scheduled window at
step 236420 had median norm 0.2024 and zero clipping; step 237055 had four
isolated clipped samples but median norm remained 0.2306. A live window at step
237605 was fully ordinary again: median/maximum loss 1.0983/1.2128,
median/p95/maximum norm 0.1935/0.2127/0.2276, zero clipping in 20 samples, and
mean token/exact accuracy 0.7529/0.2506. The latest complete ephemeral was
step 237500. This establishes recovery from the episode, not durable immunity
from another recurrence.

Recovery persisted through the next checks. Scheduled windows ending at
237690 and 238320, and a live window ending at 238455, all had zero clipping.
At 238455, median/maximum loss was 1.0774/1.1757 and
median/p95/maximum norm was 0.1857/0.1976/0.2091. This is now a sustained
multi-window recovery; monitoring remains necessary because the same run has
previously relapsed after clean intervals.

The warning proved material. After a clean scheduled window at step 239580,
clipping rose to 6/20 at 240220 and another severe but brief relapse appeared
at 240855: median/maximum loss 7.0088/7.4659, median/maximum raw norm
14.27/9657.04, 20/20 updates clipped, and mean token accuracy 0.1121. By the
live step-241155 window, median loss had returned to 1.0650 and median norm to
0.2092, with 3/20 updates still clipped and maximum norm 9.40. The latest
complete ephemeral was step 241000. Repeated collapse/recovery cycles after
several clean windows reinforce a recurrent dynamical or optimizer-state
failure mode rather than a single isolated incident.

```bash
python scripts/monitor_training_stability.py \
  --run peter-sk-sdu/DFM5/40j5y877 \
  --log logs/training/dfm8_XXL_1epoch/stability_30m.jsonl \
  --interval 1800 --window 100 --min-step 229500 --target-step 268857 \
  --process-pattern 'torchrun.*pretrain.py.*wandb_run_id=40j5y877'
```

### Relevant alternatives from the literature

- [Adam-atan2](https://arxiv.org/abs/2407.05872) is deliberately
  scale-invariant, so the weak response to scalar gradient clipping follows its
  design.
- [Adafactor](https://arxiv.org/abs/1804.04235) introduced per-tensor
  preconditioned-update RMS clipping and found threshold `d=1` stabilizing
  while `d=2` did not. [StableAdamW](https://arxiv.org/abs/2304.13013) ports
  this idea to AdamW and reports better stability/quality than global gradient
  clipping in its tested regime. This should be evaluated per tensor and using
  preconditioner-surprise telemetry, not only as one model-global post-`atan2`
  RMS for AdamATan2.
- [SPAM](https://arxiv.org/abs/2501.06842) combines spike-aware clipping with
  periodic momentum reset, directly addressing persistent contaminated
  optimizer state. A reset is more invasive than skipping one detected batch,
  but is relevant if state contamination is already underway.
- [AdaGC](https://arxiv.org/abs/2502.11034) tracks an EMA of gradient norms per
  parameter tensor and clips relative to that local history; its reported
  Llama experiments eliminated spikes and outperformed fixed global clipping.
  This is the strongest literature-backed next candidate for an AdamATan2
  experiment, although its interaction with exact scale invariance still needs
  controlled validation.
- Other related families include unit-wise gradient-to-parameter clipping
  (AGC), history-percentile or z-score thresholds (AutoClip/ZClip), and
  Stable-SPAM's historical-norm normalization plus momentum reset. They solve
  different failure modes and should not be enabled together without an
  ablation.
