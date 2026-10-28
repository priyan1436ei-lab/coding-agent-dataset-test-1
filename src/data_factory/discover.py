"""Discover candidate datasets from official sources and verify metadata."""
import argparse
import json
import logging
import os
import sys
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("discover")

KNOWN_PERMISSIVE_LICENSES = {"mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "cc-by-4.0", "cc0-1.0"}

def query_hf_dataset_metadata(dataset_id: str, timeout: int = 10) -> Dict[str, Any]:
    """Query Hugging Face API for real dataset metadata."""
    url = f"https://huggingface.co/api/datasets/{dataset_id}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AetherCoder-DataFactory/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                tags = data.get("tags", [])
                
                # Extract license
                license_tags = [t.split("license:")[1] for t in tags if t.startswith("license:")]
                detected_license = license_tags[0] if license_tags else "UNVERIFIED"
                
                # Extract size category
                size_tags = [t.split("size_categories:")[1] for t in tags if t.startswith("size_categories:")]
                detected_size = size_tags[0] if size_tags else "UNVERIFIED"
                
                # Extract languages
                lang_tags = [t.split("language:")[1] for t in tags if t.startswith("language:")]
                
                is_permissive = detected_license.lower() in KNOWN_PERMISSIVE_LICENSES

                return {
                    "dataset_id": dataset_id,
                    "status": "ACCESSIBLE",
                    "official_url": f"https://huggingface.co/datasets/{dataset_id}",
                    "sha": data.get("sha", "UNVERIFIED"),
                    "license": detected_license,
                    "is_permissive_license": is_permissive,
                    "size_category": detected_size,
                    "detected_languages": lang_tags,
                    "description": (data.get("description") or "")[:200],
                    "downloads": data.get("downloads", 0),
                    "likes": data.get("likes", 0)
                }
    except urllib.error.HTTPError as e:
        logger.warning(f"HTTP Error {e.code} for dataset {dataset_id}: {e.reason}")
        return {
            "dataset_id": dataset_id,
            "status": f"HTTP_ERROR_{e.code}",
            "official_url": f"https://huggingface.co/datasets/{dataset_id}",
            "sha": "UNVERIFIED",
            "license": "UNVERIFIED",
            "is_permissive_license": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Error checking dataset {dataset_id}: {e}")
        return {
            "dataset_id": dataset_id,
            "status": "FAILED",
            "official_url": f"https://huggingface.co/datasets/{dataset_id}",
            "sha": "UNVERIFIED",
            "license": "UNVERIFIED",
            "is_permissive_license": False,
            "error": str(e)
        }

def discover_candidates(candidates: List[str], dry_run: bool = False) -> List[Dict[str, Any]]:
    """Discover and audit a list of dataset candidate identifiers."""
    results = []
    for cand in candidates:
        logger.info(f"Discovering metadata for: {cand}")
        if dry_run:
            results.append({
                "dataset_id": cand,
                "status": "DRY_RUN",
                "sha": "dry-run-sha",
                "license": "unverified-dry-run",
                "is_permissive_license": False
            })
        else:
            meta = query_hf_dataset_metadata(cand)
            results.append(meta)
    return results

def main():
    parser = argparse.ArgumentParser(description="AetherCoder Dataset Discovery Engine")
    parser.add_argument("--candidates", nargs="+", default=[
        "google-research-datasets/mbpp",
        "sahil2801/CodeAlpaca-20k",
        "openai/openai_humaneval",
        "princeton-nlp/SWE-bench_Lite",
        "code-search-net/code_search_net"
    ], help="List of dataset IDs to check")
    parser.add_argument("--output", type=str, default="data/catalogue/discovered_candidates.json", help="Path to save output")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making network requests")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    discovered = discover_candidates(args.candidates, dry_run=args.dry_run)
    
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({"discovered": discovered}, f, indent=2)
    
    logger.info(f"Discovered {len(discovered)} sources. Results saved to {args.output}")

if __name__ == "__main__":
    main()
