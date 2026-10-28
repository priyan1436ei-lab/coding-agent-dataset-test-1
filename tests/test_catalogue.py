"""Automated unit tests for dataset catalogue and approval logic."""
import os
import json
import pytest

from src.data_factory.approve import verify_approval, audit_entire_catalogue, load_catalogue

def test_catalogue_structure():
    cat = load_catalogue("data/catalogue/datasets.json")
    assert "sources" in cat
    assert len(cat["sources"]) >= 4

def test_approval_logic():
    # MBPP must be approved
    approved, reason = verify_approval("google-research-datasets/mbpp", "data/catalogue/datasets.json")
    assert approved is True
    assert "APPROVED" in reason

    # HumanEval must be rejected from training (quarantined)
    approved, reason = verify_approval("openai/openai_humaneval", "data/catalogue/datasets.json")
    assert approved is False
    assert "quarantined benchmark" in reason.lower()

    # CodeSearchNet must be rejected
    approved, reason = verify_approval("code-search-net/code_search_net", "data/catalogue/datasets.json")
    assert approved is False

    # Unregistered dataset must be rejected
    approved, reason = verify_approval("some/random-unregistered-dataset", "data/catalogue/datasets.json")
    assert approved is False

def test_audit_entire_catalogue():
    report = audit_entire_catalogue("data/catalogue/datasets.json")
    assert len(report["approved"]) >= 2
    assert len(report["quarantined_evaluation"]) >= 2
    assert len(report["rejected"]) >= 1
