#!/usr/bin/env bash
set -euo pipefail

cd /work/dfm/HRM-Text
source /work/dfm/.home/miniforge3/etc/profile.d/conda.sh
conda activate hrm

RUN_ID="${RUN_ID:-ferrum-status-map-joint-xs-ctx16k-20epoch-resume-gbs262k-$(date +%Y%m%d-%H%M%S)}"
MASTER_PORT="${MASTER_PORT:-29730}"
OLD_CKPT="checkpoints/ferrum_status_map_xs_joint/ferrum-status-map-joint-xs-ctx16k-10epoch-gbs131k-20260722-223736"
CKPT="checkpoints/ferrum_status_map_xs_joint/${RUN_ID}"
LOG_DIR="logs/ferrum_status_map_xs_joint/${RUN_ID}"

mkdir -p "$LOG_DIR" checkpoints/ferrum_status_map_xs_joint
printf '%s\n' "$RUN_ID" > "$LOG_DIR/RUN_NAME"

cat > "$LOG_DIR/launch.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd /work/dfm/HRM-Text
source /work/dfm/.home/miniforge3/etc/profile.d/conda.sh
conda activate hrm
RUN_ID="$RUN_ID" MASTER_PORT="$MASTER_PORT" scripts/resume_ferrum_xs_joint_10_more_epochs_gbs262k.sh
EOF
chmod +x "$LOG_DIR/launch.sh"

printf 'running\n' > "$LOG_DIR/train.status"
printf 'started_at=%s\n' "$(date -Is)" > "$LOG_DIR/started_at.txt"
echo "RUN_ID=$RUN_ID"
echo "LOG_DIR=/work/dfm/HRM-Text/$LOG_DIR"
echo "CKPT=/work/dfm/HRM-Text/$CKPT"
echo "RESUME=$OLD_CKPT:epoch_10"
echo "GLOBAL_BATCH_SIZE=262144"
echo "WANDB=https://wandb.ai/peter-sk-sdu/Ferrum-HRM/runs/$RUN_ID"

set +e
env WANDB_MODE=online OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 TOKENIZERS_PARALLELISM=false \
  torchrun --nproc_per_node=8 --master_port="$MASTER_PORT" \
  pretrain.py \
  data=hlm \
  arch/size@arch=XS \
  data.path=data/sampled_ferrum_status_map_joint_v2_xs_ctx16k_20epoch \
  +data.validation_path=data/sampled_ferrum_status_map_joint_v2_validation_ctx16k \
  +data.target_only=true \
  epochs=20 \
  global_batch_size=262144 \
  gradient_accumulation_steps=1 \
  lr=2e-4 \
  lr_min_ratio=1.0 \
  lr_warmup_steps=5 \
  weight_decay=0.1 \
  beta1=0.9 \
  beta2=0.95 \
  ema=null \
  distributed_strategy=ddp \
  ddp_params_precision=fp32 \
  fwd_bwd_dtype=bfloat16 \
  accelerator_type=sm100 \
  compile_train_batch=false \
  checkpoint_format=sharded \
  checkpoint_interval=1 \
  +validation_interval=20 \
  +validation_batches=8 \
  log_interval=1 \
  project_name=Ferrum-HRM \
  run_name="$RUN_ID" \
  wandb_run_id="$RUN_ID" \
  wandb_resume=allow \
  resume_checkpoint_path="$OLD_CKPT" \
  resume_checkpoint_tag=epoch_10 \
  checkpoint_path="$CKPT" \
  >"$LOG_DIR/train.stdout.txt" \
  2>"$LOG_DIR/train.stderr.txt"
code=$?
set -e

printf '%s\n' "$code" > "$LOG_DIR/train.status"
printf 'finished_at=%s\n' "$(date -Is)" > "$LOG_DIR/finished_at.txt"
exit "$code"
