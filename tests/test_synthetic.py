"""Automated unit tests for synthetic data generation."""
import pytest
from src.synthetic.generator import build_synthetic_corpus
from src.synthetic.templates import ALGORITHM_TEMPLATES
from src.synthetic.tamil_code_synth import TAMIL_ENGLISH_TEMPLATES

def test_template_coverage():
    assert len(ALGORITHM_TEMPLATES) >= 5
    languages = set(t["language"] for t in ALGORITHM_TEMPLATES)
    assert "python" in languages
    assert "rust" in languages
    assert "java" in languages
    assert "typescript" in languages

def test_tamil_templates():
    assert len(TAMIL_ENGLISH_TEMPLATES) >= 3
    for t in TAMIL_ENGLISH_TEMPLATES:
        assert t["task_type"] == "bilingual_explanation"
        assert len(t["prompt"]) > 10

def test_synthetic_generation_execution(tmp_path):
    out_file = str(tmp_path / "test_synth.jsonl")
    res = build_synthetic_corpus(output_path=out_file, include_tamil=True)
    assert res["total_generated"] >= 10
    assert "python" in res["languages"]
