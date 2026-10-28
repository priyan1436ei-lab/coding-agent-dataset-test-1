"""Automated unit tests for quality, safety, and secret filtering."""
import pytest
from src.data_factory.filter_quality import inspect_record_quality, check_secrets, check_malicious_payload

def test_secret_detection():
    assert check_secrets("AKIAIOSFODNN7EXAMPLE") == "AWS_ACCESS_KEY"
    assert check_secrets("export GITHUB_TOKEN=ghp_123456789012345678901234567890123456") == "GITHUB_PAT"
    assert check_secrets("-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...") == "PRIVATE_KEY"
    assert check_secrets("print('no secrets here')") is None

def test_malicious_command_detection():
    assert check_malicious_payload("run rm -rf / in terminal") == "DANGEROUS_RM_ROOT"
    assert check_malicious_payload("system format C:") == "DANGEROUS_FORMAT_DISK"
    assert check_malicious_payload("ls -la") is None

def test_inspect_record_quality():
    valid_rec = {
        "id": "valid_01",
        "messages": [
            {"role": "user", "content": "How do I calculate factorial in Python?"},
            {"role": "assistant", "content": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n - 1)"}
        ]
    }
    passed, reason = inspect_record_quality(valid_rec)
    assert passed is True
    assert reason == "PASSED"

    secret_rec = {
        "id": "bad_01",
        "messages": [
            {"role": "user", "content": "Here is my AWS key: AKIAIOSFODNN7EXAMPLE"},
            {"role": "assistant", "content": "Do not hardcode keys!"}
        ]
    }
    passed, reason = inspect_record_quality(secret_rec)
    assert passed is False
    assert "SECRET_EXPOSURE" in reason
