# AetherCoder-27B: Hardware & Storage Environment Report

**Audit Timestamp**: 2026-10-28 19:02:00 IST  
**Environment**: Local Development Node  

---

## 1. Physical Hardware & System Specifications

| Component | Detected Specification | Constraint Analysis |
| :--- | :--- | :--- |
| **Operating System** | Windows 11 Home Single Language (64-bit) | Native PowerShell / Python 3.13 environment |
| **System RAM** | 24.0 GB (24,842,968 KB total, ~6.5 GB free) | Ample for chunked streaming, insufficient for in-memory corpus loading (>50GB) |
| **GPU** | NVIDIA GeForce RTX 3050 Laptop GPU | 6,144 MiB (6 GB) GDDR6 VRAM, Driver 591.74, CUDA 13.1 |
| **Storage (G: Workspace)** | 45.45 GB Free (out of 474.71 GB) | Active project location: `G:\My Drive\datasettttt` |
| **Storage (C: System)** | 47.85 GB Free (out of 474.72 GB) | System drive |

---

## 2. 27B Model Feasibility Analysis

### Theoretical Memory Requirements (27B Parameters)
- **16-bit Float (BF16 / FP16)**: $\approx 27 \times 10^9 \times 2 \text{ bytes} \approx 54 \text{ GB}$ VRAM.
- **8-bit Quantization (Int8)**: $\approx 27 \text{ GB}$ VRAM.
- **4-bit NormalFloat (NF4 QLoRA)**:
  - Base Weights: $\approx 13.5 \text{ GB} - 15 \text{ GB}$.
  - LoRA Adapter Weights ($r=16, \alpha=32$): $\approx 150 \text{ MB}$.
  - Optimizer States (AdamW 32-bit for LoRA parameters): $\approx 400 \text{ MB}$.
  - Activation Memory (Gradient Checkpointing, batch size 1, sequence length 2048): $\approx 4 \text{ GB} - 6 \text{ GB}$.
  - **Total Minimum 4-bit VRAM Required**: **$\approx 18 \text{ GB} - 22 \text{ GB}$**.

### Local Hardware Verdict
- The detected local GPU has **6 GB VRAM**.
- Loading a 27B model (even at 4-bit) requires $\ge 14\text{ GB}$ VRAM, resulting in immediate **CUDA Out-of-Memory (OOM)**.
- **Resolution**:
  1. **Local Pilot Target**: Use `Qwen/Qwen2.5-Coder-1.5B` to validate dataset tokenization, loss convergence, and QLoRA pipeline under $\le 5\text{ GB}$ VRAM.
  2. **Production 27B Cloud Target**: Provide distributed launch configuration (`scripts/run_27b_cloud.sh`) targeting an A100 (40GB/80GB) or H100 node with DeepSpeed Zero-3 / FSDP.

---

## 3. Strict Storage Budget & Safeguards

To strictly obey safety constraints and prevent disk saturation on the G: drive (45.45 GB free):

- **Safe Disk Floor**: Hard cutoff if free space on G: drops below **15.0 GB**.
- **Max Raw Download Cap**: **2.0 GB** total raw compressed data.
- **Max Processed Manifest Cap**: **1.0 GB** JSONL.
- **Processing Mode**: Mandatory chunked streaming (500 records per batch) with streaming disk writes (`data/normalized`, `data/deduplicated`, `data/final`). Never load entire datasets into RAM.
- **Temporary Cache Cleanup**: Automatic removal of uncompressed staging files after normalization and hash verification.
