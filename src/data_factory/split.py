"""Deterministic train/validation/test corpus partitioner."""
import argparse
import hashlib
import json
import logging
import os
import random
import sys
from typing import Dict, Any, List

from src.data_factory.stream_reader import stream_jsonl

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("split")

def deterministic_hash_partition(record_id: str, train_ratio: float = 0.90, val_ratio: float = 0.05) -> str:
    """Assign record to split deterministically based on MD5/SHA256 hash of record ID."""
    h = int(hashlib.sha256(record_id.encode("utf-8")).hexdigest()[:8], 16)
    score = (h % 10000) / 10000.0
    
    if score < train_ratio:
        return "train"
    elif score < (train_ratio + val_ratio):
        return "val"
    else:
        return "test"

def partition_corpus(
    input_file: str,
    output_dir: str = "data/final",
    train_ratio: float = 0.90,
    val_ratio: float = 0.05,
    seed: int = 42,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Split input JSONL into deterministic train, validation, and test splits."""
    os.makedirs(output_dir, exist_ok=True)
    random.seed(seed)

    train_path = os.path.join(output_dir, "train.jsonl")
    val_path = os.path.join(output_dir, "val.jsonl")
    test_path = os.path.join(output_dir, "test.jsonl")

    counts = {"train": 0, "val": 0, "test": 0, "total": 0}
    lang_distribution: Dict[str, Dict[str, int]] = {}
    task_distribution: Dict[str, Dict[str, int]] = {}

    if dry_run:
        logger.info(f"DRY-RUN: Simulating dataset partition on {input_file}")
        for r in stream_jsonl(input_file, max_records=200):
            r_id = r.get("id", str(counts["total"]))
            split = deterministic_hash_partition(r_id, train_ratio, val_ratio)
            counts[split] += 1
            counts["total"] += 1
        return {"dry_run": True, "counts": counts}

    train_f = open(train_path, "w", encoding="utf-8")
    val_f = open(val_path, "w", encoding="utf-8")
    test_f = open(test_path, "w", encoding="utf-8")

    files = {"train": train_f, "val": val_f, "test": test_f}

    try:
        for r in stream_jsonl(input_file):
            counts["total"] += 1
            r_id = r.get("id", f"rec_{counts['total']}")
            split = deterministic_hash_partition(r_id, train_ratio, val_ratio)
            counts[split] += 1
            
            # Record distribution
            lang = r.get("language", "unknown")
            task = r.get("task_type", "unknown")
            lang_distribution.setdefault(lang, {"train": 0, "val": 0, "test": 0})[split] += 1
            task_distribution.setdefault(task, {"train": 0, "val": 0, "test": 0})[split] += 1

            files[split].write(json.dumps(r, ensure_ascii=False) + "\n")
    finally:
        train_f.close()
        val_f.close()
        test_f.close()

    manifest = {
        "input_file": input_file,
        "counts": counts,
        "splits": {
            "train": train_path,
            "val": val_path,
            "test": test_path
        },
        "language_breakdown": lang_distribution,
        "task_breakdown": task_distribution
    }
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2)

    logger.info(
        f"Partition complete: Train={counts['train']}, Val={counts['val']}, Test={counts['test']} -> {output_dir}"
    )
    return manifest

def main():
    parser = argparse.ArgumentParser(description="AetherCoder Corpus Partitioner")
    parser.add_argument("--input", type=str, required=True, help="Input validated JSONL file")
    parser.add_argument("--output-dir", type=str, default="data/final", help="Destination directory for splits")
    parser.add_argument("--train-ratio", type=float, default=0.90, help="Fraction for training")
    parser.add_argument("--val-ratio", type=float, default=0.05, help="Fraction for validation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for determinism")
    parser.add_argument("--dry-run", action="store_true", help="Simulate partition without writing")
    args = parser.parse_args()

    res = partition_corpus(
        args.input,
        output_dir=args.output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        seed=args.seed,
        dry_run=args.dry_run
    )
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
