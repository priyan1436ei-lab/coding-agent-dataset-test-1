"""Automated unit tests for streaming deduplication."""
import pytest
from src.data_factory.deduplicate import Deduplicator, normalize_code_for_hashing

def test_normalize_code_for_hashing():
    c1 = "def foo():\n    # A comment\n    x = 1\n    return x\n"
    c2 = "def foo():\n    x = 1\n    return x\n"
    assert normalize_code_for_hashing(c1) == normalize_code_for_hashing(c2)

def test_exact_deduplication():
    dedup = Deduplicator()
    rec1 = {
        "id": "1",
        "messages": [
            {"role": "user", "content": "Write hello world in python"},
            {"role": "assistant", "content": "print('hello world')"}
        ]
    }
    rec2 = {
        "id": "2",
        "messages": [
            {"role": "user", "content": "Write hello world in python"},
            {"role": "assistant", "content": "print('hello world')"}
        ]
    }
    is_dup1, _ = dedup.is_duplicate(rec1)
    is_dup2, reason2 = dedup.is_duplicate(rec2)

    assert is_dup1 is False
    assert is_dup2 is True
    assert "EXACT_DUPLICATE" in reason2
