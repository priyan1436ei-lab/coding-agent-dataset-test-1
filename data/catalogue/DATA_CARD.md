# Dataset Card: AetherCoder-Corpus-v1

## Dataset Summary
AetherCoder-Corpus-v1 is a curated, legally compliant, multi-language coding dataset engineered for instruction tuning, debugging, test generation, repository-level tool use, and bilingual technical explanations (Tamil-English + Standard English).

### Supported Languages
- **Primary Languages**: Python, Java, C, C++, JavaScript, TypeScript, SQL, HTML, CSS, Rust, Go, Bash.
- **Natural Languages**: English, Tamil-English bilingual code explanations.

### Task Categories
1. **`code_generation`**: Generating functions, classes, and algorithms from natural language descriptions.
2. **`debugging_repair`**: Detecting syntactic, logical, and performance bugs in broken snippets and producing verified diffs/fixes.
3. **`unit_test_generation`**: Formulating parameterized unit tests (`pytest`, `JUnit`, `Jest`, etc.) for provided code.
4. **`code_review`**: Analyzing code for security vulnerabilities, edge cases, and style refactorings.
5. **`agent_tool_use`**: Step-by-step tool-calling interactions (file read, file search, bash commands, test inspection).
6. **`bilingual_explanation`**: Technical programming walkthroughs in Tamil-English code commentary for diverse engineering communities.

---

## Data Schema
Each record is serialized in standard JSONL with ChatML-compatible `messages`:
```json
{
  "id": "aether-py-00042",
  "messages": [
    {"role": "system", "content": "You are AetherCoder, an expert programming assistant."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "task_type": "code_generation",
  "language": "python",
  "source": "approved-dataset-id",
  "license": "CC-BY-4.0",
  "quality_status": "verified",
  "is_synthetic": false,
  "provenance": {
    "pipeline_version": "1.0.0",
    "sha256": "abcdef...",
    "cleaned_at": "2026-10-28T19:00:00Z"
  }
}
```

---

## Quality & Contamination Controls
- **Deduplication**: Strict SHA-256 hash deduplication on normalized AST/code text + MinHash 3-gram similarity.
- **Secret Filtering**: Automated regex rejection of AWS, GitHub, OpenAI tokens, RSA private keys, and passwords.
- **De-contamination**: Strict 10-gram and docstring similarity exclusion against HumanEval, MBPP test, and SWE-bench.
- **Execution Verification**: Code snippets pass Python `ast.parse()` validation and safe isolated syntax linters.
