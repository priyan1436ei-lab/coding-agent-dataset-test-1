"""Automated unit tests for benchmark contamination prevention."""
import pytest
from src.data_factory.contamination import ContaminationDetector

def test_contamination_detection_humaneval_signature():
    detector = ContaminationDetector(n_gram_size=10)
    
    contaminated_rec = {
        "id": "leak_01",
        "messages": [
            {"role": "user", "content": "def has_close_elements(numbers: list[float], threshold: float) -> bool:"},
            {"role": "assistant", "content": "for i in range(len(numbers)): ..."}
        ]
    }
    is_cont, reason = detector.is_contaminated(contaminated_rec)
    assert is_cont is True
    assert "HUMANEVAL_SIGNATURE_LEAK" in reason

def test_clean_record_passes_contamination():
    detector = ContaminationDetector(n_gram_size=10)
    
    clean_rec = {
        "id": "clean_01",
        "messages": [
            {"role": "user", "content": "Write an enterprise billing calculator with sales tax in Python."},
            {"role": "assistant", "content": "def calculate_bill(subtotal, tax_rate=0.08):\n    return subtotal * (1 + tax_rate)"}
        ]
    }
    is_cont, reason = detector.is_contaminated(clean_rec)
    assert is_cont is False
    assert reason == "CLEAN"
