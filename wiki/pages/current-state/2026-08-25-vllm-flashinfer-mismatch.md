---
type: Runtime Incident
title: vLLM Startup Failure From FlashInfer Version Mismatch
description: Diagnosis of persistent vLLM status 71 failures in the 8K evaluation campaign.
tags: [vllm, flashinfer, evaluation, hrm-cu132]
status: stable
last_updated: 2026-08-26
confidence: high
---
# vLLM Startup Failure From FlashInfer Version Mismatch

The persistent vLLM servers in `hrm-cu132` failed during engine initialization,
before serving requests. The exact traceback reports:

```text
flashinfer-cubin version (0.6.13) does not match flashinfer version (0.6.16.post3)
```

This occurs while vLLM initializes its sampler, even though the server is
configured with `--attention-backend FLASH_ATTN` and FlashAttention 4 is
selected for attention. The model loads successfully; the failure is in the
optional FlashInfer sampler import.

The affected environment currently has vLLM `0.27.1`,
`flashinfer-python 0.6.16.post3`, and `flashinfer-cubin 0.6.13`. The scheduler
therefore reports persistent-server startup `status 71`, and retries do not
help until the environment or server environment is corrected.

Known remedies are to install a matching `flashinfer-cubin` version, or use the
existing operational workaround for this machine:

```bash
VLLM_USE_FLASHINFER_SAMPLER=0 FLASHINFER_DISABLE_VERSION_CHECK=1
```

The latter is already used by the dedicated Folketing audit launcher. The
evaluation scheduler did not propagate these variables to its persistent vLLM
servers at the time of this incident.

## Evaluator dependency incident

The same campaign also exposed a separate failure in `hrm-cu132`: it had
`antlr4-python3-runtime==4.11.0`, while OmegaConf's generated grammar in the
evaluation environment requires the 4.9 runtime. Standard MATH shards then
exited immediately with:

```text
Could not deserialize ATN with version 3 (expected 4).
```

This was an evaluator import failure, not an OOM or a vLLM failure. The working
repair is:

```bash
uv pip install --python /home/ucloud/miniforge3/envs/hrm-cu132/bin/python \
  'antlr4-python3-runtime==4.9.3'
```

After resetting the incomplete 2.15M rows, all eight MATH workers generated
normally with batch size 64.

## 8K long-context evaluation fixes

The 2.15M long-context campaign exposed three independent evaluator issues:

1. Several prompts were sized against the raw input rather than the rendered
   Gemma chat template. `long_context.py` now tokenizes each rendered prompt,
    reserves 2560 tokens for template/framing overhead and the configured output,
    and preserves the head and tail when truncation is required. The extra
    margin is necessary because the actual LongAlign renderer added 2,049
    tokens on a boundary case; 2048 still allowed an 8,193-token request.
2. The RULER entry used the display name `ruler`; the registered task is
   `dfm_evals/ruler`. The single-task config now uses the registered name.
3. Marathon's dataset metadata requires `datasets>=5.0.1`. The `dfm-evals`
   project constraint and lockfile now require that version; the evaluator
   environment was synchronized accordingly.

LongAlign sample IDs are also made unique, and shard merging now supports all
 8K task names, including the Danish summarization task. The affected current
2.15M rows were reset after these changes. The epoch-8 baseline remains gated
behind the current 2.15M terminal and teardown jobs, so it will start only
after the corrected 2.15M suite has completed.

The persistent server pool also had a startup race: parallel `find-free-port`
scans could select the same port before the child processes had bound it. The
pool now allocates each GPU a separate modulo-8 port lane. A stale orphan from
the interrupted run was removed; current plan-owned servers have distinct
ports and are monitored by parent process group.

## 2026-08-25 Long-context retry

The first retry still failed because the 1024-token template margin allowed a
rendered request of 7681 input tokens plus 512 output tokens. The long-context
budget is now conservative: 6144 input tokens, 512 output tokens, and a 1536
token framing margin within the 8192-token server limit. The four affected jobs
were reset atomically under the scheduler plan lock:

- 2.15M `longbench_en` and `longalign_en`;
- epoch-8 baseline `longbench_en` and `longalign_en`.

At retry start, all four clients launched successfully with fresh persistent
vLLM servers and no context error in their new logs. Epoch 8 here is the
baseline checkpoint; the 8K continuation is epoch 9 and remains blocked until
the baseline evaluation/average finalizes.

The long-context task factories now accept and propagate the scheduler's
`max_gen_toks` parameter. This removes the previous warning that the parameter
was ignored and keeps prompt budgeting and generation length coupled.

LongBench and LongAlign preprocessing is now cached as versioned JSONL under
`data/eval_cache/long_context`. Build it explicitly with
`uv run --project dfm-evals python scripts/prepare_long_context_eval_cache.py`
before a campaign. Retries and shards then reuse the prepared rows instead of
reloading HF data, language-detecting, and re-tokenizing the full dataset.

## 2026-08-25 boundary correction

**Superseded on 2026-08-26 by the exact rendered-token preprocessing below.**

The 2560-token framing estimate was still one token too optimistic: LongAlign
produced a rendered input of 7681 tokens, so a 512-token generation requested
8193 tokens. `long_context.py` now uses framing reserve 2570 and cache version
`v6`; the resulting LongAlign cache caps tokenizer input at 5110 tokens,
leaving a small margin below the 8192-token server limit. The LongAlign EN
cache was rebuilt before resetting and retrying the 2.15M and epoch-8 baseline
jobs.

## 2026-08-26 exact LongAlign preprocessing and 32-way sharding

The framing-reserve approach was retired for the production LongAlign retry.
The two 8K exports use byte-identical `tokenizer.json` files. The cache builder
now renders every prompt with the deployed
`evaluation/chat_templates/gemma4_native_chat.jinja` template, tokenizes that
rendered string with the exported HF tokenizer, and truncates by binary search
while preserving the prompt head and tail. The verified input ceiling is 7,648
tokens: 512 tokens remain for generation and 32 tokens remain as safety margin
inside the 8,192-token vLLM limit.

Run the exact build with:

```bash
PATH=/home/ucloud/miniforge3/envs/hrm/bin:$PATH \
TOKENIZERS_PARALLELISM=false \
python scripts/prepare_long_context_eval_cache.py --workers 32
```

The `v8` LongAlign EN build processed 5,000 rows in about 45 seconds. Four rows
needed truncation; the resulting rendered prompts range from 1,610 to 7,560
tokens. The cache is specific to the 8K evaluation. Future 16K or 32K caches
must be rebuilt from the original dataset rather than derived from this
already-truncated cache.

The failed unsharded LongAlign jobs for the 2.15M checkpoint and epoch-8
baseline were replaced atomically under the scheduler plan lock by 32 shards
each. Their merge jobs now depend on all 32 corresponding shard rows and carry
`metadata.shards=32`. The scheduler was left soft-stopped after the rewrite.

The first retry exposed a separate cache race. An invalid cache was silently
treated as absent, so concurrent shard processes rebuilt it and wrote through
the same `.tmp` path. Existing invalid caches now fail loudly, cache reads are
streamed, and fallback writers use unique temporary files followed by atomic
replacement. The exact `v8` cache was regenerated and verified in the
production environment before all 64 LongAlign shard rows were reset.

The initial `long_context_headline/overall=0.48305` at 2.15M is invalid as a
long-context-only aggregate: the logger scanned every merged DFM task under the
checkpoint root. Restricting the calculation to the eight long-context tasks
with non-empty metrics gives `0.35338`; `govreport_long` produced an empty
merged metric and is not represented. The headline logger must be restricted
to the explicitly scheduled long-context task names before this aggregate is
used for comparisons.

**Resolved on 2026-08-26:** `govreport_long` uses the `summarization` scorer;
its merge dispatch had incorrectly searched only for RULER and generic
long-context scorers. The corrected merge exports ROUGE, BLEU, chrF, and
BERTScore metrics. Long-context headline logging now uses the new
`long_context_headline_v2` prefix and exactly one declared representative
metric for each of the nine scheduled tasks; it fails if any declared metric
is absent. The corrected overall values are `0.40897` at 2.15M and `0.45694`
for the epoch-8 baseline. The old contaminated prefix remains historical and
must not be used.

## 2026-08-26 production 8K RULER suite

The eight-example `ruler_smoke` suite is retained only to reproduce historical
results. It is no longer the production RULER signal. The replacement
`ruler_8k` suite evaluates all 13 locally implemented RULER variants at an
8,192-token server limit with 32 deterministic examples per variant: 416
examples per checkpoint. It is split into eight scheduler shards, merged into
an overall score plus per-variant scores, and contributes to the new
`long_context_headline_v3` average.

RULER length estimation must use the exported `tokenizer.json` through the
low-level `tokenizers` backend. The `transformers` build in the `dfm-evals`
environment fails to load this export because `fix_mistral_regex` is passed
twice. The direct tokenizer backend avoids that unrelated compatibility bug.
The export declares `fix_mistral_regex=true`. vLLM applies Transformers'
corrected pre-tokenizer, while an initially added low-level length counter did
not; this caused number-heavy CWE prompts to be undercounted. The lightweight
counter now applies the same regex patch before sizing generated contexts and
retains a 256-token framing reserve. Earlier unpatched attempts produced exact
8,193-token rejected requests and are superseded.

The comparison campaign lives at
`logs/scheduler/dfm9_8k_ruler_full_20260826`. It evaluates the 2.15M 8K
checkpoint and the epoch-8 4K baseline export configured with YARN/8K. To run
beside active training, each persistent vLLM server uses
`vllm_gpu_memory_utilization=0.18`, requires at least 48,000 MiB effective free
GPU memory, and uses client batch 4. The server reports capacity for roughly
4.46 concurrent full 8K requests, making four the evidence-based concurrency
limit while training is resident.

The original RULER QA implementation fetched HotpotQA from the obsolete CMU
HTTP endpoint and all eight shards timed out at `qa_2`. As of 2026-08-26 it
uses the official `hotpotqa/hotpot_qa` distractor validation Parquet conversion
from Hugging Face and writes downloads through an atomic `.part` file. The
production cache is
`~/.cache/dfm_evals/ruler/qa/hotpotqa.parquet` (27 MB). The loader was verified
against 7,405 usable QA examples and 73,700 context documents before the
comparison campaign was reset and relaunched.

The completed comparison had 20/20 successful scheduler jobs. Production
RULER fell from `0.76182` at the 4K epoch-8 baseline to `0.57548` after the
first 22,511 steps of 8K continuation (step 2,150,000). The nine-task
`long_context_headline_v3/overall` fell from `0.43326` to `0.40624`. This is a
more trustworthy signal than the superseded eight-example smoke result. Both
points, including all per-variant RULER metrics, were explicitly synced to the
`DFM5/dfm9-xl-8k` run. An initial accidental 2.15M sync to
`hrm-long-context/rq9pskna` is superseded for comparison and should not be used.

### Actual production prompt lengths

An audit of vLLM's recorded `model_usage.input_tokens` shows that the 8,192
server limit does not by itself make every task long-context. At epoch 8 and
step 2.15M, all 416 production RULER inputs exceed 4K (6,212--7,915 tokens).
The shares above 4K are: GovReport 100% (86/86), LongBench EN 85.1%
(3,121/3,666), LongAlign EN 98.4% (4,919/5,000), LongAlign DA 100% but only
five examples, Marathon 99.6% (1,524/1,530), QMSum 98.9% (269/272), and
Danish EUR-Lex 96.1% (799/831). The plain `danish_summarization` task has zero
inputs above 4K (maximum 4,047; median 457).

Consequently, `long_context_headline_v3` is a transition aggregate rather
than a strictly long-context-only average: it still includes the short plain
Danish summarization task, and its LongAlign DA component is based on only
five examples. A future headline revision should exclude or replace plain
`danish_summarization` and enlarge the Danish long-context evaluation cohort.

Project-owner decision on 2026-08-26: defer that headline revision until the
step-2.20M evaluation. YaRN itself has no trainable parameters, but the model
weights may need more than the first 22,511 continuation steps to adapt to the
new positional geometry and 8K examples. Keep v3 unchanged so 2.15M and 2.20M
remain directly comparable.

The existing short-context suite averages also declined between the original
epoch-8 evaluation and step 2.15M: `suite_avg_v3/standard` fell from
`0.72830` (8 metrics) to `0.65960`, and `suite_avg_v3/dfm` fell from `0.62751`
(31 metrics) to `0.54625`. These explicit suite lists contain only `eval/*`
and `dfm_eval/*` metrics; they do not contain any `long_context/*` metrics.
The 2.15M suite row was synced to `DFM5/dfm9-xl-8k` on 2026-08-26.

Interpretation caveat: epoch 8's short-context values are the original 4K
evaluation, while step 2.15M uses the 8K/YaRN export. Their delta therefore
combines the serving-position change and 22,511 steps of 8K continuation; it
does not by itself isolate the effect of continuation training. The separate
epoch-8 YaRN/8K baseline currently covers the long-context suite, not the full
standard and DFM suites.
