"""Automated unit tests for record normalization."""
import pytest
from src.data_factory.normalize import normalize_single_record, detect_code_language, infer_task_type

def test_detect_code_language():
    assert detect_code_language("def foo():\n    return 42") == "python"
    assert detect_code_language("public static void main(String[] args)") == "java"
    assert detect_code_language("const x = () => { console.log('hi'); }") == "javascript"
    assert detect_code_language("SELECT id, name FROM users WHERE active = 1") == "sql"
    assert detect_code_language("fn main() {\n    println!(\"Hello\");\n}") == "rust"

def test_infer_task_type():
    assert infer_task_type("Please fix the IndexError in this function") == "debugging_repair"
    assert infer_task_type("Write pytest test cases for this code") == "unit_test_generation"
    assert infer_task_type("Review this PR for security leaks") == "code_review"
    assert infer_task_type("பைத்தானில் இரும தேடல் விளக்கம்") == "bilingual_explanation"

def test_normalize_mbpp_schema():
    raw_mbpp = {
        "task_id": 42,
        "text": "Write a function to add two numbers.",
        "code": "def add(a, b): return a + b",
        "test_list": ["assert add(2, 3) == 5"]
    }
    norm = normalize_single_record(raw_mbpp, "google-research-datasets/mbpp", "CC-BY-4.0")
    assert norm is not None
    assert norm["id"] == "mbpp_42"
    assert len(norm["messages"]) == 3
    assert norm["messages"][1]["role"] == "user"
    assert norm["messages"][2]["role"] == "assistant"
    assert "add(a, b)" in norm["messages"][2]["content"]
