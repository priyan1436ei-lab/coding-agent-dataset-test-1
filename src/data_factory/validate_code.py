"""Code syntax and sandbox validation engine. Ensures safety and correctness."""
import argparse
import ast
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from typing import Dict, Any, Tuple, Optional, List

from src.data_factory.stream_reader import stream_jsonl

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("validate_code")

def extract_code_blocks(text: str) -> List[Tuple[str, str]]:
    """Extract (language, code) blocks from markdown fences."""
    pattern = re.compile(r"```([a-zA-Z0-9+#_-]*)\s*\n(.*?)```", re.DOTALL)
    blocks = []
    for match in pattern.finditer(text):
        lang = match.group(1).lower() or "python"
        code = match.group(2).strip()
        blocks.append((lang, code))
    return blocks

def validate_python_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Safe offline AST syntax verification for Python."""
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"ParseError: {e}"

def validate_balanced_brackets(code: str) -> Tuple[bool, Optional[str]]:
    """Check balanced delimiters for C/C++/Java/JS/TS/Rust/Go."""
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}
    in_single_quote = False
    in_double_quote = False
    
    for i, char in enumerate(code):
        if char == '"' and (i == 0 or code[i-1] != '\\'):
            in_double_quote = not in_double_quote
        elif char == "'" and (i == 0 or code[i-1] != '\\'):
            in_single_quote = not in_single_quote
            
        if in_single_quote or in_double_quote:
            continue
            
        if char in '({[':
            stack.append(char)
        elif char in ')}]':
            if not stack or stack[-1] != pairs[char]:
                return False, f"Unbalanced delimiter '{char}' at character index {i}"
            stack.pop()

    if stack:
        return False, f"Unclosed delimiters remaining: {stack}"
    return True, None

def validate_sql_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Heuristic validation of SQL query structure."""
    keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "WITH"]
    first_word = code.strip().split()[0].upper() if code.strip() else ""
    if first_word not in keywords:
        return False, f"SQL does not begin with standard keyword: '{first_word}'"
    return True, None

def validate_snippet(lang: str, code: str) -> Tuple[bool, Optional[str]]:
    """Validate syntax according to language."""
    lang = lang.lower()
    if lang in ["python", "py"]:
        return validate_python_syntax(code)
    elif lang in ["sql"]:
        return validate_sql_syntax(code)
    elif lang in ["c", "cpp", "c++", "java", "javascript", "js", "typescript", "ts", "rust", "go"]:
        return validate_balanced_brackets(code)
    return True, None

def run_sandboxed_python_test(code: str, test_code: str, timeout_sec: float = 2.0) -> Tuple[bool, str]:
    """Execute python code against test assertions in an isolated subprocess with timeout.
    Prevents execution of malicious imports or unbounded loops.
    """
    # Safety pre-check
    forbidden = ["os.system", "subprocess", "shutil.rmtree", "open(", "socket", "urllib", "eval("]
    for fb in forbidden:
        if fb in code or fb in test_code:
            return False, f"BLOCKED_UNSAFE_OPERATION: {fb}"

    import textwrap
    indented_test = textwrap.indent(textwrap.dedent(test_code), "    ")
    combined_script = f"""# Isolated Sandbox Script
import sys
{code}

# Test Cases
try:
{indented_test}
    sys.exit(0)
except AssertionError as e:
    sys.stderr.write(f"AssertionError: {{e}}\\n")
    sys.exit(2)
except Exception as e:
    sys.stderr.write(f"RuntimeError: {{e}}\\n")
    sys.exit(3)
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_f:
        temp_f.write(combined_script)
        temp_path = temp_f.name

    try:
        proc = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )
        if proc.returncode == 0:
            return True, "PASSED"
        return False, f"EXEC_FAIL (Exit code {proc.returncode}): {proc.stderr.strip()[:100]}"
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT_EXPIRED"
    except Exception as e:
        return False, f"ERROR: {str(e)}"
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

def validate_record_code(record: Dict[str, Any], execute_tests: bool = False) -> Dict[str, Any]:
    """Inspect and validate code within canonical record messages."""
    messages = record.get("messages", [])
    asst_text = " ".join([m.get("content", "") for m in messages if m.get("role") == "assistant"])
    blocks = extract_code_blocks(asst_text)
    
    validation_info = {
        "blocks_count": len(blocks),
        "syntax_valid": True,
        "syntax_errors": [],
        "tested": False,
        "test_passed": False
    }

    if not blocks:
        # Check raw content if not in code block
        is_valid, err = validate_snippet(record.get("language", "python"), asst_text)
        if not is_valid:
            validation_info["syntax_valid"] = False
            validation_info["syntax_errors"].append(err)
    else:
        for lang, code in blocks:
            is_valid, err = validate_snippet(lang, code)
            if not is_valid:
                validation_info["syntax_valid"] = False
                validation_info["syntax_errors"].append(f"[{lang}] {err}")

    record["code_validation"] = validation_info
    return record

def main():
    parser = argparse.ArgumentParser(description="AetherCoder Code Validator")
    parser.add_argument("--input", type=str, required=True, help="Input JSONL file")
    parser.add_argument("--output", type=str, required=True, help="Output validated JSONL file")
    parser.add_argument("--dry-run", action="store_true", help="Simulate validation")
    args = parser.parse_args()

    total = 0
    valid_count = 0
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    
    with open(args.output, "w", encoding="utf-8") as out_f:
        for r in stream_jsonl(args.input):
            total += 1
            validated_r = validate_record_code(r)
            if validated_r["code_validation"]["syntax_valid"]:
                valid_count += 1
            if not args.dry_run:
                out_f.write(json.dumps(validated_r, ensure_ascii=False) + "\n")

    logger.info(f"Validation complete: {valid_count}/{total} records have valid code syntax.")

if __name__ == "__main__":
    main()
