"""Automated unit tests for code syntax and sandbox execution."""
import pytest
from src.data_factory.validate_code import validate_python_syntax, validate_balanced_brackets, run_sandboxed_python_test

def test_validate_python_syntax():
    valid_code = "def add(a, b):\n    return a + b\n"
    is_valid, err = validate_python_syntax(valid_code)
    assert is_valid is True
    assert err is None

    broken_code = "def add(a, b\n    return a + b\n"
    is_valid, err = validate_python_syntax(broken_code)
    assert is_valid is False
    assert "SyntaxError" in err

def test_validate_balanced_brackets():
    balanced = "function test() { if (true) { return [1, 2, 3]; } }"
    is_valid, err = validate_balanced_brackets(balanced)
    assert is_valid is True

    unbalanced = "function test() { if (true) { return [1, 2, 3]; }"
    is_valid, err = validate_balanced_brackets(unbalanced)
    assert is_valid is False
    assert "Unclosed delimiters" in err

def test_sandboxed_python_test():
    code = "def square(x):\n    return x * x\n"
    test_code = "assert square(4) == 16\nassert square(0) == 0\n"
    passed, msg = run_sandboxed_python_test(code, test_code)
    assert passed is True
    assert msg == "PASSED"

def test_sandboxed_python_test_catches_unsafe():
    code = "import os\nos.system('dir')\n"
    test_code = "assert True\n"
    passed, msg = run_sandboxed_python_test(code, test_code)
    assert passed is False
    assert "BLOCKED_UNSAFE_OPERATION" in msg
