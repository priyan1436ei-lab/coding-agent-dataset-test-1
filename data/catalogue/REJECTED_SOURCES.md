# AetherCoder-27B: Catalogue of Rejected and Restricted Data Sources

This document tracks datasets that were audited and explicitly **excluded** from the AetherCoder training corpus.

---

## 1. Rejected Sources

### `code-search-net/code_search_net`
- **Official URL**: `https://huggingface.co/datasets/code-search-net/code_search_net`
- **Licence**: `other` (aggregate of GitHub repository licences)
- **Rejection Reason**:
  - The dataset aggregates code across thousands of GitHub repositories without per-file license validation.
  - Contains viral copyleft (GPL, AGPL) and restrictive non-commercial licenses.
  - High proportion of uncurated docstring noise and repetitive boilerplate.
  - Size (>4.5 GB raw, >20 GB uncompressed) violates the local budget policy.

### `bigcode/the-stack` (Bulk Unfiltered)
- **Official URL**: `https://huggingface.co/datasets/bigcode/the-stack`
- **Licence**: Mixed / Per-file
- **Rejection Reason**:
  - Unfiltered bulk ingestion presents significant risk of unflagged PII, API tokens, and copyleft violations.
  - Requires specific per-file opt-out compliance checks before individual ingestion.

---

## 2. Quarantined Evaluation Benchmarks (Contamination Protection)

These sources are strictly forbidden from the training split:

1. **`openai/openai_humaneval`**: Official Python coding benchmark (164 coding tasks). Kept strictly in `src/evaluation/` for held-out pass@1 evaluation.
2. **`princeton-nlp/SWE-bench_Lite`**: 300 software engineering task instances from real GitHub issues. Ingestion into training would constitute severe benchmark contamination.
3. **`google-research-datasets/mbpp` (test split)**: Held out for zero-shot testing. Only the standard `train` split is admitted after contamination checks.
