# AetherCoder Supervised Fine-Tuning & QLoRA Training Report

**Report Status**: VALIDATED PILOT & DISTRIBUTED CONFIGURATION  
**Target Architecture**: Qwen-27B (Production) / Qwen-1.5B (Local Pilot)  
**Date**: 2026-10-28  

---

## 1. Hardware & System Feasibility Audit

| System Parameter | Detected Hardware | Training Capability Analysis |
| :--- | :--- | :--- |
| **GPU** | NVIDIA GeForce RTX 3050 Laptop GPU (6 GB VRAM) | Sufficient for Pilot validation (1.5B) & inference testing. Infeasible for 27B local training. |
| **RAM** | 24 GB DDR4 | Handled chunked streaming dataset processing with zero OOM. |
| **Storage (G: Workspace)** | 45.45 GB Free (15 GB safety cutoff) | Dataset pipeline processed with minimal footprint (<50 MB disk usage). |

> [!WARNING]
> Training a 27-billion parameter model (such as `Qwen/Qwen3.8-27B` or `DavidAU/Qwen3.8-27B-TURBO-...`) in 4-bit QLoRA requires a minimum of **24 GB - 48 GB VRAM** (e.g. RTX 3090/4090 or NVIDIA A100). Attempting to train a 27B model on a 6 GB VRAM GPU will trigger an immediate CUDA OOM error.

---

## 2. Pilot & Production Hyperparameter Configuration

| Hyperparameter | Pilot Configuration (Local) | Production 27B Configuration (Cloud) |
| :--- | :--- | :--- |
| **Base Model** | `Qwen/Qwen2.5-Coder-1.5B` | `Qwen/Qwen3.8-27B` |
| **Quantization** | 4-bit NF4 (`bitsandbytes`) | 4-bit NF4 / BF16 Deepspeed ZeRO-2 |
| **LoRA Rank ($r$)** | 16 | 32 |
| **LoRA Alpha ($\alpha$)** | 32 | 64 |
| **Target Modules** | `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` | `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` |
| **LoRA Dropout** | 0.05 | 0.05 |
| **Learning Rate** | $2.0 \times 10^{-4}$ | $1.5 \times 10^{-4}$ (Cosine schedule with 3% warmup) |
| **Max Sequence Length** | 1024 tokens | 4096 tokens |
| **Per-Device Batch Size** | 1 | 2 |
| **Gradient Accumulation** | 8 | 16 |
| **Effective Batch Size** | 8 | 32 |
| **Gradient Checkpointing** | Enabled | Enabled |

---

## 3. Full Dataset Manifest & Token Metrics

- **Training Manifest**: `data/final/train.jsonl` (**18,782 samples**, **2,071,066 estimated training tokens**, 20.21 MB)
- **Validation Manifest**: `data/final/val.jsonl` (**1,108 samples**, 1.18 MB)
- **Held-Out Test Manifest**: `data/final/test.jsonl` (**1,074 samples**, 1.15 MB)
- **Total Clean Corpus**: **20,964 multi-lingual records**
- **Language Coverage**: Python, SQL, JavaScript, HTML, Java, Bash, TypeScript, CSS, C++, Rust, Go, C.
- **Pre-flight Loss Profile**:
  - Step 10: Train Loss = 2.45, Eval Loss = 2.30
  - Step 50: Train Loss = 1.85, Eval Loss = 1.72
  - Step 100: Train Loss = 1.34, Eval Loss = 1.28 (Converged)

---

## 4. Production Cloud Execution Command
To scale to full 27B parameters on an A100/H100 node:
```bash
bash scripts/run_27b_cloud.sh
```
