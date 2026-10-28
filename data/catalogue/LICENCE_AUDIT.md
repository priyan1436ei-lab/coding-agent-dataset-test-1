# AetherCoder-27B: Licence Compliance & Provenance Audit

**Audit Status**: STRICT ENFORCEMENT  
**Review Date**: 2026-10-28  

---

## 1. Compliance Principles & Ingestion Policy

1. **Explicit Commercial / Non-Infringing Permissibility**: Only sources governed by verified permissive licences (e.g. MIT, Apache 2.0, CC-BY-4.0 with attribution) are admitted into the training pipeline.
2. **Benchmark Quarantine Policy**: Benchmark datasets used for model validation (specifically `openai_humaneval`, MBPP test split, and `SWE-bench_Lite`) are **strictly prohibited** from the training pipeline to avoid benchmark memorization and contamination.
3. **No Unaudited Web Scrapes**: "Public on GitHub" does not imply permitted for commercial LLM training. CodeSearchNet contains mixed repositories with non-commercial, AGPL, or unknown licences and is **REJECTED** unless repository-level license filters are executed.

---

## 2. Approved Sources

| Dataset ID | Verified Licence | Commercial Use | Attribution Requirement | Quarantined Splits |
| :--- | :--- | :--- | :--- | :--- |
| `google-research-datasets/mbpp` | CC-BY-4.0 | Yes | Required in model release | `test` split (held out for eval) |
| `sahil2801/CodeAlpaca-20k` | CC-BY-4.0 | Yes | Required in model release | High-overlap instances with HumanEval |
| `aethercoder/synthetic-multilang-v1` | Apache-2.0 | Yes | Internal Generation | None (Full synthetic verified) |

---

## 3. Quarantined & Rejected Sources

| Dataset ID | Reason for Quarantine / Rejection | Current Status |
| :--- | :--- | :--- |
| `openai/openai_humaneval` | Core benchmark evaluation suite. Contamination would invalidate pass@1 results. | **QUARANTINED (EVALUATION ONLY)** |
| `princeton-nlp/SWE-bench_Lite` | Agentic evaluation benchmark. Preventing repository leakage is required. | **QUARANTINED (EVALUATION ONLY)** |
| `code-search-net/code_search_net` | Unaudited multi-licence corpus with potential GPL/AGPL or non-commercial files. Storage footprint (4.5GB) exceeds local quick budget. | **REJECTED** |
