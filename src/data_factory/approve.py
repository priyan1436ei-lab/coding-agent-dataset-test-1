"""Enforce an explicit allow-list and licence audit before downloading or ingestion."""
import argparse
import json
import logging
import os
import sys
from typing import Dict, Any, Tuple, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("approve")

APPROVED_ROLES = {"training", "training_seed", "synthetic_enhancement"}
PERMITTED_LICENSES = {"apache-2.0", "mit", "cc-by-4.0", "bsd-2-clause", "bsd-3-clause", "cc0-1.0"}
QUARANTINED_BENCHMARKS = {"openai/openai_humaneval", "princeton-nlp/SWE-bench_Lite", "princeton-nlp/SWE-bench"}

def load_catalogue(catalogue_path: str = "data/catalogue/datasets.json") -> Dict[str, Any]:
    if not os.path.exists(catalogue_path):
        raise FileNotFoundError(f"Catalogue file not found at: {catalogue_path}")
    with open(catalogue_path, "r", encoding="utf-8") as f:
        return json.load(f)

def verify_approval(dataset_id: str, catalogue_path: str = "data/catalogue/datasets.json") -> Tuple[bool, str]:
    """Verify if a dataset is approved for training ingestion.
    Returns (is_approved, reason).
    """
    if dataset_id in QUARANTINED_BENCHMARKS:
        return False, f"REJECTED: {dataset_id} is a quarantined benchmark reserved strictly for evaluation."

    catalogue = load_catalogue(catalogue_path)
    sources = {s["id"]: s for s in catalogue.get("sources", [])}

    if dataset_id not in sources:
        return False, f"REJECTED: {dataset_id} is not registered in data/catalogue/datasets.json."

    entry = sources[dataset_id]
    
    if entry.get("approval_status") != "APPROVED":
        return False, f"REJECTED: Dataset {dataset_id} has approval status '{entry.get('approval_status')}' (not APPROVED)."

    if entry.get("use_role") not in APPROVED_ROLES:
        return False, f"REJECTED: Dataset {dataset_id} has role '{entry.get('use_role')}' which is not in {APPROVED_ROLES}."

    license_name = entry.get("license", "").lower()
    if license_name not in PERMITTED_LICENSES:
        return False, f"REJECTED: License '{license_name}' is not in approved permissive licenses {PERMITTED_LICENSES}."

    return True, f"APPROVED: {dataset_id} (License: {entry.get('license')}, Role: {entry.get('use_role')})"

def audit_entire_catalogue(catalogue_path: str = "data/catalogue/datasets.json") -> Dict[str, Any]:
    """Audit all sources in catalogue and report their approval status."""
    catalogue = load_catalogue(catalogue_path)
    report = {
        "approved": [],
        "quarantined_evaluation": [],
        "rejected": []
    }
    for source in catalogue.get("sources", []):
        s_id = source["id"]
        status, reason = verify_approval(s_id, catalogue_path)
        item = {
            "id": s_id,
            "license": source.get("license"),
            "approval_status": source.get("approval_status"),
            "reason": reason
        }
        if status:
            report["approved"].append(item)
        elif source.get("approval_status") == "HELD_OUT_EVALUATION":
            report["quarantined_evaluation"].append(item)
        else:
            report["rejected"].append(item)
    return report

def main():
    parser = argparse.ArgumentParser(description="AetherCoder Source Approval Auditor")
    parser.add_argument("--check-id", type=str, help="Specific dataset ID to verify")
    parser.add_argument("--audit-all", action="store_true", help="Audit all sources in catalogue")
    parser.add_argument("--catalogue", type=str, default="data/catalogue/datasets.json", help="Path to catalogue file")
    parser.add_argument("--dry-run", action="store_true", help="Perform verification without side effects")
    args = parser.parse_args()

    if args.check_id:
        approved, reason = verify_approval(args.check_id, args.catalogue)
        if approved:
            logger.info(f"VERIFIED: {reason}")
            sys.exit(0)
        else:
            logger.error(f"AUDIT FAILED: {reason}")
            sys.exit(1)
    elif args.audit_all:
        report = audit_entire_catalogue(args.catalogue)
        print(json.dumps(report, indent=2))
        logger.info(f"Approved: {len(report['approved'])}, Quarantined: {len(report['quarantined_evaluation'])}, Rejected: {len(report['rejected'])}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
