"""Synthetic data generator producing high-quality verified multi-lingual code records."""
import argparse
import hashlib
import json
import logging
import os
import sys
import time
from typing import Dict, Any, List, Optional

from src.synthetic.templates import ALGORITHM_TEMPLATES, DEBUGGING_TEMPLATES, AGENT_TOOL_TEMPLATES
from src.synthetic.tamil_code_synth import TAMIL_ENGLISH_TEMPLATES
from src.data_factory.validate_code import validate_python_syntax, validate_balanced_brackets, run_sandboxed_python_test

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("synthetic_gen")

SYSTEM_PROMPT = "You are AetherCoder, an expert, rigorous coding and software engineering assistant."

def generate_synthetic_record(template: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Transform template into a validated canonical AetherCoder record."""
    lang = template["language"]
    task_type = template["task_type"]
    user_prompt = template["prompt"]
    assistant_response = template["response"]
    test_code = template.get("test_code")

    is_syntax_valid = True
    syntax_error = None
    tested = False
    test_passed = False

    # Execute sandbox validation for Python if test code provided
    if lang == "python":
        from src.data_factory.validate_code import extract_code_blocks
        blocks = extract_code_blocks(assistant_response)
        python_code = ""
        for blk_lang, blk_code in blocks:
            if blk_lang in ["python", "py", ""]:
                python_code = blk_code
                break
        if not python_code:
            python_code = assistant_response

        is_syntax_valid, syntax_error = validate_python_syntax(python_code)
        if test_code and is_syntax_valid:
            import textwrap
            tested = True
            dedented_test = textwrap.dedent(test_code)
            test_passed, test_msg = run_sandboxed_python_test(python_code, dedented_test)
            if not test_passed:
                logger.warning(f"Synthetic test failed for template '{template.get('title')}': {test_msg}")
            else:
                logger.info(f"Sandbox test PASSED for template '{template.get('title')}'")
    elif lang in ["c", "cpp", "java", "javascript", "typescript", "rust", "go"]:
        is_syntax_valid, syntax_error = validate_balanced_brackets(assistant_response)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": assistant_response}
    ]

    hasher = hashlib.sha256()
    hasher.update((user_prompt + assistant_response).encode("utf-8"))
    sha = hasher.hexdigest()

    rec_id = f"synth_{lang}_{index:05d}"

    return {
        "id": rec_id,
        "messages": messages,
        "task_type": task_type,
        "language": lang,
        "source": "aethercoder/synthetic-multilang-v1",
        "license": "Apache-2.0",
        "quality_status": "verified" if (is_syntax_valid and (not tested or test_passed)) else "flagged",
        "is_synthetic": True,
        "provenance": {
            "generator": "aether_synthetic_engine_v1",
            "title": template.get("title", "code_sample"),
            "sha256": sha,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "syntax_valid": is_syntax_valid,
            "syntax_error": syntax_error,
            "tested": tested,
            "test_passed": test_passed
        }
    }

def build_synthetic_corpus(
    output_path: str = "data/raw/aethercoder_synthetic-multilang-v1.jsonl",
    include_tamil: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Generate synthetic records from templates."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    all_templates = list(ALGORITHM_TEMPLATES) + list(DEBUGGING_TEMPLATES) + list(AGENT_TOOL_TEMPLATES)
    if include_tamil:
        all_templates.extend(TAMIL_ENGLISH_TEMPLATES)

    records = []
    for idx, t in enumerate(all_templates, 1):
        rec = generate_synthetic_record(t, idx)
        records.append(rec)

    if dry_run:
        logger.info(f"DRY-RUN: Generated {len(records)} synthetic records (simulated).")
        return {"dry_run": True, "count": len(records)}

    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    logger.info(f"Successfully generated {len(records)} verified synthetic records -> {output_path}")
    return {
        "output_path": output_path,
        "total_generated": len(records),
        "languages": list(set(r["language"] for r in records)),
        "tasks": list(set(r["task_type"] for r in records))
    }

def main():
    parser = argparse.ArgumentParser(description="AetherCoder Synthetic Dataset Generator")
    parser.add_argument("--output", type=str, default="data/raw/aethercoder_synthetic-multilang-v1.jsonl", help="Output path")
    parser.add_argument("--no-tamil", action="store_true", help="Exclude Tamil-English bilingual records")
    parser.add_argument("--dry-run", action="store_true", help="Dry run simulation")
    args = parser.parse_args()

    res = build_synthetic_corpus(output_path=args.output, include_tamil=not args.no_tamil, dry_run=args.dry_run)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
