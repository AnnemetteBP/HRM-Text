#!/usr/bin/env bash
set -euo pipefail

source /home/ucloud/miniforge3/etc/profile.d/conda.sh
conda activate hrm

PLAN="logs/scheduler/dfm8_L_campaign_epoch2_20260803"
BASE_LOG="dfm8_L_campaign_epoch2"
PY="/home/ucloud/miniforge3/envs/hrm/bin/python"
CKPT="checkpoints/dfm8/L-gbs131072"
STEPS_PER_EPOCH=268651
TRAIN_CMD="OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 torchrun --nproc_per_node=8 pretrain.py data=dfm8 arch/size@arch=L lr=3e-4 lr_min_ratio=1 lr_warmup_steps=2000 weight_decay=0.1 beta1=0.9 beta2=0.95 ema=0.9999 global_batch_size=262144 gradient_accumulation_steps=1 epochs=2 distributed_strategy=fsdp fsdp_params_precision=fp32 checkpoint_format=sharded fwd_bwd_dtype=bfloat16 accelerator_type=sm100 compile_train_batch=true checkpoint_interval=1 checkpoint_step_interval=10000 ephemeral_checkpoint_step_interval=1000 checkpoint_path=checkpoints/dfm8/L-gbs131072 reset_ema_on_resume=false upcast_optimizer_state_on_resume=false project_name=DFM5 run_name=DFM8-L-gbs131072 wandb_run_id=g2oaotmc wandb_resume=allow"

if [[ -e "$PLAN" ]]; then
  echo "Refusing to overwrite existing plan: $PLAN" >&2
  exit 1
fi

create_eval() {
  local step="$1"
  local mode="$2"
  local epoch
  epoch="$($PY -c "print($step / $STEPS_PER_EPOCH)")"
  local export_dir="/work/dfm/HRM-Text/exports/dfm8_L_step${step}_ema_hf"
  local args=(
    python -m eval_scheduler plan create
    --plan-dir "$PLAN"
    --ckpt-path "$CKPT"
    --ckpt-tag "step_${step}"
    --eval-epoch "$epoch"
    --log-root "logs/eval/${BASE_LOG}/step_${step}"
    --dfm-log-root "logs/dfm_evals/${BASE_LOG}/step_${step}"
    --euroeval-log-root "logs/euroeval/${BASE_LOG}/step_${step}"
    --wandb-project DFM5
    --wandb-run-id g2oaotmc
    --wandb-run-name DFM8-L-gbs131072
    --model-prefix hrm-dfm8-L-vllm-native-proxy
    --run-euroeval
    --queue-order euroeval-first
    --dfm-ifeval-shards 32
    --max-retries 5
    --standard-batch 128
    --dfm-batch 64
    --ifeval-batch 64
    --euroeval-batch 64
    --python-bin "$PY"
    --standard-config evaluation/config/dfm6_vllm_benchmarking.yaml
    --port-base 57000
    --checkpoint-wait-seconds 60
    --standard-engine-backend vllm
    --standard-hf-export-dir "$export_dir"
    --hrm-server-backend vllm
    --hrm-hf-export-dir "$export_dir"
    --hrm-vllm-native-proxy
    --hrm-vllm-gemma-bfcl-tools
    --hrm-vllm-gemma-bfcl-tool-mode parser
    --vllm-python "$PY"
    --vllm-dtype bfloat16
    --vllm-max-model-len 4096
    --vllm-gpu-memory-utilization 0.9
    --min-gpu-free-mib 178000
    --vllm-attention-backend FLASH_ATTN
    --vllm-extra-args "--enforce-eager --attention-backend FLASH_ATTN --chat-template /work/dfm/HRM-Text/evaluation/chat_templates/gemma4_native_chat.jinja"
    --euroeval-max-concurrent-calls 64
    --judge-model openai/gemma-4-e4b-judge
    --judge-server-model unsloth/gemma-4-E4B-it
    --judge-server-dtype bfloat16
    --judge-server-attn-implementation sdpa
    --judge-server-max-new-tokens 64
    --judged-max-connections 32
    --judged-batch 32
    --judged-vllm-gpu-memory-utilization 0.65
    --judged-min-gpu-free-mib 178000
    --govreport-max-report-chars 9000
  )
  if [[ "$mode" == "append" ]]; then
    args+=(--append)
  else
    args+=(--force)
  fi
  "${args[@]}"
}

add_release() {
  local step="$1"
  python -m eval_scheduler plan add-eval-release \
    --plan-dir "$PLAN" \
    --checkpoint-tag "step_${step}" \
    --barrier-job-id "campaign-barrier-${step}" \
    --teardown-job-id "campaign-teardown-${step}"
}

add_training() {
  local source="$1"
  local target="$2"
  local resume_tag="$3"
  local deps="$4"
  local args=(
    python -m eval_scheduler plan add-training
    --plan-dir "$PLAN"
    --job-id "campaign-train-${target}"
    --stop-after-step "$target"
    --command "$TRAIN_CMD"
    --checkpoint-path "$CKPT"
    --log-dir "logs/training/dfm8_L_epoch2/${source}_to_${target}"
    --resume-from-tag "$resume_tag"
    --workdir /work/dfm/HRM-Text
    --checkpoint-carry-ranks 8
    --min-gpu-free-mib 178000
  )
  if [[ -n "$deps" ]]; then
    args+=(--deps "$deps")
  fi
  "${args[@]}"
}

create_eval 300000 fresh
add_release 300000
add_training epoch_1 300000 epoch_1 ""

for step in 350000 400000 450000 500000; do
  previous=$((step - 50000))
  create_eval "$step" append
  add_release "$step"
  add_training "$previous" "$step" "step_${previous}" "campaign-teardown-${previous}"
done

# The metadata-derived total is an upper estimate. If epoch_1 packs into fewer
# batches, the training loop naturally exhausts it and writes epoch_2 first.
add_training 500000 537714 step_500000 campaign-teardown-500000

python -m eval_scheduler status --plan-dir "$PLAN"
