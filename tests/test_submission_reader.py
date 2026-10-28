"""
Unit tests for src/submission_reader.py
"""

import os
import pytest
from src.submission_reader import (
    process_uploaded_submission,
    parse_github_url
)

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data")


def test_process_zip_submission():
    zip_path = os.path.join(SAMPLE_DIR, "candidate_submission_v1_partial.zip")
    result = process_uploaded_submission(zip_path, "candidate_submission_v1_partial.zip")
    assert result["success"] is True
    assert result["total_files"] >= 2
    assert "app.py" in result["raw_content"]
    assert "models.py" in result["raw_content"]


def test_process_single_code_file(tmp_path):
    py_file = tmp_path / "solution.py"
    py_file.write_text("def solve(): return 42", encoding="utf-8")
    result = process_uploaded_submission(str(py_file), "solution.py")
    assert result["success"] is True
    assert result["total_files"] == 1
    assert "def solve(): return 42" in result["raw_content"]


def test_parse_github_urls():
    valid_urls = [
        ("https://github.com/torvalds/linux", ("torvalds", "linux")),
        ("https://github.com/facebook/react.git", ("facebook", "react")),
        ("http://github.com/pallets/flask/", ("pallets", "flask")),
        ("github.com/psf/requests", ("psf", "requests"))
    ]
    for url, (owner, repo) in valid_urls:
        parsed = parse_github_url(url)
        assert parsed is not None
        assert parsed["owner"] == owner
        assert parsed["repo"] == repo

    invalid_urls = [
        "https://gitlab.com/user/project",
        "https://google.com",
        "invalid_string"
    ]
    for url in invalid_urls:
        assert parse_github_url(url) is None


def test_corrupted_zip_file(tmp_path):
    bad_zip = tmp_path / "corrupt.zip"
    bad_zip.write_bytes(b"not a real zip content")
    result = process_uploaded_submission(str(bad_zip), "corrupt.zip")
    assert result["success"] is False
    assert "invalid or corrupted" in result["error"].lower()
