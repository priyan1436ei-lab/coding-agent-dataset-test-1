"""Streaming deduplication engine for exact and near-duplicate code elimination."""
import argparse
import hashlib
import json
import logging
import os
import re
import sys
from typing import Dict, Any, Set, Iterator, Optional, Tuple, List

from src.data_factory.stream_reader import stream_jsonl

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("deduplicate")

def normalize_code_for_hashing(text: str) -> str:
    """Normalize code to detect exact and near duplicates across trivial formatting differences."""
    # Strip comments (Python #, C/JS // and /* */)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"#.*", "", text)
    # Normalize whitespace & lower-case
    lines = [re.sub(r"\s+", " ", line.strip()) for line in text.splitlines()]
    lines = [l for l in lines if l]
    return "\n".join(lines).lower()

def compute_simhash_features(text: str, n: int = 3) -> Set[str]:
    """Compute character n-grams for near-duplicate Jaccard similarity estimation."""
    normalized = normalize_code_for_hashing(text)
    if len(normalized) < n:
        return {normalized}
    return {normalized[i:i+n] for i in range(len(normalized) - n + 1)}

def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Compute Jaccard index between two n-gram sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

def compute_minhash_signature(features: Set[str], num_hashes: int = 16) -> List[int]:
    """Compute MinHash signature of 16 values using independent hash seeds."""
    if not features:
        return [0] * num_hashes
    
    # Pre-hashed features to integers
    hashed_vals = [int(hashlib.md5(f.encode("utf-8")).hexdigest()[:8], 16) for f in features]
    
    # 16 fixed hash coefficients (a, b) mod prime (2^31 - 1)
    prime = 2147483647
    sig = []
    for i in range(num_hashes):
        a = (i * 2654435761 + 1013904223) & 0xFFFFFFFF
        b = (i * 1103515245 + 12345) & 0xFFFFFFFF
        min_h = min((a * h + b) % prime for h in hashed_vals)
        sig.append(min_h)
    return sig

class Deduplicator:
    def __init__(self, near_dup_threshold: float = 0.88, max_cache: int = 25000):
        self.seen_exact_hashes: Set[str] = set()
        self.near_dup_threshold = near_dup_threshold
        self.num_bands = 4
        self.rows_per_band = 4
        self.num_hashes = self.num_bands * self.rows_per_band
        # LSH buckets: (band_index, bucket_hash) -> list of record_ids
        self.lsh_buckets: Dict[Tuple[int, int], List[str]] = {}
        self.id_to_features: Dict[str, Set[str]] = {}
        self.max_cache = max_cache
        self.stats = {
            "total_records": 0,
            "exact_duplicates": 0,
            "near_duplicates": 0,
            "retained_records": 0
        }

    def is_duplicate(self, record: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if record is an exact or near duplicate using stable hash + MinHash LSH."""
        messages = record.get("messages", [])
        content = " ".join([m.get("content", "") for m in messages if m.get("role") in ("user", "assistant")])
        if not content.strip():
            return True, "EMPTY_CONTENT"

        # 1. Exact hash check
        norm_text = normalize_code_for_hashing(content)
        stable_hash = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()
        
        if stable_hash in self.seen_exact_hashes:
            self.stats["exact_duplicates"] += 1
            return True, "EXACT_DUPLICATE"

        # 2. MinHash LSH candidate check
        features = compute_simhash_features(content, n=4)
        sig = compute_minhash_signature(features, num_hashes=self.num_hashes)
        
        rec_id = record.get("id", f"rec_{self.stats['total_records']}")
        candidate_ids = set()

        for band_idx in range(self.num_bands):
            start = band_idx * self.rows_per_band
            band_tuple = tuple(sig[start:start + self.rows_per_band])
            bucket_hash = hash(band_tuple)
            key = (band_idx, bucket_hash)
            
            if key in self.lsh_buckets:
                for cand_id in self.lsh_buckets[key]:
                    candidate_ids.add(cand_id)

        # Evaluate candidate near-duplicates with exact Jaccard similarity
        for cand_id in candidate_ids:
            cand_features = self.id_to_features.get(cand_id)
            if cand_features is not None:
                sim = jaccard_similarity(features, cand_features)
                if sim >= self.near_dup_threshold:
                    self.stats["near_duplicates"] += 1
                    return True, f"NEAR_DUPLICATE (sim={sim:.2f} with {cand_id})"

        # Retain and index
        self.seen_exact_hashes.add(stable_hash)
        self.id_to_features[rec_id] = features
        
        for band_idx in range(self.num_bands):
            start = band_idx * self.rows_per_band
            band_tuple = tuple(sig[start:start + self.rows_per_band])
            bucket_hash = hash(band_tuple)
            key = (band_idx, bucket_hash)
            self.lsh_buckets.setdefault(key, []).append(rec_id)

        self.stats["retained_records"] += 1
        return False, "UNIQUE"

    def process_file(
        self,
        input_file: str,
        output_file: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Stream JSONL through deduplicator and write clean stream."""
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        if dry_run:
            logger.info(f"DRY-RUN: Deduplicating {input_file} (simulated)")
            for record in stream_jsonl(input_file, max_records=200):
                self.stats["total_records"] += 1
                self.is_duplicate(record)
            return {"dry_run": True, "stats": self.stats}

        with open(output_file, "w", encoding="utf-8") as out_f:
            for record in stream_jsonl(input_file):
                self.stats["total_records"] += 1
                is_dup, reason = self.is_duplicate(record)
                if not is_dup:
                    out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

        retention_pct = (self.stats["retained_records"] / max(1, self.stats["total_records"])) * 100
        logger.info(
            f"Deduplication completed: {self.stats['retained_records']}/{self.stats['total_records']} retained "
            f"({retention_pct:.1f}%). Exact dups: {self.stats['exact_duplicates']}, Near dups: {self.stats['near_duplicates']}"
        )
        return {
            "input_file": input_file,
            "output_file": output_file,
            "stats": self.stats,
            "retention_rate_pct": round(retention_pct, 2)
        }

def main():
    parser = argparse.ArgumentParser(description="AetherCoder Streaming Deduplicator")
    parser.add_argument("--input", type=str, required=True, help="Input normalized JSONL")
    parser.add_argument("--output", type=str, required=True, help="Output deduplicated JSONL")
    parser.add_argument("--threshold", type=float, default=0.88, help="Near-duplicate Jaccard threshold (0.0 - 1.0)")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without outputting file")
    args = parser.parse_args()

    dedup = Deduplicator(near_dup_threshold=args.threshold)
    res = dedup.process_file(args.input, args.output, dry_run=args.dry_run)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
