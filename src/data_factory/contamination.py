"""Benchmark contamination auditor: Prevents evaluation benchmark leakage into training splits."""
import argparse
import hashlib
import json
import logging
import os
import re
import sys
from typing import Dict, Any, Set, List, Tuple, Optional

from src.data_factory.stream_reader import stream_jsonl

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("contamination")

# Known HumanEval signature keywords and canonical problem phrases
HUMANEVAL_SIGNATURES = [
    "has_close_elements", "separate_paren_groups", "truncate_number", "below_zero",
    "mean_absolute_deviation", "intersperse", "filter_by_substring", "rolling_max",
    "make_palindrome", "string_xor", "longest_element", "greatest_common_divisor",
    "all_prefixes", "string_sequence", "count_distinct_characters", "parse_nested_parens",
    "filter_by_prefix", "how_many_times", "sort_numbers", "find_closest_elements",
    "rescale_to_unit", "filter_integers", "strlen", "largest_divisor", "factorize",
    "remove_duplicates", "flip_case", "concatenate", "filter_by_suffix", "get_positive",
    "is_prime", "fizz_buzz", "monotonic", "sort_third", "unique_elements", "triples_sum_to_zero",
    "car_race_collision", "incr_list", "pairs_sum_to_zero", "change_base", "triangle_area",
    "fib4", "median", "sum_squares", "circular_shift", "search_largest_prime", "encode_cyclic"
]

def extract_canonical_tokens(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric sequence for n-gram comparison."""
    return re.findall(r"[a-z0-9_]+", text.lower())

def generate_ngrams(tokens: List[str], n: int = 10) -> Set[str]:
    """Generate n-grams as space-delimited strings."""
    if len(tokens) < n:
        return set()
    return {" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)}

class ContaminationDetector:
    def __init__(self, n_gram_size: int = 10):
        self.n_gram_size = n_gram_size
        self.benchmark_ngrams: Set[str] = set()
        self.benchmark_signatures: Set[str] = set(s.lower() for s in HUMANEVAL_SIGNATURES)
        self.stats = {
            "audited_records": 0,
            "contaminated_records": 0,
            "passed_records": 0,
            "contamination_details": []
        }

    def register_benchmark_text(self, text: str):
        """Add benchmark reference text to the quarantine n-gram index."""
        tokens = extract_canonical_tokens(text)
        self.benchmark_ngrams.update(generate_ngrams(tokens, self.n_gram_size))

    def is_contaminated(self, record: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if record contains benchmark leakages."""
        messages = record.get("messages", [])
        content = " ".join([m.get("content", "") for m in messages if m.get("role") in ("user", "assistant")])
        tokens = extract_canonical_tokens(content)

        # 1. Exact function signature match in prompt
        user_msgs = " ".join([m.get("content", "") for m in messages if m.get("role") == "user"]).lower()
        for sig in self.benchmark_signatures:
            if re.search(rf"\bdef\s+{sig}\b", user_msgs) or re.search(rf"\bfunction\s+{sig}\b", user_msgs):
                return True, f"HUMANEVAL_SIGNATURE_LEAK ({sig})"

        # 2. Benchmark n-gram overlap
        if self.benchmark_ngrams:
            rec_ngrams = generate_ngrams(tokens, self.n_gram_size)
            intersection = rec_ngrams.intersection(self.benchmark_ngrams)
            if intersection:
                sample_match = next(iter(intersection))
                return True, f"BENCHMARK_NGRAM_MATCH ({sample_match})"

        return False, "CLEAN"

    def audit_file(
        self,
        input_file: str,
        output_clean_file: str,
        quarantine_file: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Audit training candidates against benchmark contamination."""
        os.makedirs(os.path.dirname(os.path.abspath(output_clean_file)), exist_ok=True)
        if quarantine_file:
            os.makedirs(os.path.dirname(os.path.abspath(quarantine_file)), exist_ok=True)

        if dry_run:
            logger.info(f"DRY-RUN: Checking contamination in {input_file}")
            for r in stream_jsonl(input_file, max_records=200):
                self.stats["audited_records"] += 1
                is_cont, reason = self.is_contaminated(r)
                if is_cont:
                    self.stats["contaminated_records"] += 1
                else:
                    self.stats["passed_records"] += 1
            return {"dry_run": True, "stats": self.stats}

        q_f = open(quarantine_file, "w", encoding="utf-8") if quarantine_file else None
        try:
            with open(output_clean_file, "w", encoding="utf-8") as out_f:
                for r in stream_jsonl(input_file):
                    self.stats["audited_records"] += 1
                    is_cont, reason = self.is_contaminated(r)
                    if is_cont:
                        self.stats["contaminated_records"] += 1
                        self.stats["contamination_details"].append({"id": r.get("id"), "reason": reason})
                        if q_f:
                            q_f.write(json.dumps({"id": r.get("id"), "reason": reason, "snippet": str(r)[:140]}, ensure_ascii=False) + "\n")
                    else:
                        self.stats["passed_records"] += 1
                        out_f.write(json.dumps(r, ensure_ascii=False) + "\n")
        finally:
            if q_f:
                q_f.close()

        clean_pct = (self.stats["passed_records"] / max(1, self.stats["audited_records"])) * 100
        logger.info(
            f"Contamination Audit Complete: {self.stats['passed_records']}/{self.stats['audited_records']} clean "
            f"({clean_pct:.1f}%). Quarantined: {self.stats['contaminated_records']}"
        )
        return {
            "input_file": input_file,
            "output_clean_file": output_clean_file,
            "stats": self.stats,
            "clean_pct": round(clean_pct, 2)
        }

def main():
    parser = argparse.ArgumentParser(description="AetherCoder Contamination Auditor")
    parser.add_argument("--input", type=str, required=True, help="Input filtered JSONL")
    parser.add_argument("--output", type=str, required=True, help="Output uncontaminated JSONL")
    parser.add_argument("--quarantine", type=str, default="data/catalogue/contaminated_quarantine.jsonl", help="Quarantine file")
    parser.add_argument("--dry-run", action="store_true", help="Simulate contamination audit")
    args = parser.parse_args()

    detector = ContaminationDetector()
    res = detector.audit_file(args.input, args.output, quarantine_file=args.quarantine, dry_run=args.dry_run)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
