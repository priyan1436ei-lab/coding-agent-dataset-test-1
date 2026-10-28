"""Quality filter: Removes malformed records, low-entropy noise, secrets, and dangerous payloads."""
import argparse
import json
import logging
import os
import re
import sys
from typing import Dict, Any, Tuple, Optional, List

from src.data_factory.stream_reader import stream_jsonl

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("filter_quality")

# Regex patterns for secret detection
SECRET_PATTERNS = [
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS_ACCESS_KEY"),
    (re.compile(r"\bghp_[a-zA-Z0-9]{36}\b"), "GITHUB_PAT"),
    (re.compile(r"\bgithub_pat_[a-zA-Z0-9_]{40,}\b"), "GITHUB_PAT_FINE_GRAINED"),
    (re.compile(r"\bsk-[a-zA-Z0-9]{32,}\b"), "OPENAI_API_KEY"),
    (re.compile(r"-----BEGIN\s+(RSA|EC|DSA|OPENSSH)?\s*PRIVATE\s+KEY-----"), "PRIVATE_KEY"),
    (re.compile(r"(?i)(api_key|secret_key|client_secret)\s*[:=]\s*['\"][a-zA-Z0-9_=-]{16,}['\"]"), "GENERIC_API_SECRET")
]

# Unsafe malicious execution patterns
MALICIOUS_PATTERNS = [
    (re.compile(r"\brm\s+-rf\s+/(?:\s|$|\*)"), "DANGEROUS_RM_ROOT"),
    (re.compile(r"\bformat\s+c:", re.IGNORECASE), "DANGEROUS_FORMAT_DISK"),
    (re.compile(r":\(\)\{\s*:\|\:&\s*\};:"), "FORK_BOMB"),
    (re.compile(r"\bmkfs\.(ext4|vfat|ntfs)\s+/dev/sd[a-z]"), "DESTRUCTIVE_FILESYSTEM")
]

def check_secrets(text: str) -> Optional[str]:
    """Scan text for high-risk hardcoded API credentials or keys."""
    for pattern, name in SECRET_PATTERNS:
        if pattern.search(text):
            return name
    return None

def check_malicious_payload(text: str) -> Optional[str]:
    """Scan text for explicitly destructive operating system commands."""
    for pattern, name in MALICIOUS_PATTERNS:
        if pattern.search(text):
            return name
    return None

def check_repetitive_noise(text: str) -> bool:
    """Detect degenerate token repetition and low-information spam."""
    if len(text) < 10:
        return True
    
    # Check for excessive single-character repetition (e.g. aaaaa...)
    if re.search(r"(.)\1{30,}", text):
        return True
        
    # Check line-level repetition
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) >= 8:
        unique_lines = set(lines)
        if len(unique_lines) / len(lines) < 0.25:
            # More than 75% repetitive lines
            return True

    return False

def inspect_record_quality(record: Dict[str, Any], min_chars: int = 25, max_chars: int = 64000) -> Tuple[bool, str]:
    """Audit single canonical record for syntax, safety, entropy, and length.
    Returns (is_valid, rejection_reason).
    """
    if not isinstance(record, dict):
        return False, "MALFORMED_RECORD_NOT_DICT"

    messages = record.get("messages")
    if not isinstance(messages, list) or len(messages) < 2:
        return False, "INSUFFICIENT_MESSAGES"

    # Verify user and assistant exist and have valid content
    user_msgs = [m for m in messages if m.get("role") == "user" and m.get("content")]
    asst_msgs = [m for m in messages if m.get("role") == "assistant" and m.get("content")]

    if not user_msgs:
        return False, "MISSING_USER_PROMPT"
    if not asst_msgs:
        return False, "MISSING_ASSISTANT_REPLY"

    full_content = " ".join([m.get("content", "") for m in messages])
    
    # Length boundaries
    if len(full_content) < min_chars:
        return False, f"TOO_SHORT (length={len(full_content)} < {min_chars})"
    if len(full_content) > max_chars:
        return False, f"TOO_LONG (length={len(full_content)} > {max_chars})"

    # Repetition check
    if check_repetitive_noise(full_content):
        return False, "DEGENERATE_REPETITION"

    # Secret check
    secret_found = check_secrets(full_content)
    if secret_found:
        return False, f"SECRET_EXPOSURE ({secret_found})"

    # Malicious payload check
    malicious_found = check_malicious_payload(full_content)
    if malicious_found:
        return False, f"DESTRUCTIVE_COMMAND_DETECTED ({malicious_found})"

    return True, "PASSED"

def filter_corpus(
    input_file: str,
    output_file: str,
    rejections_file: Optional[str] = None,
    min_chars: int = 25,
    max_chars: int = 64000,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Process corpus through quality filters, logging rejection causes."""
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    if rejections_file:
        os.makedirs(os.path.dirname(os.path.abspath(rejections_file)), exist_ok=True)

    stats = {
        "total_evaluated": 0,
        "passed": 0,
        "rejected": 0,
        "reasons": {}
    }

    if dry_run:
        logger.info(f"DRY-RUN: Simulating quality filter on {input_file}")
        for r in stream_jsonl(input_file, max_records=200):
            stats["total_evaluated"] += 1
            passed, reason = inspect_record_quality(r, min_chars, max_chars)
            if passed:
                stats["passed"] += 1
            else:
                stats["rejected"] += 1
                stats["reasons"][reason] = stats["reasons"].get(reason, 0) + 1
        return {"dry_run": True, "stats": stats}

    rej_f = open(rejections_file, "w", encoding="utf-8") if rejections_file else None
    
    try:
        with open(output_file, "w", encoding="utf-8") as out_f:
            for r in stream_jsonl(input_file):
                stats["total_evaluated"] += 1
                passed, reason = inspect_record_quality(r, min_chars, max_chars)
                if passed:
                    stats["passed"] += 1
                    r["quality_status"] = "verified"
                    out_f.write(json.dumps(r, ensure_ascii=False) + "\n")
                else:
                    stats["rejected"] += 1
                    stats["reasons"][reason] = stats["reasons"].get(reason, 0) + 1
                    if rej_f:
                        rej_record = {"id": r.get("id"), "reason": reason, "record_snippet": str(r)[:160]}
                        rej_f.write(json.dumps(rej_record, ensure_ascii=False) + "\n")
    finally:
        if rej_f:
            rej_f.close()

    pass_rate = (stats["passed"] / max(1, stats["total_evaluated"])) * 100
    logger.info(f"Quality filter passed {stats['passed']}/{stats['total_evaluated']} records ({pass_rate:.1f}%)")
    return {
        "input_file": input_file,
        "output_file": output_file,
        "stats": stats,
        "pass_rate_pct": round(pass_rate, 2)
    }

def main():
    parser = argparse.ArgumentParser(description="AetherCoder Corpus Quality Filter")
    parser.add_argument("--input", type=str, required=True, help="Input JSONL file")
    parser.add_argument("--output", type=str, required=True, help="Output filtered JSONL file")
    parser.add_argument("--rejections", type=str, default="data/catalogue/quarantined_records.jsonl", help="Path to log rejections")
    parser.add_argument("--min-chars", type=int, default=25, help="Minimum record character count")
    parser.add_argument("--max-chars", type=int, default=64000, help="Maximum record character count")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing files")
    args = parser.parse_args()

    res = filter_corpus(
        args.input,
        args.output,
        rejections_file=args.rejections,
        min_chars=args.min_chars,
        max_chars=args.max_chars,
        dry_run=args.dry_run
    )
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
