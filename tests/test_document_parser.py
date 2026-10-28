"""
Unit tests for src/document_parser.py
"""

import os
import pytest
from src.document_parser import parse_document

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data")


def test_parse_markdown_file():
    md_path = os.path.join(SAMPLE_DIR, "company_requirements.md")
    result = parse_document(md_path, "company_requirements.md")
    assert result["success"] is True
    assert "Company Task Requirements" in result["text"]
    assert result["char_count"] > 100


def test_parse_txt_file():
    txt_path = os.path.join(SAMPLE_DIR, "company_requirements.txt")
    result = parse_document(txt_path, "company_requirements.txt")
    assert result["success"] is True
    assert "Database Schema & Models" in result["text"]


def test_parse_docx_file():
    docx_path = os.path.join(SAMPLE_DIR, "company_requirements.docx")
    result = parse_document(docx_path, "company_requirements.docx")
    assert result["success"] is True
    assert "Company Task Requirements" in result["text"]


def test_parse_empty_file(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")
    result = parse_document(str(empty_file), "empty.txt")
    assert result["success"] is False
    assert "empty" in result["error"].lower()


def test_parse_unsupported_file(tmp_path):
    bin_file = tmp_path / "sample.xyz123"
    bin_file.write_bytes(b"\x00\x01\x02\x03")
    result = parse_document(str(bin_file), "sample.xyz123")
    assert result["success"] is False
    assert "unsupported" in result["error"].lower()


def test_parse_nonexistent_file():
    result = parse_document("nonexistent_file_path.pdf", "nonexistent_file_path.pdf")
    assert result["success"] is False
    assert "does not exist" in result["error"].lower()
