"""Unit tests for A-to-Z language classifier, FIM transformation, and repository packing."""
import pytest
from src.data_factory.language_classifier import LanguageClassifier
from src.data_factory.fim import transform_to_fim, FIM_PREFIX, FIM_SUFFIX, FIM_MIDDLE
from src.data_factory.repo_packer import pack_repository, generate_file_tree
from src.data_factory.quality_scorer import CodeQualityScorer

def test_language_classifier_extensions():
    clf = LanguageClassifier()
    assert clf.classify_by_extension("main.adb") == "Ada"
    assert clf.classify_by_extension("boot.asm") == "Assembly"
    assert clf.classify_by_extension("script.sh") == "Bash"
    assert clf.classify_by_extension("kernel.c") == "C"
    assert clf.classify_by_extension("engine.cpp") == "C++"
    assert clf.classify_by_extension("Program.cs") == "C#"
    assert clf.classify_by_extension("core.clj") == "Clojure"
    assert clf.classify_by_extension("system.go") == "Go"
    assert clf.classify_by_extension("main.rs") == "Rust"
    assert clf.classify_by_extension("query.sql") == "SQL"
    assert clf.classify_by_extension("module.zig") == "Zig"
    assert clf.classify_by_extension("hardware.v") == "Verilog"

def test_language_classifier_content():
    clf = LanguageClassifier()
    assert clf.classify_content("fn main() { println!(\"Hello\"); }") == "Rust"
    assert clf.classify_content("package main\nfunc main() {}") == "Go"
    assert clf.classify_content("SELECT id FROM users WHERE active = 1") == "SQL"
    assert clf.classify_content("procedure Hello is begin null; end Hello;") == "Ada"

def test_fim_transformation():
    code = """def calculate_area(radius):
    pi = 3.14159
    return pi * (radius ** 2)
"""
    transformed, applied = transform_to_fim(code, fim_rate=1.0, seed=42)
    assert applied is True
    assert FIM_PREFIX in transformed
    assert FIM_SUFFIX in transformed
    assert FIM_MIDDLE in transformed

def test_quality_scorer():
    scorer = CodeQualityScorer()
    
    clean_code = """def add_numbers(a: int, b: int) -> int:
    # Adds two integers
    return a + b
"""
    score, metrics = scorer.score_code(clean_code)
    assert score >= 0.7
    assert metrics["passed"] is True

    minified_code = "var a=1;var b=2;" + "x" * 2000 + ";console.log(a+b);"
    bad_score, bad_metrics = scorer.score_code(minified_code)
    assert bad_metrics["passed"] is False

def test_repo_packer(tmp_path):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    (repo_dir / "requirements.txt").write_text("torch>=2.0.0\n", encoding="utf-8")
    src_dir = repo_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('hello')\n", encoding="utf-8")

    res = pack_repository(str(repo_dir))
    assert res["repo_name"] == "sample_repo"
    assert "requirements.txt" in res["manifests"]
    assert "<repo_context>" in res["formatted_context"]
    assert "<file_sep path=\"requirements.txt\">" in res["formatted_context"]
