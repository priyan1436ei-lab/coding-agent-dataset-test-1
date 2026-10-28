"""Automated unit tests for streaming reader."""
import json
import os
import tempfile
import pytest

from src.data_factory.stream_reader import stream_jsonl, stream_chunks

def test_stream_jsonl_safely_skips_malformed():
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        f.write('{"id": 1, "text": "valid"}\n')
        f.write('NOT_A_VALID_JSON_LINE\n')
        f.write('{"id": 2, "text": "valid_again"}\n')
        path = f.name

    try:
        records = list(stream_jsonl(path))
        assert len(records) == 2
        assert records[0]["id"] == 1
        assert records[1]["id"] == 2
    finally:
        os.remove(path)

def test_stream_chunks():
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for i in range(15):
            f.write(json.dumps({"id": i}) + "\n")
        path = f.name

    try:
        chunks = list(stream_chunks(path, chunk_size=5))
        assert len(chunks) == 3
        assert len(chunks[0]) == 5
        assert len(chunks[1]) == 5
        assert len(chunks[2]) == 5
    finally:
        os.remove(path)
