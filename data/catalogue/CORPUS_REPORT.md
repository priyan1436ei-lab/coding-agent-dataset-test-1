# AetherCoder-27B Corpus Quality & Statistics Report

**Generated At**: 2026-10-28 14:02:03 UTC  
**Corpus File**: `data/final/train.jsonl`  

---

## 1. Executive Summary

| Metric | Measured Value |
| :--- | :--- |
| **Total Records Retained** | **18,782** |
| **Total Actual Size** | **20.21 MB** |
| **Estimated Training Tokens** | **2,071,066 tokens** |
| **Average Tokens / Record** | **110.3** |
| **Synthetic Data Percentage** | **0.09%** |

---

## 2. Pipeline Attrition & Quality Funnel

| Stage | Record Count | Pass / Retention Rate |
| :--- | :--- | :--- |
| Discovered Candidates | 21,012 | 100% |
| Downloaded Approved Records | 21,012 | 100% |
| Successfully Normalized | 21,012 | 100.0% |
| Deduplication Retained | 21,010 | 100.0% |
| Quality Filter Passed | 20,972 | 99.8% |
| Contamination Filter Passed | 20,964 | 100.0% |

---

## 3. Programming Language Distribution

| Language | Record Count | Share (%) |
| :--- | :--- | :--- |
| `python` | 15,356 | 81.8% |
| `sql` | 972 | 5.2% |
| `javascript` | 829 | 4.4% |
| `html` | 610 | 3.2% |
| `java` | 407 | 2.2% |
| `bash` | 200 | 1.1% |
| `typescript` | 155 | 0.8% |
| `css` | 146 | 0.8% |
| `cpp` | 85 | 0.5% |
| `rust` | 8 | 0.0% |
| `go` | 8 | 0.0% |
| `c` | 6 | 0.0% |

---

## 4. Task Distribution

| Task Category | Record Count | Share (%) |
| :--- | :--- | :--- |
| `code_generation` | 18,135 | 96.6% |
| `debugging_repair` | 236 | 1.3% |
| `unit_test_generation` | 234 | 1.2% |
| `code_review` | 95 | 0.5% |
| `agent_tool_use` | 78 | 0.4% |
| `bilingual_explanation` | 4 | 0.0% |

---

## 5. Provenance & Source Allocation

| Source ID | Record Count | Share (%) |
| :--- | :--- | :--- |
| `sahil2801/CodeAlpaca-20k` | 17,894 | 95.3% |
| `google-research-datasets/mbpp` | 872 | 4.6% |
| `aethercoder/synthetic-multilang-v1` | 16 | 0.1% |

---

## 6. License Audit & Contamination Safeguards
- **Permissive Sources Only**: 100% of admitted records carry CC-BY-4.0 or Apache-2.0 licenses with full attribution metadata preserved.
- **Quarantined Benchmarks**: HumanEval (164 tasks), MBPP test split, and SWE-bench Lite verified zero overlap.
- **Unresolved Inquiries**: 0 (CodeSearchNet unverified licenses successfully quarantined and rejected).
