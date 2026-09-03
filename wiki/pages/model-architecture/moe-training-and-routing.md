---
type: Plan
title: MoE Training and Routing
description: Joint sparse-MoE training contract, FlexOlmo boundary, load-balancing scope, domain specialization, and matched expert geometry for HRM.
tags: [architecture, hrm, moe, routing, training, specialization]
status: draft
last_updated: 2026-09-03
confidence: medium
part_of: /pages/model-architecture.md
sources:
  - id: flexolmo
    resource: https://arxiv.org/abs/2507.07024
    title: "FlexOlmo: Open Language Models for Flexible Data Use"
  - id: olmoe
    resource: https://arxiv.org/abs/2409.02060
    title: "OLMoE: Open Mixture-of-Experts Language Models"
  - id: switch
    resource: https://arxiv.org/abs/2101.03961
    title: "Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity"
  - id: deepseek-moe
    resource: https://arxiv.org/abs/2401.06066
    title: "DeepSeekMoE: Towards Ultimate Expert Specialization in Mixture-of-Experts Language Models"
  - id: ucloud-submit-job
    resource: https://docs.cloud.sdu.dk/guide/submitting.html
    title: "UCloud: Submit a Job"
---
# MoE Training and Routing

## Boundary from FlexOlmo

The HRM reference is a standard jointly trained token-choice MoE, not a
FlexOlmo expert-composition system. In every step, its router selects experts
from the token hidden state; selected experts, router, attention, embeddings,
and the rest of HRM are optimized together on one mixed stream. Experts are
not assigned domain identities in advance.

FlexOlmo instead targets distributed training without sharing data: experts
are independently trained on their associated datasets and later combined
through domain-informed routing without joint training.[^flexolmo] That is a
distinct modular-data objective. If pursued here, it must be a separately
named architecture rather than an implicit change to the joint MoE.

## What load balance does and does not do

The current implementation includes Switch-style auxiliary load balancing,
router z-loss, FP32 router math, dropless dispatch, and aggregate plus
recurrent-call-resolved load/probability telemetry. Load balance prevents gross
traffic collapse; it does not make experts semantic or domain specialists.
The z-loss restrains router-logit growth; it does not distribute tokens.

The current balance loss is calculated independently for every router call
using rank-local batch statistics, then averaged across calls. This is enough
for single-device correctness but is not yet the declared multi-GPU scientific
implementation. Synchronize load/probability statistics over the intended
data-parallel balance group, or explicitly test a buffered approximation,
before interpreting expert health. Evidence after this plan was drafted also
indicates that the balance-statistics scope can materially affect MoE quality,
so it must be recorded with every result.

HRM makes balance scope unusually consequential. Pooling all six L calls could
hide collapse or a runtime straggler within one call. Enforcing uniformity in
each call may instead constrain recurrent-phase specialization. Keep per-call
telemetry in either case and treat per-call versus pooled balance as an ablation.

Top-k selection is discrete. Under the current top-1 selected-probability rule,
the language-model loss differentiates the selected gate weight, while the
balance loss acts through all softmax probabilities. It does not evaluate the
counterfactual task loss of unselected experts. Top-2 supplies a richer task
gradient but doubles expert branches unless each expert is narrowed.

## Domain specialization

Standard MoE specialization is emergent and may follow token identity,
frequency, syntax, language, position, recurrent phase, or optimization
artifacts rather than human domain names. Sufficient source coverage in the
training mix is necessary but does not guarantee a domain expert.

Use source labels first for evaluation, not as router inputs. Report held-out
domain loss, expert fractions, entropy, load variation, route persistence, and
domain-from-route predictability while controlling for token and length. Then
test causality by zeroing, swapping, or forcing matched-load experts. Routing
correlation alone is not specialization.

An explicitly domain-supervised router is a separate experiment: labels may be
unavailable at inference, and forcing every domain to use every expert equally
would oppose domain specialization. FlexOlmo-style independently trained data
experts are appropriate when data isolation, removal, or permission control is
the actual objective.[^flexolmo]

### Project-specific domain taxonomy

Do not use a flat mutually exclusive list such as `math`, `code`, `news`,
`creative`, and `Danish`: the first four are capabilities or genres while the
last is a language, and real rows occupy several categories. Maintain
multi-axis metadata instead:

- language: Danish, English, mixed/multilingual;
- capability: formal/math reasoning, code/SWE/tool use, grounded
  knowledge/science/government, dialogue/creative/instruction;
- objective/genre: continuation, QA, transformation, summarization, tool
  trajectory, conversation;
- source/document identity, context-length bin, and rights/provenance class.

For the current DFM lineage, natural candidate probe families already exist:
Numina/Sapient math; Nemotron SWE, Code Meta Reasoning, and Terminal Corpus;
factual FLAN plus scientific/government/news summarization; and the general
instruction, dialogue, editing, translation, and creative mixtures. Danish is
a cross-cutting slice through those families, not a fifth exclusive bucket.
News should normally be treated as grounded knowledge/summarization with a
time-based split rather than as a presumed expert identity.

The primary training stream should retain the natural audited mixture. Build a
separate equal-token probe grid across the axes above, with held-out sources
inside each family, and keep source labels outside the router. This
distinguishes domain generalization from memorizing dataset templates. If
emergent routing does not provide useful coverage, a later seeded experiment
may add a domain-to-expert routing prior or forced-route warmup and anneal it
away before ordinary inference. A persistent label-dependent router or
independently trained removable experts belongs to the separately named
FlexOlmo-style path.

### Concrete probe artifact contract

The current trainer accepts one `validation_path`, and the MoE output exposes
aggregate per-call counts rather than token route identities. The full DFM9
sampled and tokenized trees are expected on the training backend, not in this
local checkout. Domain-routing evaluation therefore needs two additive
utilities rather than a modification of the training sample:

1. `build_moe_probe_suite.py` reads a versioned source manifest, renders rows
   through the production Gemma chat template, deduplicates against training,
   applies source/document-level splits, and writes one V1 sampled directory
   per probe with an equal supervised-token budget.
2. `eval_moe_routing_probes.py` loads one checkpoint, resets carry per probe,
   runs teacher-forced evaluation over every V1 directory, and writes local
   JSON plus optional W&B metrics under `moe_probe/<probe_id>/<metric>`.

The manifest is source/split metadata, not a copy of raw text. Each record must
include `probe_id`, source URI or local path, immutable revision/hash, upstream
split, language tags, capability tags, objective, maximum supervised tokens,
document/source split policy, overlap-audit status, and rights/provenance
status. Evaluation output must record the checkpoint hash, resolved model
config, tokenizer/template hash, probe-manifest hash, seed, and actual valid
token count.

Existing aggregate MoE outputs are sufficient for per-probe loss, expert
loads, mean probabilities, balance/z losses, and call-resolved comparisons
because each loader is probe-homogeneous. Router entropy, load CV/min/max,
selected probability, and token-level route persistence/churn require an
optional evaluation-only routing trace. Do not retain raw prompts or token IDs
in W&B; store aggregate results and a local hashed artifact.

## Expert count, active count, and fair geometry

Train each `(E, k, expert width)` candidate with the routing geometry used at
evaluation. Changing `k` after training changes branch scale, active FLOPs,
expert gradient exposure, and the learned router objective; it is not a free
inference knob.

For dense intermediate width `I`, the primary matched comparison is:

| Row | Experts | Active | Expert width | Total expert FFN capacity | Active FFN compute |
|---|---:|---:|---:|---:|---:|
| Dense | 1 | 1 | `I` | `1x` | `1x` |
| Reference | 4 | 1 | `I` | `4x` | `1x` |
| Granular | 8 | 2 | `I/2` | `4x` | `1x` |

Thus `E4/k1/I` versus `E8/k2/(I/2)` separates routing granularity while
approximately matching both total expert parameters and active expert matrix
multiplication. The half-width expert setting is not exposed by the current
code and must be added before the second sparse row can run. DeepSeekMoE's
fine-grained and shared-expert results motivate later experiments, not skipping
this HRM-specific controlled pair.[^deepseek-moe]

Do not infer an expert-count law from XXS alone: vocabulary parameters dominate
that size, and small batches give weak per-expert statistics. Use XXS for
mechanics, S for screening, and at least B for a credible core-capacity result.

## Initialization and training modes

For training from scratch, initialize experts comparably and jointly optimize
the complete model on the same mixed token stream used by the dense control.
Random initialization plus balance loss is the deterministic reference.

For a cheaper sparse-upcycling probe from a dense Mimir checkpoint, clone the
selected dense feedforward into every expert, initialize routing near uniform,
reset optimizer state for new parameters, and continue pretraining. Report it
as upcycling: it measures adaptation from a trained dense model and is not a
from-scratch architecture comparison. OLMoE's released code documents sparse
upcycling as a supported but separate path.[^olmoe]

A dead expert receives no task gradient because it executes no tokens; a
balance loss can move the router toward it but cannot directly train its FFN.
Router jitter, a short uniform-dispatch burn-in, cloned dense initialization,
or expert dropout are possible anti-starvation controls. None is present in the
reference, and none should be introduced unless deterministic E4/k1 traces
show persistent starvation. Any stochastic routing must replay correctly under
activation checkpointing.

## Production boundary

The current dispatcher is dropless and executes only selected token/expert
pairs, but it uses Python expert loops. All experts remain inside the ordinary
FSDP-wrapped block, so every recurrent invocation can materialize the entire
expert bank. This is sparse mathematical activation, not yet efficient sparse
distributed training.

Before claiming speed or scaling, implement local grouped GEMM or block-sparse
dispatch. Larger expert banks then require expert/data process groups,
all-to-all token dispatch, global or group-scoped balance statistics, explicit
capacity/overflow policy, and checkpoint/resume parity. Dropless kernels such
as MegaBlocks-style block-sparse execution are preferable to token dropping in
the recurrent reference because dropped updates can compound across calls.

On 2026-09-03, the first B200 BF16 training attempt exposed a mixed-precision
dispatch bug: the residual-derived route accumulator was FP32 while autocast
produced BF16 expert outputs, and `index_add` requires identical dtypes. The
implementation now casts route weights and expert outputs to the accumulator
dtype before accumulation. A CPU BF16-autocast regression test covers this
case. The corrected commit `2a52387` completed a one-step B200 DDP smoke on
2026-09-03 with BF16 compute: loss `6.73447`, accuracy `0.00216`, and MoE
balance loss `1.06573`. The run emitted a nonfatal FlashAttention/CuTe
`AuxData` JIT-adapter diagnostic during initial compilation but completed the
optimizer step and finalized metrics. Treat timing as provisional until that
diagnostic is characterized in a longer smoke.

The earlier benchmark writer started its timer after the first optimizer step,
so a `max_steps=1` diagnostic did not create `BENCH_OUTPUT`. As of 2026-09-03,
the timer starts before the training loop and a successful one-step diagnostic
writes its JSON summary. Training can also run without a W&B session by setting
`wandb_enabled=false`; set `local_metrics_path` to retain run metadata and every
logged train/validation record as JSON Lines inside the run directory.

When the full sampled DFM9 storage is unavailable, use
`scripts/prepare_moe_real_pilot.py` for a bounded real-data training gate rather
than extending the synthetic correctness sample. It streams equal token budgets
from `oliverkinch/da-instruct-dynaword-hq`, `AI-MO/NuminaMath-1.5`, and
`allenai/tulu-3-sft-personas-code`, applies the DFM-Mimir chat template, and
writes native `V1Dataset` arrays. The script refuses output and cache paths
outside the repository and refuses to overwrite an existing output tree. This
pilot tests optimization and routing on Danish, math, and code, but it is not a
substitute for the complete 161-source DFM9 mixture or a dense-Mimir comparison.

## UCloud B200 smoke-run workflow

UCloud hardware is selected when the job is created in the UCloud UI, before
SSH or VS Code connects. Shell commands inside the allocation do not select or
allocate nodes. Use one B200 GPU node for the first MoE correctness smoke; a
multi-node launch is a later scaling task.

The local SSH alias is `ucloud` in `~/.ssh/config`. Each new UCloud job can
receive a different SSH port, so copy the current job's port from its UCloud
interface and replace only the `Port` value in that host block. The recovered
local reconnect sequence is below. Each command is intentionally separate.
`pkill` terminates stale **local SSH client connections**; it does not cancel
or kill the remote UCloud job.

```bash
nano ~/.ssh/config
```

The host block should retain its existing hostname, user, key, and identity
settings while using the new job port:

```sshconfig
Host ucloud
    HostName ssh.cloud.sdu.dk
    User ucloud
    Port <CURRENT_JOB_PORT>
    IdentityFile /Users/ampirchert/.ssh/id_ed25519_ucloud
    IdentitiesOnly yes
```

```bash
pkill -f 'ssh.*ucloud'
```

```bash
ssh-keyscan -p <CURRENT_JOB_PORT> ssh.cloud.sdu.dk >> ~/.ssh/known_hosts
```

```bash
ssh -vvv ucloud
```

The last command is the direct connection check. Once it succeeds, VS Code's
Remote-SSH target is the same `ucloud` alias. The key scan must use the same
port placed in `~/.ssh/config`.

If SSH reports that the remote host identification changed, remove only that
job endpoint's old key, repeat the key-scan command, and reconnect; substitute
the current job port:

```bash
ssh-keygen -R "[ssh.cloud.sdu.dk]:<CURRENT_JOB_PORT>"
```

Correction, 2026-09-03: `/work/dfm` is a historical mount name, not a portable
project location. Only folders attached to the job under `/work` persist after
the allocation ends.[^ucloud-submit-job] At job submission, attach either the
existing persistent folder containing DFM9 plus a separate work folder, or one
combined persistent folder. Keep the repository, Conda prefix, logs, and
checkpoints under the attached work folder. Do not place durable artifacts
under `/home/ucloud`.

Superseded, 2026-09-03: the workstation branch preparation below was the
pre-commit recovery plan. The implemented experiment now lives on the single
branch `hrm-moe`; commit `310c2ad` incorporates `origin/main` through
`4d67287`. Use `hrm-moe` directly on UCloud. The historical commands are
retained for provenance:

```bash
cd /Users/ampirchert/development/HRM-Text

git switch -c backup/local-work-20260903
git add -A
git restore --staged -- .DS_Store
git diff --cached --name-status
git commit -m "WIP: preserve local work before HRM-MoE branch split"

git switch main
git switch -c experiment/hrm-moe
git restore --source backup/local-work-20260903 -- \
  config/arch/net/hrm_moe.yaml \
  models/baselines/hrm_moe_nocarry_bp_warmup.py \
  models/moe.py \
  models/moe_lm_head.py \
  tests/test_hrm_moe.py
git add -- \
  config/arch/net/hrm_moe.yaml \
  models/baselines/hrm_moe_nocarry_bp_warmup.py \
  models/moe.py \
  models/moe_lm_head.py \
  tests/test_hrm_moe.py
git diff --cached --name-only
git commit -m "Add experimental HRM sparse MoE architecture"
git push -u origin HEAD
```

`origin` is the user's fork. A later PR to the original repository should use
a separate branch based on `upstream/main`, because a branch based on the
fork's modified `main` can include every fork-only commit in the PR. The
original repository is `https://github.com/sapientinc/HRM-Text.git`; add it as
`upstream`, inspect divergence, and port the minimal MoE commit only after the
fork branch has been tested.

After creating the B200 job, attach the persistent UCloud folder or folders and
connect to the allocated machine. Determine their actual names under `/work`,
then set explicit paths rather than assuming a mount name:

```bash
ls -la /work

WORK_ROOT=/work/<attached-work-folder>
DFM9_ROOT=/work/<attached-data-folder>/sampled_dfm9
PROJECT_ROOT="$WORK_ROOT/HRM-Text"
ENV_PREFIX="$WORK_ROOT/conda-envs/hrm-moe-env"

git clone --branch hrm-moe --single-branch \
  https://github.com/AnnemetteBP/HRM-Text.git "$PROJECT_ROOT"
cd "$PROJECT_ROOT"
```

Create a separate persistent Python 3.13 environment. The repository has
`[tool.uv] package = false`, so an editable package installation is not needed
to run modules from the repository root. Install Torch and extension build
prerequisites first, then consume `pyproject.toml` with the `sm100` extra. This
ordering makes Torch available to the FlashAttention 4 source build:

UCloud image correction, 2026-09-03: job `j-12379951-job-0` opened with the
`(base)` Conda environment already active, while
`/home/ucloud/miniforge3/etc/profile.d/conda.sh` did not exist. On an image
whose prompt already shows `(base)`, skip the hard-coded `source` command and
invoke `conda` directly. The source path below applies only to images where
that Miniforge installation exists.

```bash
source /home/ucloud/miniforge3/etc/profile.d/conda.sh
conda create -y --prefix "$ENV_PREFIX" python=3.13 pip
conda activate "$ENV_PREFIX"

python -m pip install --upgrade pip uv
export CUDA_HOME=/usr/local/cuda-13.2
export PATH="$CUDA_HOME/bin:$CONDA_PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:${LD_LIBRARY_PATH:-}"

uv pip install --python "$CONDA_PREFIX/bin/python" \
  torch packaging ninja wheel setuptools setuptools-scm pytest \
  --torch-backend=cu130

MAX_JOBS=8 NVCC_THREADS=2 uv pip install \
  --python "$CONDA_PREFIX/bin/python" \
  --requirements pyproject.toml \
  --extra sm100 \
  --torch-backend=cu130 \
  --no-build-isolation-package flash-attn-4

python -c 'import torch; from flash_attn.cute import flash_attn_varlen_func; print(torch.__version__, torch.cuda.get_device_name(0))'
python -m pytest -q tests/test_hrm_moe.py
```

Create an interactive `tmux` session after installation, start the run inside
it, and detach with `Ctrl-b`, then `d`. `tmux` survives an SSH/VS Code
disconnect but not expiration or cancellation of the UCloud allocation.

```bash
tmux new-session -s hrm-moe-b200
```

Inside that session:

```bash
WORK_ROOT=/work/<attached-work-folder>
DFM9_ROOT=/work/<attached-data-folder>/sampled_dfm9
PROJECT_ROOT="$WORK_ROOT/HRM-Text"
ENV_PREFIX="$WORK_ROOT/conda-envs/hrm-moe-env"

cd "$PROJECT_ROOT"
source /home/ucloud/miniforge3/etc/profile.d/conda.sh
conda activate "$ENV_PREFIX"
set -o pipefail

RUN_ID="hrm-moe-e4-b200-smoke-$(date +%Y%m%d-%H%M%S)"
RUN_ROOT="hrm-moe-runs/$RUN_ID"
mkdir -p "$RUN_ROOT/logs" "$RUN_ROOT/results" "$RUN_ROOT/checkpoints"

BENCH_OUTPUT="$RUN_ROOT/results/summary.json" \
OMP_NUM_THREADS=1 \
MKL_NUM_THREADS=1 \
torchrun --nproc_per_node=1 pretrain.py \
  arch/net@arch=hrm_moe \
  arch/size@arch=XXS \
  arch.bp_warmup_ratio=0.0 \
  data=dfm9 \
  data.path="$DFM9_ROOT" \
  accelerator_type=sm100 \
  distributed_strategy=ddp \
  ddp_params_precision=fp32 \
  fwd_bwd_dtype=bfloat16 \
  compile_train_batch=false \
  activation_checkpointing=none \
  ema=null \
  global_batch_size=8192 \
  epochs=1 \
  lr=2.2e-4 \
  lr_min_ratio=1.0 \
  lr_warmup_steps=10 \
  max_steps=20 \
  log_interval=1 \
  wandb_enabled=false \
  local_metrics_path="$RUN_ROOT/results/metrics.jsonl" \
  checkpoint_step_interval=20 \
  checkpoint_format=unsharded \
  checkpoint_path="$RUN_ROOT/checkpoints" \
  project_name=HRM-MoE-Smokes \
  run_name="$RUN_ID" \
  2>&1 | tee "$RUN_ROOT/logs/train.log"

python -m json.tool "$RUN_ROOT/results/summary.json"
```

Reattach after reconnecting with `tmux attach -t hrm-moe-b200`. This launch
does not initialize W&B; metrics stay in `results/metrics.jsonl` and the
benchmark summary in `results/summary.json`. The DFM9 sample is not in Git; its
explicit Hydra path override points training at the attached persistent data
folder.

[^flexolmo]: FlexOlmo, arXiv:2507.07024.
[^olmoe]: OLMoE, arXiv:2409.02060.
[^switch]: Switch Transformers, arXiv:2101.03961.
[^deepseek-moe]: DeepSeekMoE, arXiv:2401.06066.
[^ucloud-submit-job]: UCloud, "Submit a Job."
