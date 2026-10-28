"""Normalize heterogeneous coding records into canonical AetherCoder ChatML format."""
import argparse
import hashlib
import json
import logging
import os
import re
import sys
from typing import Dict, Any, List, Optional

from src.data_factory.stream_reader import stream_records

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("normalize")

DEFAULT_SYSTEM_PROMPT = "You are AetherCoder, an expert, rigorous coding and software engineering assistant."

LANGUAGE_EXT_MAP = {
    "python": "python",
    "py": "python",
    "javascript": "javascript",
    "js": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "c++": "cpp",
    "rust": "rust",
    "rs": "rust",
    "go": "go",
    "golang": "go",
    "sql": "sql",
    "html": "html",
    "css": "css",
    "bash": "bash",
    "sh": "bash",
    "shell": "bash"
}

def detect_code_language(text: str) -> str:
    """Heuristic language detector based on keywords, syntax markers, and markdown blocks."""
    # Check for markdown code fences with language tags
    match = re.search(r"```([a-zA-Z0-9+#]+)", text)
    if match:
        tag = match.group(1).lower()
        if tag in LANGUAGE_EXT_MAP:
            return LANGUAGE_EXT_MAP[tag]

    # Heuristic signature checks
    if re.search(r"\b(def|import numpy|import os|__init__|print\(|self\.)\b", text):
        return "python"
    if re.search(r"\b(public static void main|System\.out\.println|package [a-z]+;)\b", text):
        return "java"
    if re.search(r"\b(console\.log|const\s+\w+\s*=|let\s+\w+\s*=|function\s*\(|=>\s*\{)\b", text):
        return "javascript"
    if re.search(r"\b(interface\s+\w+|type\s+\w+\s*=|:\s*string|:\s*number)\b", text):
        return "typescript"
    if re.search(r"\b(fn main|let mut|impl\s+\w+|println!)\b", text):
        return "rust"
    if re.search(r"\b(func main\(\)|fmt\.Println|package main)\b", text):
        return "go"
    if re.search(r"\b(#include <stdio\.h>|#include <iostream>|int main\(|std::cout)\b", text):
        return "cpp" if "std::" in text or "iostream" in text else "c"
    if re.search(r"\b(SELECT\s+.*FROM|CREATE TABLE|INSERT INTO|UPDATE\s+\w+\s+SET)\b", text, re.IGNORECASE):
        return "sql"
    if re.search(r"(<html|<div|<body|<!DOCTYPE html>)", text, re.IGNORECASE):
        return "html"
    if re.search(r"(\.[a-zA-Z0-9_-]+\s*\{|#[a-zA-Z0-9_-]+\s*\{|margin:\s*|padding:\s*)", text):
        return "css"
    if re.search(r"(#!/bin/bash|chmod \+x|echo \"|\$@|\$1)", text):
        return "bash"
        
    return "python" # default to python for general coding benchmarks

def infer_task_type(user_content: str) -> str:
    """Infer task type category from prompt intent."""
    lowered = user_content.lower()
    if any(k in lowered for k in ["fix", "bug", "error", "defect", "repair", "failing"]):
        return "debugging_repair"
    if any(k in lowered for k in ["test", "pytest", "unit test", "assert", "junit", "jest"]):
        return "unit_test_generation"
    if any(k in lowered for k in ["review", "refactor", "security", "optimize", "complexity"]):
        return "code_review"
    if any(k in lowered for k in ["tool", "function_call", "action", "search_files", "execute"]):
        return "agent_tool_use"
    if any(k in lowered for k in ["tamil", "விளக்கம்", "நிரல்", "பயிற்சி"]):
        return "bilingual_explanation"
    return "code_generation"

def normalize_single_record(
    raw: Dict[str, Any],
    source_id: str,
    license_id: str,
    index_hint: int = 0
) -> Optional[Dict[str, Any]]:
    """Convert arbitrary raw record into canonical schema."""
    user_prompt = ""
    assistant_reply = ""
    system_prompt = DEFAULT_SYSTEM_PROMPT
    
    # 1. Canonical messages format already
    if "messages" in raw and isinstance(raw["messages"], list):
        messages = raw["messages"]
        user_prompt = " ".join([m["content"] for m in messages if m.get("role") == "user"])
        assistant_reply = " ".join([m["content"] for m in messages if m.get("role") == "assistant"])
        task_type = raw.get("task_type") or infer_task_type(user_prompt)
        lang = raw.get("language") or detect_code_language(assistant_reply + " " + user_prompt)
        rec_id = raw.get("id") or f"{source_id.replace('/', '_')}_{index_hint:06d}"
        
        return {
            "id": rec_id,
            "messages": messages,
            "task_type": task_type,
            "language": lang,
            "source": source_id,
            "license": license_id,
            "quality_status": "unreviewed",
            "is_synthetic": raw.get("is_synthetic", False),
            "provenance": {
                "source_id": source_id,
                "original_keys": list(raw.keys()),
                "index_hint": index_hint
            }
        }

    # 2. MBPP schema: {"task_id": 1, "text": "...", "code": "...", "test_list": [...]}
    if "text" in raw and "code" in raw:
        user_prompt = raw["text"].strip()
        tests = raw.get("test_list", [])
        test_context = f"\n\nUnit tests to satisfy:\n```python\n" + "\n".join(tests) + "\n```" if tests else ""
        user_prompt = f"Write a Python program to solve this task:\n{user_prompt}{test_context}"
        code = raw["code"].strip()
        assistant_reply = f"```python\n{code}\n```"
        task_id = raw.get("task_id", index_hint)
        rec_id = f"mbpp_{task_id}"
        lang = "python"
        task_type = "code_generation"

    # 3. Alpaca / CodeAlpaca schema: {"instruction": "...", "input": "...", "output": "..."}
    elif "instruction" in raw and "output" in raw:
        instruction = raw["instruction"].strip()
        inp = (raw.get("input") or "").strip()
        if inp:
            user_prompt = f"{instruction}\n\nInput Context:\n{inp}"
        else:
            user_prompt = instruction
        assistant_reply = raw["output"].strip()
        rec_id = f"{source_id.replace('/', '_')}_{index_hint:06d}"
        lang = detect_code_language(assistant_reply + " " + user_prompt)
        task_type = infer_task_type(user_prompt)

    # 4. Prompt / Response schema: {"prompt": "...", "response": "..."}
    elif "prompt" in raw and "response" in raw:
        user_prompt = raw["prompt"].strip()
        assistant_reply = raw["response"].strip()
        rec_id = f"{source_id.replace('/', '_')}_{index_hint:06d}"
        lang = detect_code_language(assistant_reply + " " + user_prompt)
        task_type = infer_task_type(user_prompt)

    # 5. Question / Solution schema: {"question": "...", "solution": "..."}
    elif "question" in raw and ("solution" in raw or "answer" in raw):
        user_prompt = raw["question"].strip()
        assistant_reply = (raw.get("solution") or raw.get("answer")).strip()
        rec_id = f"{source_id.replace('/', '_')}_{index_hint:06d}"
        lang = detect_code_language(assistant_reply + " " + user_prompt)
        task_type = infer_task_type(user_prompt)

    else:
        # Unable to parse schema
        return None

    # Construct canonical ChatML messages
    canonical_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": assistant_reply}
    ]

    hasher = hashlib.sha256()
    hasher.update((user_prompt + assistant_reply).encode("utf-8"))

    return {
        "id": rec_id,
        "messages": canonical_messages,
        "task_type": task_type,
        "language": lang,
        "source": source_id,
        "license": license_id,
        "quality_status": "unreviewed",
        "is_synthetic": raw.get("is_synthetic", False),
        "provenance": {
            "source_id": source_id,
            "sha256": hasher.hexdigest(),
            "original_keys": list(raw.keys()),
            "index_hint": index_hint
        }
    }

def normalize_file(
    input_file: str,
    output_file: str,
    source_id: str,
    license_id: str,
    max_records: Optional[int] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Normalize input file into canonical JSONL."""
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    
    total_parsed = 0
    total_written = 0
    total_skipped = 0

    if dry_run:
        logger.info(f"DRY-RUN: Simulating normalization of {input_file}")
        for idx, raw_record in enumerate(stream_records(input_file, max_records=10)):
            norm = normalize_single_record(raw_record, source_id, license_id, index_hint=idx)
            if norm:
                total_written += 1
            else:
                total_skipped += 1
        return {"input_file": input_file, "dry_run": True, "valid": total_written, "skipped": total_skipped}

    with open(output_file, "w", encoding="utf-8") as out_f:
        for idx, raw_record in enumerate(stream_records(input_file, max_records=max_records)):
            total_parsed += 1
            normalized = normalize_single_record(raw_record, source_id, license_id, index_hint=idx)
            if normalized:
                out_f.write(json.dumps(normalized, ensure_ascii=False) + "\n")
                total_written += 1
            else:
                total_skipped += 1

    logger.info(f"Normalized {total_written}/{total_parsed} records ({total_skipped} skipped) -> {output_file}")
    return {
        "input_file": input_file,
        "output_file": output_file,
        "total_parsed": total_parsed,
        "total_written": total_written,
        "total_skipped": total_skipped
    }

def main():
    parser = argparse.ArgumentParser(description="AetherCoder Record Normalizer")
    parser.add_argument("--input", type=str, required=True, help="Input raw data file")
    parser.add_argument("--output", type=str, required=True, help="Output normalized JSONL file")
    parser.add_argument("--source-id", type=str, required=True, help="Canonical source identifier")
    parser.add_argument("--license", type=str, required=True, help="License identifier (e.g. CC-BY-4.0)")
    parser.add_argument("--max-records", type=int, default=None, help="Max records to process")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without writing output")
    args = parser.parse_args()

    res = normalize_file(
        args.input,
        args.output,
        args.source_id,
        args.license,
        max_records=args.max_records,
        dry_run=args.dry_run
    )
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
