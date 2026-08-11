---
type: Operational Record
title: Active Work
description: 'Part of Current State: Active Work.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# Active Work

Part of [Current State](/pages/current-state.md).

Update on 2026-06-03:

- Lite evals for `checkpoints/dfm4/XL-ddp` checkpoints `step_50000` and
  `step_100000` were restarted for the affected DROP and IFEval jobs after the
  original launch used overly conservative or invalid settings. Confidence:
  high.
- `scripts/schedule_checkpoint_evals.sh` now defaults
  `IFEVAL_BATCH_SIZE=16`. This is used both for the HRM OpenAI shim
  `--batch-size` and Inspect `--max-connections`, replacing the earlier
  conservative default of `1`. Confidence: high.
- DROP standard eval must preserve the YAML benchmark config via
  `run_only=[DROP]` and `shard_overrides.DROP.*`; replacing the whole
  `benchmarks=[...]` entry loses per-task generation settings. The current
  DROP lite restart uses `condition=direct`, `max_tokens=64`, and
  `generation_config.batch_size=16`. The attempted `stop: "\n\n"` setting was
  removed because `SimpleEngine.generate()` does not accept `stop`.
  Confidence: high.
- GSM8K lite eval initially inherited the global `condition=synth,cot` setting
  from `evaluation/config/hrm_benchmarking.yaml`, producing unusable
  `invalid=1.0` behavior for `step_50000` and likely the same for
  `step_100000`. On 2026-06-03 the GSM8K benchmark entry was patched to
  explicitly use `condition=direct` and `max_tokens=512`; a foreground smoke
  test verified the effective config as `batch_size=16`, `condition=direct`,
  `max_context=3072`, `max_tokens=512`. The clean reruns were launched in tmux
  window `gsm8k_direct_20260603_094627`, writing to the normal shard logs under
  `logs/eval/dfm4_XL_ddp_lite_probe/{step_50000,step_100000}/standard_shards/GSM8k/`.
  Confidence: high.
- The GSM8K direct reruns completed but still produced `invalid=1.0` for both
  lite checkpoints. The likely cause is the GSM8K scorer, not necessarily the
  model: `_extract_answer()` only accepts a boxed answer or an entire generation
  string parseable as a single number, so natural-language final answers are
  marked invalid. GSM8K was deliberately not synced to W&B after this result.
  Confidence: high for the local result, medium for the root-cause inference.
- A 3-sample GSM8K smoke generation probe for `checkpoints/dfm4/XL-ddp`
  `step_50000` and `step_100000` with `condition=direct`, `max_context=3072`,
  `max_tokens=128`, and `batch_size=3` produced incoherent token-salad rather
  than natural-language math answers. The current `_extract_answer()` returned
  `None` for all six samples. This supersedes the earlier parser-only
  hypothesis for these two early XL checkpoints; the parser is still strict,
  but the sampled generations themselves were unusable. Confidence: high.
- Follow-up probe on `step_100000` isolated the incoherence to EMA inference:
  `ckpt_use_ema=True` produced token-salad for `direct`, `synth,cot`, `cot`,
  and `synth`, while `ckpt_use_ema=False` produced coherent outputs (`direct`
  emitted the parseable bare number `128`; `synth,cot`/`cot` emitted readable
  step-by-step reasoning, though still wrong on the sampled GSM8K item). The
  unsharded checkpoint's model keys match the loader, and optimizer EMA tensors
  map correctly to named parameters. The likely operational fix for early
  DFM4 XL lite evals is to rerun with non-EMA weights by passing
  `ckpt_use_ema=false` into `evaluation.main` / the HRM OpenAI server
  `--no-ema`. Confidence: high.
- A compact 6-prompt comparison across GSM8K, ARC, and BoolQ for DFM4 XL
  `step_50000` and `step_100000` confirmed the same pattern: EMA generations
  are token-salad at both checkpoints; non-EMA generations are short,
  parseable answers. Sample non-EMA direct results: GSM8K emitted `12`/`120` at
  `step_50000` and `128`/`120` at `step_100000`; ARC/BoolQ answers moved from
  `A,C,A,A` to `C,C,B,B` on the sampled prompts. Confidence: high.
- The likely root cause is numerical, not save/load key mapping: model
  parameters and `param_ema` are bfloat16, and `ema=0.9999` means each update
  uses alpha `1e-4`. A local scalar check showed bfloat16 `lerp_` often rounds
  these updates to zero, e.g. `0.02 -> 0.03` with alpha `1e-4` leaves the EMA
  value unchanged in bfloat16 while fp32 would update to `0.020001`. Therefore
  EMA can remain close to initialization even after many steps. Future EMA
  should store/update shadow weights in fp32 or use a much less aggressive EMA
  decay if kept in bf16. Confidence: high.
- DDP mixed precision was patched on 2026-06-03 to mirror the FSDP2 path more
  closely. The DDP branch no longer casts trainable parameters with
  `model.to(dtype=fwd_bwd_dtype)` before optimizer creation; instead,
  `TrainState.use_cuda_autocast` enables CUDA autocast during the forward/backward
  step when `distributed_strategy=ddp` and `fwd_bwd_dtype != float32`. This keeps
  DDP optimizer state and EMA shadow parameters in fp32 while preserving bf16
  compute. `python -m py_compile pretrain.py` passed. Existing bf16-DDP
  checkpoints retain their old bf16 optimizer/EMA state; the clean fix applies
  to new DDP checkpoints. Confidence: high.
- Non-EMA lite eval support was added on 2026-06-03. Confidence: high.
  `scripts/schedule_checkpoint_evals.sh` accepts `NO_EMA=1`, passing
  `ckpt_use_ema=false` to `evaluation.main` and `--no-ema` to
  `scripts/hrm_openai_server.py`; `scripts/schedule_multiple_checkpoint_evals.sh`
  propagates `NO_EMA` into per-job child schedulers and final merge invocations.
  `evaluation/config/hrm_benchmarking_lite.yaml` is the isolated standard-eval
  lite config: direct mode by default, standard batch size `16`, `GSM8k`
  `max_tokens=256`, `MATH` `max_tokens=512`, `DROP` `max_tokens=64`, and no
  per-MCQ `batch_size: 1` overrides. Validation passed with `bash -n` for both
  scheduler scripts and YAML parsing for the lite config.
- Non-EMA lite evals for DFM4 XL-DDP `step_50000` and `step_100000` were
  launched on all 8 GPUs on 2026-06-03. Confidence: high. The checkpoint state
  files report `global_batch_size=196608`, so W&B epoch x-axis values are
  `0.1365202623373361` and `0.2730405246746722`. Logs are under
  `logs/eval/dfm4_XL_ddp_noema_lite_probe_20260603_1125` and
  `logs/dfm_evals/dfm4_XL_ddp_noema_lite_probe_20260603_1125`; the tmux window
  is `hrm-1:noema-lite`. Metrics are written to the existing W&B run
  `dfm4-XL-ddp` in project `Original Plus Mixed Danish Instruction Rich L`
  under prefixes `lite_eval_noema/` and `lite_dfm_eval_noema/`.

```bash
NO_EMA=1 \
LITE_EVAL=1 \
QUEUE_ORDER=heavy_first \
CKPT_TAGS=step_50000,step_100000 \
EVAL_EPOCHS=0.1365202623373361,0.2730405246746722 \
CKPT_PATH=checkpoints/dfm4/XL-ddp \
GPUS=0,1,2,3,4,5,6,7 \
STANDARD_CONFIG=evaluation/config/hrm_benchmarking_lite.yaml \
STANDARD_BATCH_SIZE=16 \
DFM_BATCH_SIZE=16 \
IFEVAL_BATCH_SIZE=16 \
EVAL_PREFIX=lite_eval_noema \
DFM_EVAL_PREFIX=lite_dfm_eval_noema \
WANDB_PROJECT="Original Plus Mixed Danish Instruction Rich L" \
WANDB_RUN_ID=4chqwd3w \
WANDB_RUN_NAME=dfm4-XL-ddp \
MAX_RETRIES=3 \
LOG_ROOT_BASE=logs/eval/dfm4_XL_ddp_noema_lite_probe_20260603_1125 \
DFM_LOG_ROOT_BASE=logs/dfm_evals/dfm4_XL_ddp_noema_lite_probe_20260603_1125 \
scripts/schedule_multiple_checkpoint_evals.sh
```
  to new runs, or to resumed runs only insofar as state loading casts/restores
  into the new fp32 optimizer objects. Confidence: high.
- Resume/upcycling support was added for legacy bf16 DDP checkpoints:
  `upcast_optimizer_state_on_resume` upcasts floating optimizer state tensors to
  fp32 after checkpoint load, and `reset_ema_on_resume` resets any optimizer
  `param_ema` buffers from the loaded current parameters in fp32. These flags
  are present in `PretrainConfig` and `config/cfg_pretrain.yaml`. Use both when
  resuming the DFM4 XL DDP run from `step_100000` or `step_150000` so future EMA
  is rebuilt from the coherent raw model instead of carrying forward the broken
  bf16 EMA shadow. `python -m py_compile pretrain.py` and a config key smoke
  check passed. Confidence: high.
- A no-EMA PIQA-only probe was run locally for DFM4 XL DDP checkpoints
  `step_50000` and `step_100000` without W&B sync. Command used two local
  `scripts/hrm_openai_server.py` instances with `--no-ema`, `--batch-size 16`,
  and `condition=direct`, then `uv run --project dfm-evals evals suite
  hrm_danish_piqa`. Results under
  `logs/dfm_evals/dfm4_XL_ddp_noema_piqa_20260603_110551`: `step_50000`
  `lite_dfm_eval_noema/piqa/piqa_scorer/accuracy=0.18518518518518517`
  (`n=108`), `step_100000`
  `lite_dfm_eval_noema/piqa/piqa_scorer/accuracy=0.4722222222222222`
  (`n=108`). This shows clear non-EMA improvement from 50k to 100k, unlike the
  EMA lite evals. Confidence: high.
- W&B workspace update on 2026-06-03. Confidence: high for API readback. The
  package `gql==4.0.0` was installed in the `hrm` environment, which also
  installed `graphql-core==3.2.8` and `backoff==2.2.1`. The W&B Python
  client's AST type check was still incompatible with these objects, so the
  actual view mutation used direct GraphQL HTTP requests with the existing
  W&B credentials. The API showed that saved view `nw-boh5wwabbfc7-v`
  (`manual workspace`) has no Lite sections, while the default project view
  `nw-nwuserpetersk-w` (`Peter-sk's workspace`) contained auto sections
  `lite_eval` and `lite_dfm_eval`. Those two auto sections were repointed to
  `lite_eval_noema` and `lite_dfm_eval_noema` by changing their `name` and
  `defaultName` fields. Backups were written to
  `logs/wandb_workspace_specs/20260603T103845Z_before_lite_noema_nw-nwuserpetersk-w.json`
  and
  `logs/wandb_workspace_specs/20260603T103845Z_after_lite_noema_nw-nwuserpetersk-w.json`.
- DFM4 XL-DDP non-EMA lite checkpoint comparison on 2026-06-03. Confidence:
  high for local merged JSON values; medium for interpreting lite-shard results
  against full DFM L evals. At `step_50000` and `step_100000`, the raw
  non-EMA XL checkpoints show coherent learning but remain under DFM L epoch 1
  on most standard tasks. Examples at `step_100000`: `MMLU=0.3015` vs DFM L
  epoch 1 `0.3860`, `GSM8k=0.0364` vs `0.6892`, `DROP/f1=0.1066` vs `0.2419`,
  `WMT24++ chrf3pp=0.4052` vs `0.4907`, and `MultiWikiQA f1=0.5106` vs
  `0.8412`. PIQA is the main exception: `step_100000` reaches
  `0.4722`, slightly above DFM L epoch 1 `0.4630` but below later DFM L
  epochs. Improvements from `50k` to `100k` include `MMLU 0.2443 -> 0.3015`,
  `DROP/f1 0.0641 -> 0.1066`, `GSM8k 0.0242 -> 0.0364`,
  `GEC-DaLA 0.0996 -> 0.2148`, `WMT24++ 0.3616 -> 0.4052`,
  `MultiWikiQA f1 0.4289 -> 0.5106`, and `PIQA 0.1852 -> 0.4722`.
- Non-GSM lite metrics for `checkpoints/dfm4/XL-ddp` checkpoints `step_50000`
  and `step_100000` were merged and synced to W&B run `4chqwd3w` under
  `lite_eval/*` and `lite_dfm_eval/*`. This includes standard tasks
  `DROP`, `MMLU`, `ARC`, `HellaSwag`, `Winogrande`, `BoolQ`, and `MATH`, plus
  DFM tasks `danish_citizen_tests`, `dala`, `gec_dala`, `wmt24pp_en_da`,
  `multi_wiki_qa`, `piqa`, `generative_talemaader`, `govreport`,
  `nordjyllandnews`, `humaneval`, and `ifeval-da`. Confidence: high.
- `scripts/merge_ifeval_da_shards.py` now honors `--prefix`, so lite IFEval-DA
  metrics can be logged under `lite_dfm_eval/ifeval-da/...` rather than the
  full-eval `dfm_eval/...` namespace. Confidence: high.
- Manual restart wrappers were launched under
  `logs/eval/dfm4_XL_ddp_lite_probe/manual_restarts_20260603_083305/` for
  `step500_ifeval`, `step500_drop`, and `step100_ifeval`; their status is
  appended to `logs/eval/dfm4_XL_ddp_lite_probe/status.tsv`. Confidence: high.
- PIQA dfm-evals was slow because the task had no task-local generation cap and
  therefore used the HRM model-info fallback of `output_tokens=512`. This made
  8-sample batches take about seven minutes when one request ran to the cap.
  `dfm-evals/dfm_evals/tasks/piqa.py` now accepts `max_gen_toks`, and
  `config/dfm_evals_hrm_single_tasks.yaml` sets `max_gen_toks=8` for
  `hrm_danish_piqa`. Restarting the `step_50000` PIQA shard with batch 16
  completed the full `108/108` samples in under a minute. Confidence: high.
- `scripts/watch_multi_checkpoint_eval_progress.py` now supports `--once`,
  parses manual scheduler `START/END` lines, and uses `nvidia-smi`
  compute-app PID-to-GPU mapping to recover live manually restarted HRM eval
  jobs. Confidence: high.
- After the manual IFEval and PIQA restarts, GPUs 0, 6, and 7 became idle
  because their replacement wrappers used one-job queues and did not return to
  the main multi-checkpoint queue. The remaining main queue still had `16`
  jobs. Replacement queue consumers were launched from
  `logs/eval/dfm4_XL_ddp_lite_probe/manual_queue_workers_20260603_085141/`
  for GPUs 0, 6, and 7; they append to the shared status file and started
  `step_100000` DROP, MMLU, and HellaSwag. Confidence: high.
- WMT24++ en-da has `960` usable samples after filtering, so shard `0/8` has
  `120` samples. `scripts/watch_multi_checkpoint_eval_progress.py` now includes
  this known total and shows server-batch progress for DFM eval tasks before
  completed HTTP requests are available. Confidence: high.
- Additional DFM eval totals added to the monitor on 2026-06-03:
  `generative-talemaader` test split has `808` samples (`101` in shard `0/8`),
  `nordjyllandnews` is capped at `1000` samples (`125` in shard `0/8`), and
  GovReport test has `973` samples (`61` in shard `0/16`). The tmux monitor in
  `hrm-1:7.2` was restarted after the patch so it uses the updated totals.
  Confidence: high.
- HumanEval local-sandbox scoring failed when generated code contained embedded
  NUL bytes, because the upstream scorer passed the code to `python -c` and
  Python's subprocess layer raises `ValueError: embedded null byte`. The local
  `dfm-evals/dfm_evals/tasks/code.py` wrapper now uses a sanitized verifier:
  completions with NUL bytes are marked incorrect without execution, and other
  pre-exec `ValueError`s are counted as incorrect instead of crashing the task.
  The `step_50000` and `step_100000` HumanEval shard `0/4` runs were restarted
  cleanly on GPUs 5 and 4 with batch size 16. Confidence: high.

Update on 2026-06-01:

- W&B native `_step` history cannot be repaired in-place after later eval/log
  rows have advanced the run step. An attempted same-run backfill of DFM L train
  rows into `Original Plus Mixed Danish Instruction Rich L/kgnbdmwf` was
  rejected by W&B for old `_step` values; a later custom-step replay polluted
  the visible train curves and should not be used as the clean comparison run.
  Confidence: high.
- A clean comparison run was created at
  `Original Plus Mixed Danish Instruction Rich L/dfmlfull0601`
  (`dfm-L-full-train-backfill`). It backfilled DFM L train history from
  `DFM L/kgnbdmwf` before adding eval metrics, preserving native train `_step`
  values. The train backfill logged `118,775` rows, source steps `5` through
  `592,395`; W&B summary verifies `train/source_step=592395`,
  `train/loss=1.1001414060592651`, and
  `train/accuracy=0.7316066026687622`. Confidence: high.
- The same clean run now has standard `eval/*` and Danish `dfm_eval/*` metrics
  for DFM L epochs `1`, `2`, and `3`, replayed from local merged metric JSONs.
  Each epoch logged `195` standard metrics and `74` DFM metrics using
  `eval/epoch` and `dfm_eval/epoch` as the W&B plot axes. Spot-checked summary
  values include `eval/MATH/acc/epoch_1=0.3854`,
  `eval/MATH/acc/epoch_2=0.45380217999999994`,
  `eval/MATH/acc/epoch_3=0.47639826`,
  `dfm_eval/ifeval-da/instruction_following/final_acc/epoch_1=0.393870787633715`,
  `dfm_eval/ifeval-da/instruction_following/final_acc/epoch_2=0.41204577082020327`,
  and
  `dfm_eval/ifeval-da/instruction_following/final_acc/epoch_3=0.4760777566757044`.
  Confidence: high.

Update on 2026-05-31:

- Superseded: earlier on 2026-05-31, `pretrain.py` only saved checkpoints at
  epoch boundaries via `checkpoint_interval`.
- Step-based checkpointing is now implemented. `config/cfg_pretrain.yaml` has
  `checkpoint_step_interval: null` by default; setting it to a positive integer
  saves additional checkpoints during training at `fsdp2_step_{step}` and
  `carry_step_{step}.{rank}.pt`. Epoch checkpoints are still saved as
  `fsdp2_epoch_{epoch}` and `carry_epoch_{epoch}.{rank}.pt`. Confidence: high.
- Checkpoint loading now supports explicit tags. Standard/eval code can pass
  `ckpt_tag=step_10000` or `ckpt_tag=epoch_1`; the OpenAI shim accepts
  `--ckpt-tag step_10000`, and HF conversion accepts `--ckpt_tag step_10000`.
  Existing `ckpt_epoch=...` and `--ckpt-epoch ...` paths still work, and when no
  epoch/tag is passed, loading still defaults to the latest epoch checkpoint.
  Confidence: high.
- `scripts/schedule_checkpoint_evals.sh` now accepts `CKPT_TAG`, defaulting to
  `epoch_${EPOCH}`. For intra-epoch evals use, for example,
  `EPOCH=1 CKPT_TAG=step_10000 ... scripts/schedule_checkpoint_evals.sh`; the
  `EPOCH` value remains the W&B x-axis/merge epoch unless those logging scripts
  are extended separately. Confidence: high.
- Fractional eval epochs are now supported for intra-epoch checkpoints.
  `scripts/schedule_checkpoint_evals.sh` accepts `EVAL_EPOCH`, defaulting to
  `EPOCH`, and passes it to the standard/DFM/IFEval merge scripts. The merge
  and incremental DFM logging scripts parse `--epoch` as `float`, so W&B rows
  can use values such as `eval/epoch=1.234` and `dfm_eval/epoch=1.234`.
  Per-checkpoint summary aliases sanitize fractional labels with `p`, for
  example `epoch_1p234`, while integer epochs keep `epoch_1`. Confidence: high.
- Superseded: training resume was previously not implemented in `pretrain.py`.
  It is now implemented for current epoch checkpoints and new metadata-backed
  step checkpoints. `config/cfg_pretrain.yaml` exposes
  `wandb_run_id`, `wandb_resume`, `resume_checkpoint_path`,
  `resume_checkpoint_tag`, `resume_epoch`, `resume_step`, and
  `resume_batch_in_epoch`. `pretrain.py` loads DCP model and optimizer state
  from `fsdp2_{tag}`, loads rank-local carry from `carry_{tag}.{rank}.pt`,
  restores `train_state.step`, and calls `V1Dataset.set_epoch(...)` so epoch
  checkpoints continue on the next dataset epoch instead of replaying epoch 0.
  On resume, `num_params` is written to W&B summary rather than logged at step
  `0`, so a backfilled run can continue without violating W&B monotonic step
  ordering. Confidence: high.
- New checkpoints write sidecar metadata files named
  `checkpoint_state_{tag}.json` with `tag`, `step`, `epoch`,
  `batch_in_epoch`, `global_batch_size`, `data_path`, and `seed`. Step
  checkpoints such as `step_500000` use this metadata to resume inside an epoch
  by replay-skipping already completed batches. Existing old epoch checkpoints
  do not have sidecars; for them resume infers the step as
  `completed_epoch * total_steps // config.epochs`. Confidence: high.
- Example resume from an existing DFM epoch checkpoint:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 torchrun --nproc_per_node=8 pretrain.py \
  data=dfm \
  arch/size@arch=L \
  lr=2.5e-4 \
  global_batch_size=172032 \
  project_name="DFM L" \
  run_name=dfm-L-resume-epoch3 \
  checkpoint_path=checkpoints/dfm/L-resume \
  resume_checkpoint_path=checkpoints/dfm/L \
  resume_checkpoint_tag=epoch_3
```

  For new step checkpoints, use `resume_checkpoint_tag=step_500000`; if the
  sidecar JSON is missing, also provide `resume_epoch`, `resume_step`, and
  `resume_batch_in_epoch`. Confidence: high.
- The original DFM L epoch checkpoints were reconstructed with exact step
  sidecars by comparing raw local W&B train history timestamps from
  `wandb/run-20260528_234406-kgnbdmwf/run-kgnbdmwf.wandb` against checkpoint
  mtimes. The verified last logged train steps before checkpoint writes are:
  `epoch_1=164670`, `epoch_2=329380`, and `epoch_3=494080`. Sidecars
  `checkpoints/dfm/L/checkpoint_state_epoch_{1,2,3}.json` were written with
  those steps, so `resume_checkpoint_tag=epoch_3` now resolves to
  `step=494080`, `start_epoch=4`, and `skip_batches=0`. Confidence: high.
  The terminal progress-bar lines around `20840` at epoch transitions are not a
  reliable global W&B step boundary by themselves.
- W&B run `Original Plus Mixed Danish Instruction Rich L/dfm-l-resume-epoch3`
  was prepared for resuming DFM L from `epoch_3`. It contains `98,816` train
  rows backfilled from local DFM L history through step `494080`, plus standard
  `eval/*` and Danish `dfm_eval/*` metrics for epochs `1`, `2`, and `3`.
  Verified summary values include `resume_prepared_max_train_step=494080`,
  `train/loss=1.1266595125198364`, `train/accuracy=0.7248556613922119`,
  `eval/MATH/acc/epoch_3=0.47639826`, and
  `dfm_eval/ifeval-da/instruction_following/final_acc/epoch_3=0.4760777566757044`.
  Resume training should use `wandb_run_id=dfm-l-resume-epoch3` and
  `wandb_resume=allow` so it appends step `494085+` train metrics to the
  prepared run. Confidence: high.
- Caveat observed after launching the resumed run: because eval and dfm_eval
  rows were logged after the train backfill, W&B advanced the internal run step
  a few steps beyond `494080` before training resumed. The first resumed train
  log at step `494085` was warned/dropped because W&B's current internal step
  was `494087`. Subsequent train logs above that point are accepted; W&B API
  showed the run as `running` and train summary values updating. For future
  prepared resume runs, either log eval rows with explicit non-advancing/merged
  steps or expect the first one or two train logs after resume to be skipped.
  Confidence: high.
- The first DFM L epoch-3 resume attempt failed at `step_500000` while saving
  the step checkpoint because `save_train_checkpoint()` still referenced an
  old global `RANK` variable. `pretrain.py` was fixed to pass `rank` explicitly
  into checkpoint save helpers. The DCP model/optimizer checkpoint
  `checkpoints/dfm/L/fsdp2_step_500000` had already been written before the
  crash. Because `baselines.hrm_nocarry_bp_warmup` has `initial_carry() -> None`,
  the missing carry files were safely recovered as `torch.save(None, ...)` for
  ranks `0..7`, and `checkpoint_state_step_500000.json` was written with
  `step=500000`, `epoch=4`, and `batch_in_epoch=5920`. Resume now resolves
  `step_500000` to `ResumeState(tag='step_500000', step=500000, start_epoch=4,
  skip_batches=5920)`. Confidence: high.
- Goldfish loss integration assessment, 2026-06-01. Goldfish loss is a
  label-masking modification to next-token cross entropy: drop a deterministic
  or randomized subset of target tokens from loss computation by setting labels
  to the ignore index before CE. In this repo the correct integration point is
  `models/lm_head.py`, immediately before `F.cross_entropy(...)`, because
  `dataset_new.py` already emits packed `labels` with `IGNORE_LABEL_ID` and
  `LMHead` already computes masks, CE, and metrics centrally. A minimal optional
  implementation needs config fields on `LMHeadConfig`/arch config such as
  `goldfish_strategy`, `goldfish_k`, `goldfish_start_position`, and
  `goldfish_context_width`; default `goldfish_strategy: null` preserves current
  behavior. Confidence: high for integration point; medium for preferred
  strategy defaults.
- Goldfish loss is now implemented behind an explicit opt-in. Main code lives
  in `models/goldfish_loss.py`; `models/lm_head.py` applies it only when
  `arch.goldfish_strategy` is set. `config/arch/net/hrm.yaml` defaults to
  `goldfish_strategy: null`, `goldfish_k: 50`, `goldfish_context_width: 50`,
  and `goldfish_seed: 0`, so existing runs are unchanged unless the option is
  enabled. Enable Apertus-style settings with
  `arch.goldfish_strategy=hash arch.goldfish_k=50 arch.goldfish_context_width=50`.
  Validation passed with `python scripts/check_goldfish_loss.py`,
  `python -m py_compile`, and Hydra composition of the Goldfish overrides.
  Confidence: high.
- Hydra override compatibility for the resume command was fixed on 2026-06-01.
  `config/cfg_pretrain.yaml` now declares `project_name`, `run_name`,
  `checkpoint_path`, `seed`, `log_interval`, `fwd_bwd_dtype`,
  `checkpoint_step_interval`, W&B resume fields, and checkpoint resume fields.
  `config/data/dfm.yaml` now declares `target_only: true`. The DFM L
  epoch-3 resume command was checked with `python pretrain.py --cfg job ...`
  and composes without `Could not override ...` errors. Confidence: high.

Update on 2026-05-27 20:45 Europe/Berlin:

- CP4 evaluation for `original_plus_mixed_danish_instruction_rich/L` completed.
  The queued scheduler reached `FINAL_MERGE_END`, with standard evals, MATH
  shards, DFM tasks, and IFEval-DA shards all finishing with status 0 and
  writing/syncing W&B logs under
  `logs/eval/original_plus_mixed_danish_instruction_rich_L_epoch4_queued_all`
  and
  `logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch4_queued_all`.
  Confidence: high.
- DFM data prep is not complete. The full-tree tokenizer recovery is still
  running as PID `1128417` with one low-priority worker against
  `data/converted_sources`; it has begun rebuilding `data/tokenized_mixed`.
  The sampling watcher PID `1135056` is still waiting and `data/sampled_dfm`
  has not been produced yet. Confidence: high.

Superseded by 2026-05-28 00:00 Europe/Berlin:

- The one-worker tokenizer PID `1128417` and watcher PID `1135056` were stopped
  deliberately and replaced by a two-worker full-tree tokenizer run. New
  tokenizer PID: `1941931`; new watcher PID: `1942797`. Command:

```bash
ionice -c2 -n7 nice -n 10 ./data_io/tokenizer/target/release/tokenizer \
  data/converted_sources \
  --tokenizer-path /work/dfm/HRM-Text/data_io/trained_tokenizers/bpe/tokenizer.json \
  --workers 2 \
  -o data/tokenized_mixed
```

- The restarted tokenizer recognized `33` already completed tokenized dirs and
  reported `Processing 1344 files on 2 threads...`. The watcher now waits for
  PID `1941931` and samples `data/sampled_dfm` only if the tokenizer log
  contains `Done.` and more than 1000 tokenized dirs are present. Confidence:
  high.

Update on 2026-05-28 08:35 Europe/Berlin:

- CP4 metrics for `original_plus_mixed_danish_instruction_rich/L` were manually
  re-synced to W&B run `es1od1in` in project
  `Original Plus Mixed Danish Instruction Rich L`. The sync used the CP4
  standard logs, merged MATH metrics, DFM EEE exports, and merged IFEval-DA
  metrics, and reported `231` metrics synced. Log:
  `logs/eval/original_plus_mixed_danish_instruction_rich_L_epoch4_queued_all/wandb_sync_all_cp4_rerun.log`.
  Confidence: high.

Later update on 2026-05-28:

- GovReport and NordjyllandNews were removed from the standard original+mixed
  eval queues in `scripts/schedule_original_plus_mixed_cp3_evals.sh` and
  `scripts/evaluate_original_plus_mixed_standard_split.sh`; future runs should
  treat these as DFM summarization evals instead of standard `eval/*` tasks.
  Confidence: high.
- Original+mixed CP4 was evaluated on the DFM summarization tasks
  `dfm_evals/govreport` and `dfm_evals/nordjyllandnews`. Both tasks completed
  with status 0 and synced 10 metrics each to W&B run `es1od1in` under
  `dfm_eval/govreport/*` and `dfm_eval/nordjyllandnews/*`. Logs:
  `logs/dfm_evals/original_plus_mixed_danish_instruction_rich_L_epoch4_summarization_dfm_eval`.
  Confidence: high.
- `scripts/schedule_dfm_summarization_bertscore_all_checkpoints.sh` now supports
  `SKIP_ORIGINAL=1` and `SKIP_ORIGINAL_PLUS_MIXED=1`, and its server cleanup
  guard tolerates an unset `server_pid`. This avoids accidental old-family jobs
  and spurious final status 1 after successful task completion. Confidence:
  high.
- A code-generation DFM eval was added as `dfm_evals/humaneval`, wrapping
  `inspect-evals` HumanEval with Docker sandbox execution by default. The HRM
  suite entry is `hrm_code_humaneval` in
  `config/dfm_evals_hrm_single_tasks.yaml`. A zero-sample CLI probe resolved the
  task and loaded the HumanEval dataset successfully:

```bash
OPENAI_API_KEY=inspectai uv run --project dfm-evals evals suite hrm_code_humaneval \
  --file config/dfm_evals_hrm_single_tasks.yaml \
  --target-model openai/dummy \
  --target-base-url http://127.0.0.1:9/v1 \
  --mode set -- --limit 0 --log-dir /tmp/hrm_humaneval_probe --log-dir-allow-dirty
```

  Confidence: high for registration; medium for full execution because a real
  run requires a working code sandbox.
- HumanEval was run on 2026-05-28 for all 8 available L checkpoints using GPUs
  `0,1,2,3` and the local sandbox fallback because Docker was not installed on
  the node. Logs are under
  `logs/dfm_evals/humaneval_all_checkpoints_20260528`. All eight W&B sync logs
  report successful sync of `dfm_eval/humaneval/verify/accuracy`.

  Results:

  - Original Sapient epochs 1-4: accuracy `0.000`, `0.000`, `0.000`, `0.000`.
  - Original+mixed Danish-rich epochs 1-4: accuracy `0.146`, `0.238`, `0.256`,
    `0.226`.

  Confidence: high.
- Tokenization was restarted again on 2026-05-28 after two-worker resume attempts
  exited without `Done.`. The active stable fallback is one worker:
  tokenizer PID `3661868`, watcher PID `3662969`, log
  `logs/tokenize/dfm_full_recovery_tokenizer_workers1_resume5.log`. It reported
  `Processing 930 files on 1 threads...` after recognizing `447` completed
  tokenized dirs. Confidence: high.
- The one-worker tokenizer finished rebuilding the expected `1377` tokenized
  dirs, but its log did not contain `Done.`, so the strict watcher refused to
  start sampling. The one unmatched source file was
  `data/converted_sources/nemotron_swe/data/swe.parquet.unsplit`, the parked
  unsplit SWE file, not an expected tokenizer output. DFM sampling was started
  manually with `data_io/sample_tokenized.py` and is writing
  `data/sampled_dfm`. Confidence: high.

- Mixed-corpus tokenization is active at `data/tokenized_mixed`; it was previously at `1316/1317` files with the final tail in `nemotron_swe/data/swe.parquet`.
- Original Sapient-only tokenization for the L reproduction run has been launched into `data/tokenized_original_sapient`.
- The original Sapient tokenization command scans `5212` source files from:

```text
data/downloads/datasets/sapient_cleaned/data_clustered
data/downloads/datasets/sapient_cleaned/data
```

See [Original L Reproduction](/pages/original-l-reproduction.md) for the run plan.

MPS branch update on 2026-05-25:

- Repo path: `/Users/petersk/Nobackup/HRM-Text-mps`.
- After stopping a still-running background Sapient downloader, the partial Sapient download has `490` completed `.parquet`/`.jsonl` inputs under `data/downloads/datasets/sapient_cleaned` and `1` incomplete cache file.
- Completed local inputs were tokenized into `data/tokenized_original_sapient_partial`.
- Verification: `490` tokenized `metadata.json` files, about `83G`; a final tokenizer validation scan reported `Processing 0 files`.
- A small symlinked tokenized view was built at `data/tokenized_original_sapient_partial_smoke`.
- Sampling produced `data/sampled_original_sapient_partial_smoke`, about `519M`, with `metadata.total_length=21,359,878`.
- Two MPS debug training steps against this smoke sample passed with finite loss, metrics, gradients, parameters, and post-optimizer parameters.
- Gradient accumulation is implemented with `global_batch_size` as the effective optimizer token batch. Verified B-size MPS diagnostic: `global_batch_size=131072`, `gradient_accumulation_steps=8`, derived `local_microbatch_size=16384`, one optimizer step finite. Because epochs drop their own partial final effective batch, the smoke sample runs `162` optimizer steps per epoch, or `648` steps for `epochs=4`.

See [Original L Reproduction](/pages/original-l-reproduction.md) and
[Download, Convert, Tokenize, Sample](/pages/download-convert-tokenize.md) for
commands. Confidence: high.

Update on 2026-05-24:

- The active L run uses `data=original_plus_mixed_danish_instruction_rich`.
- `config/data/original_plus_mixed_danish_instruction_rich.yaml` points to `data/sampled_original_plus_mixed_danish_instruction_rich`.
- This sample preserves the original Sapient covered-token budget essentially exactly:
  - Original Sapient sample: `56,140,714,711` covered tokens across 4 epochs.
  - Original portion inside Danish-rich sample: `56,140,181,363` covered tokens across 4 epochs.
  - Difference: `-533,348` tokens, about `0.00095%`.
- All `5212 / 5212` original Sapient tokenized tasks are present; no original tasks are missing.
- The Danish-rich sample adds mixed/Danish content on top, with `110,736,199,356` global covered tokens across 4 epochs.

See [Data Mix Policy](/pages/data-mix-policy.md) for the per-category and
task-level comparison.

Later update on 2026-05-24:

- Mixed-only filtered sampling with the default prefix config completed at `data/sampled_mixed_english_danish_filtered`, but it was too large: `70,644,435,216` tokens per epoch.
- Cause: the default prefix caps did not match `sapient_cleaned__...` task names in `data/tokenized_mixed`.
- A capped config was added at `data_io/prefix_config_mixed_2x_original.yaml`.
- Dry-run estimate with PrefixLM truncation/filtering: `24,630,898,966` tokens per epoch, about `1.755x` the original Sapient per-epoch size and below the requested `2x` ceiling.
- The capped sampling run completed. Final `metadata.total_length` is `24,630,436,020` tokens per epoch, also about `1.755x` original and below the requested `2x` ceiling.
- Outputs:
  - `data/sampled_mixed_english_danish_filtered_2x_original`
  - `data/show_analytics_mixed_english_danish_filtered_2x_original.md`
  - `logs/sample_mixed_english_danish_filtered_2x_original.err`
- Hydra data config: `config/data/mixed_english_danish_filtered_2x_original.yaml`
- Note: the output directory is still about `625G` because `sample_tokenized.py` copies the full source token bank into `tokens.npy`; only the epoch indices are capped.

Update on 2026-05-21:

- The mixed corpus now has `1326` converted source files after splitting `nemotron_swe/data/swe.parquet` into `swe_part_00.parquet` through `swe_part_09.parquet`.
- A detached `tmux` tokenizer session `hrm_tok_mixed` is running one effective worker on the full `data/converted_sources` tree. It reported `Processing 10 files on 1 threads...`, corresponding to the missing split SWE shards.
- A detached `tmux` tokenizer session `hrm_tok_original` is running one effective worker on the original Sapient roots. It reported `Processing 77 files on 1 threads...`.
- Logs:
  - `logs/tokenizer_mixed_swe_resume.log`
  - `logs/tokenizer_original_resume.log`

Monitor commands:

```bash
tmux capture-pane -pt hrm_tok_mixed -S -40
tmux capture-pane -pt hrm_tok_original -S -40
find /work/dfm/HRM-Text/data/tokenized_mixed -name metadata.json | wc -l
find /work/dfm/HRM-Text/data/tokenized_original_sapient -name metadata.json | wc -l
```

Later update on 2026-05-21:

- `hrm_tok_mixed` was stopped and restarted after incremental conversion added new mixed sources.
- At restart, `data/converted_sources` had `1340` tokenizable files and `data/tokenized_mixed` had `1317` completed metadata files.
- The restarted mixed tokenizer reported `Processing 23 files on 1 threads...`.
- `hrm_tok_original` was left running.

Later update on 2026-05-21:

- The mixed tokenizer began reading the accidentally restored unsplit `data/converted_sources/nemotron_swe/data/swe.parquet`.
- `hrm_tok_mixed` was stopped, `swe.parquet` and its stale `swe.parquet.convert_meta.json` sidecar were removed, and the mixed tokenizer was restarted.
- After cleanup, `data/converted_sources` had `1339` tokenizable files, `data/tokenized_mixed` had `1318` completed metadata files, and the restarted mixed tokenizer reported `Processing 21 files on 1 threads...`.
