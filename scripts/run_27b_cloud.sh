#!/usr/bin/env bash
# ==============================================================================
# AetherCoder-27B: Production Distributed Cloud Training Script
# Target Hardware: 1x to 4x NVIDIA A100 (80GB) or H100 (80GB)
# ==============================================================================

set -euo pipefail

echo "=== AetherCoder-27B Distributed Training Launch ==="

MODEL_NAME_OR_PATH="Qwen/Qwen3.8-27B"
TRAIN_DATA="data/final/train.jsonl"
VAL_DATA="data/final/val.jsonl"
OUTPUT_DIR="checkpoints/aethercoder-27b-qlora"

NUM_GPUS=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -n 1 || echo 1)
echo "Detected GPUs: ${NUM_GPUS}"

# Memory optimizations for 27B QLoRA
MAX_SEQ_LEN=4096
LORA_R=32
LORA_ALPHA=64
LEARNING_RATE=1.5e-4
BATCH_SIZE=2
GRAD_ACCUM=8

echo "Model: ${MODEL_NAME_OR_PATH}"
echo "Context Window: ${MAX_SEQ_LEN}"
echo "LoRA Rank: ${LORA_R}, Alpha: ${LORA_ALPHA}"

# Launch via Accelerate / DeepSpeed ZeRO-2/3
accelerate launch \
    --num_processes="${NUM_GPUS}" \
    --mixed_precision="bf16" \
    --use_deepspeed \
    --zero_stage=2 \
    src/training/train_qlora.py \
    --train-manifest="${TRAIN_DATA}" \
    --val-manifest="${VAL_DATA}" \
    --output-dir="${OUTPUT_DIR}" \
    --base-model="${MODEL_NAME_OR_PATH}" \
    --seq-len="${MAX_SEQ_LEN}" \
    --r="${LORA_R}" \
    --alpha="${LORA_ALPHA}" \
    --lr="${LEARNING_RATE}"

echo "=== Training Completed. Adapter weights stored in ${OUTPUT_DIR} ==="
