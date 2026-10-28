"""
Unit tests for src/mentor_chat.py and spreadsheet parsing.
"""

import os
import pytest
from src.document_parser import parse_spreadsheet
from src.mentor_chat import (
    explain_task_conversationally,
    answer_intern_question,
    process_hr_instruction,
    generate_tts_audio
)

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data")


def test_parse_spreadsheet_xlsx():
    xlsx_path = os.path.join(SAMPLE_DIR, "interns_roster.xlsx")
    assert os.path.exists(xlsx_path)
    res = parse_spreadsheet(xlsx_path, "interns_roster.xlsx")
    assert res["success"] is True
    assert res["count"] == 3
    assert res["records"][0]["name"] == "Aarav Sharma"
    assert "aarav.sharma@example.com" in res["records"][0]["email"]


def test_parse_spreadsheet_csv():
    csv_path = os.path.join(SAMPLE_DIR, "interns_roster.csv")
    assert os.path.exists(csv_path)
    res = parse_spreadsheet(csv_path, "interns_roster.csv")
    assert res["success"] is True
    assert res["count"] == 3
    assert res["records"][1]["name"] == "Priya Patel"


def test_explain_task_multilingual():
    task = {
        "title": "Full-Stack Task Tracker",
        "requirements_text": "Must create models for User, Project, TaskItem. Implement title validation."
    }
    for lang in ["English", "Tamil", "Hindi"]:
        exp, tts = explain_task_conversationally(task, language=lang)
        assert len(exp) > 20
        assert len(tts) > 10


def test_answer_intern_question():
    task = {
        "title": "Full-Stack Task Tracker",
        "requirements_text": "Must validate title at least 5 characters."
    }
    ans, tts = answer_intern_question("How do I validate the title?", task, [], language="English")
    assert "validation" in ans.lower() or "title" in ans.lower()


def test_generate_tts_audio():
    audio = generate_tts_audio("Hello intern, here is your assignment feedback.", "English")
    assert audio is not None
    assert len(audio) > 1000


def test_process_hr_instruction():
    xlsx_path = os.path.join(SAMPLE_DIR, "interns_roster.xlsx")
    req_path = os.path.join(SAMPLE_DIR, "company_requirements.md")

    with open(xlsx_path, "rb") as f:
        x_bytes = f.read()
    with open(req_path, "rb") as f:
        r_bytes = f.read()

    res = process_hr_instruction(
        prompt="Import these interns and assign task Full-Stack Task Tracker Module 1. Deadline is Friday.",
        attached_file_bytes=x_bytes,
        attached_filename="interns_roster.xlsx",
        secondary_file_bytes=r_bytes,
        secondary_filename="company_requirements.md"
    )

    assert res["has_assignment_intent"] is True
    assert len(res["interns"]) == 3
    assert "Friday" in res["deadline"]
    assert "Task Tracker" in res["task_title"]
    assert len(res["requirements_text"]) > 100
