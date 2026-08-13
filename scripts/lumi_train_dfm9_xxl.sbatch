#!/bin/bash
#SBATCH --job-name=hrm-dfm9-XXL
#SBATCH --account=project_465002606
#SBATCH --partition=standard-g
#SBATCH --nodes=32
#SBATCH --gpus-per-node=8
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=56
#SBATCH --mem=480G
#SBATCH --time=18:30:00
#SBATCH --output=logs/lumi/%x-%j.out
#SBATCH --error=logs/lumi/%x-%j.err

# DFM9 "XXL" training on LUMI-G (AMD MI250X / ROCm).
#
# Based on the reference sm100 (B200) DFM6 recipe (data=dfm6, arch=XL, epochs=5,
# FSDP2, sharded checkpoints, bf16), adapted for accelerator_type=rocm and scaled
# up for LUMI multi-node throughput.
#
# Scaling choice (2026-06-21): target ~32768 tokens per GCD per optimizer step
# (8 packed 4096-token sequences) for good MI250X utilization, on 16 nodes = 128
# GCDs. That gives global_batch_size = 32768 * 128 = 4,194,304, a 16x increase
# over the reference 262144. LR is sqrt-scaled with batch (sqrt(16)=4x):
# 3.0e-4 -> 1.2e-3, with warmup raised to 4000 steps.
#
# Packing constraint (pretrain.py): the PHYSICAL microbatch per GCD
#   global_batch_size / world_size / gradient_accumulation_steps
# must be >= context length (4096; dfm6 max_seq_len=4097). Here:
#   physical microbatch = 4194304 / 128 / 4 = 8192 -> 2 packed seqs/GCD. OK.
#   (effective per-GCD tokens/step = 4194304 / 128 = 32768 = 8 seqs.)
# If you change node count, keep per-GCD = global_batch_size/world_size at 32768
# by scaling GLOBAL_BATCH_SIZE with the node count (env override below).
#
# Memory: XL backbone (~1.2B) + Gemma vocab 262144 embeddings/head = ~1.79B params
# total (verified: num_params=1,786,773,504). Memcheck on 2 GCDs (dev-g) showed
# the activation memory caps the PHYSICAL microbatch at ~2 packed seqs (8192
# tokens) per GCD in bf16: 8 seqs and 4 seqs both OOM, 2 seqs fits. So we reach
# the 32768-token/GCD target via GRAD_ACCUM=4 (4 x 8192). NOTE: that test was at
# 2 GCDs; FSDP2 shards optimizer state across all ranks, so at 128 GCDs each GCD
# holds far less state and GRAD_ACCUM=2 (4 seqs, 16384/microbatch) may also fit.
# Try GRAD_ACCUM=2 at full scale to roughly halve step count if it does not OOM.
# PYTORCH_HIP_ALLOC_CONF=expandable_segments:True is set to reduce fragmentation.

set -euo pipefail

REPO=/projappl/project_465002606/frommoge/HRM-Text
SIF=/appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif
VENV=${REPO}/.venv-lumi
DATA=/scratch/project_465002606/frommoge/data/sampled_dfm9
CKPT=/scratch/project_465002606/frommoge/checkpoints/dfm9/XXL-32

# Per-project caches on scratch so they persist and are shared across nodes.
MIOPEN_CACHE=/scratch/project_465002606/frommoge/cache/miopen
TRITON_CACHE=/scratch/project_465002606/frommoge/cache/triton

mkdir -p "${REPO}/logs/lumi" "${CKPT}" "${MIOPEN_CACHE}" "${TRITON_CACHE}"

if [ ! -f "${DATA}/metadata.json" ]; then
  echo "ERROR: dataset not found at ${DATA} (metadata.json missing)." >&2
  echo "Copy sampled_dfm9 from UCloud first." >&2
  exit 1
fi

GPUS_PER_NODE=8
NNODES=${SLURM_JOB_NUM_NODES:-32}
WORLD_SIZE=$(( NNODES * GPUS_PER_NODE ))

# Hyperparameters (overridable via env at submit time). Defaults target
# 32768 tokens/GCD at 128 GCDs with sqrt-scaled LR.
GLOBAL_BATCH_SIZE=${GLOBAL_BATCH_SIZE:-1048576}
GRAD_ACCUM=${GRAD_ACCUM:-1}
LR=${LR:-1.0e-3}
WARMUP_STEPS=${WARMUP_STEPS:-2000}
EPOCHS=${EPOCHS:-1}

# Checkpointing: every epoch + every 10k steps + a rolling 1k ephemeral that
# auto-deletes. Sharded format for fast FSDP save/load.
CKPT_INTERVAL=1
CKPT_STEP_INTERVAL=10000
EPHEMERAL_CKPT_STEP_INTERVAL=250

PREFETCH=${PREFETCH:-16}

# Validate the packing constraint before launching.
PER_GCD=$(( GLOBAL_BATCH_SIZE / WORLD_SIZE / GRAD_ACCUM ))
if [ "$(( GLOBAL_BATCH_SIZE % (WORLD_SIZE * GRAD_ACCUM) ))" -ne 0 ]; then
  echo "ERROR: global_batch_size ${GLOBAL_BATCH_SIZE} not divisible by world_size*grad_accum (${WORLD_SIZE}*${GRAD_ACCUM})." >&2
  exit 1
fi
if [ "${PER_GCD}" -lt 4096 ]; then
  echo "ERROR: physical microbatch ${PER_GCD} < context length 4096; sequences cannot pack." >&2
  echo "Raise GLOBAL_BATCH_SIZE, lower GRAD_ACCUM, or reduce node count." >&2
  exit 1
fi
echo "nnodes=${NNODES} world_size=${WORLD_SIZE} global_batch_size=${GLOBAL_BATCH_SIZE} microbatch_per_gcd=${PER_GCD} grad_accum=${GRAD_ACCUM} lr=${LR} warmup=${WARMUP_STEPS} epochs=${EPOCHS}"

# Auto-resume from the newest sharded step checkpoint, if any.
RESUME_ARGS=""
LATEST_TAG=""
if [ -d "${CKPT}" ]; then
  LATEST_TAG=$(ls -1d "${CKPT}"/fsdp2_ephemeral_step_* 2>/dev/null \
    | sed 's#.*/fsdp2_##' \
    | sort -t_ -k2 -n \
    | tail -n1 || true)
fi
if [ -n "${LATEST_TAG}" ]; then
  echo "Resuming from checkpoint tag ${LATEST_TAG}"
  RESUME_ARGS="resume_checkpoint_path=${CKPT} resume_checkpoint_tag=${LATEST_TAG}"
else
  echo "No existing step checkpoint found; starting a fresh run."
fi

MASTER_ADDR=$(scontrol show hostnames "${SLURM_JOB_NODELIST}" | head -n1)
export MASTER_ADDR
export MASTER_PORT=29500

BIND="-B /project/project_465002606 -B /scratch/project_465002606 -B /projappl/project_465002606 -B /flash/project_465002606"

# One srun task per node; each runs torchrun with its SLURM_NODEID as node_rank.
srun bash -c "
  MA=\$(scontrol show hostnames \"\${SLURM_JOB_NODELIST}\" | head -n1)
  singularity exec ${BIND} ${SIF} bash -c \"
    module use /appl/local/containers/ai-modules/
    module load singularity-AI-bindings
    cd ${REPO}
    source ${VENV}/bin/activate
    export PYTHONPATH=.
    export MIOPEN_USER_DB_PATH=${MIOPEN_CACHE}
    export MIOPEN_CUSTOM_CACHE_DIR=${MIOPEN_CACHE}
    export TRITON_CACHE_DIR=${TRITON_CACHE}
    export PYTORCH_HIP_ALLOC_CONF=expandable_segments:True
    export WANDB_MODE=\\\${WANDB_MODE:-offline}
    export OMP_NUM_THREADS=7
    export NCCL_SOCKET_IFNAME=hsn
    export NCCL_NET_GDR_LEVEL=PHB
    export MPICH_GPU_SUPPORT_ENABLED=1
    python -m torch.distributed.run \
      --nnodes=${NNODES} \
      --nproc_per_node=${GPUS_PER_NODE} \
      --node_rank=\\\${SLURM_NODEID} \
      --master_addr=\${MA} \
      --master_port=${MASTER_PORT} \
      pretrain.py \
        data=dfm9 \
        data.path=${DATA} \
        arch/size@arch=XXL \
	+arch.bp_min_steps=2 \
    	arch.bp_max_steps=5 \
    	arch.bp_warmup_ratio=0.2 \
        accelerator_type=rocm \
        distributed_strategy=fsdp \
	fsdp_params_precision=fp32 \
        checkpoint_format=sharded \
        fwd_bwd_dtype=bfloat16 \
        lr=${LR} \
        lr_min_ratio=1 \
	lr_warmup_steps=${WARMUP_STEPS} \
	weight_decay=0.1 \
	beta1=0.9 \
    	beta2=0.95 \
    	ema=0.9999 \
        epochs=${EPOCHS} \
        global_batch_size=${GLOBAL_BATCH_SIZE} \
        gradient_accumulation_steps=${GRAD_ACCUM} \
    	compile_train_batch=true \
	dataloader_prefetch_factor=${PREFETCH} \
        checkpoint_interval=${CKPT_INTERVAL} \
        checkpoint_step_interval=${CKPT_STEP_INTERVAL} \
        ephemeral_checkpoint_step_interval=${EPHEMERAL_CKPT_STEP_INTERVAL} \
	reset_ema_on_resume=false \
   	upcast_optimizer_state_on_resume=false \
        project_name='DFM9' \
        run_name=dfm9-XXL-lumi \
        checkpoint_path=${CKPT} \
        ${RESUME_ARGS}
  \"
"
