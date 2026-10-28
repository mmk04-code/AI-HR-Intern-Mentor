"""
Unit tests for src/email_service.py
"""

import pytest
from src.database import init_db, create_candidate, create_task, create_submission, create_review
from src.email_service import generate_feedback_email_content, send_or_simulate_email


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "email_test.db"
    db_path = str(db_file)
    init_db(db_path)
    return db_path


def test_email_content_generation():
    subject, body_text, body_html = generate_feedback_email_content(
        candidate_name="Meera Nair",
        module_name="Module 1",
        task_title="API Development",
        review_status="Needs Changes",
        review_score=68,
        strengths=["Modular structure", "Clear routes"],
        missing_items=["Input validation", "Unit tests"],
        actionable_corrections=["Add length check on title", "Add pytest suite"],
        review_date="2026-11-05",
        review_time="15:30",
        session_link="https://meet.example.com/rev-101",
        reviewer_message="Focus on test coverage."
    )

    assert "Meera Nair" in subject or "Module 1" in subject
    assert "Needs Changes" in subject
    assert "68 / 100" in body_text
    assert "2026-11-05 at 15:30" in body_text
    assert "https://meet.example.com/rev-101" in body_text
    assert "Focus on test coverage." in body_text
    assert "<html>" in body_html.lower()


def test_simulated_email_dispatch_never_claims_sent(test_db):
    cid = create_candidate("Meera Nair", "meera@example.com", "Intern", "Batch 1", db_path=test_db)
    tid = create_task(cid, "Module 1", "API Dev", "Desc", "Reqs", "req.txt", db_path=test_db)
    sid = create_submission(tid, "upload", raw_content="code", db_path=test_db)
    rid = create_review(sid, "Needs Changes", 68, False, "Fallback", "English", {}, "Summary", db_path=test_db)

    result = send_or_simulate_email(
        review_id=rid,
        recipient_email="meera@example.com",
        subject="Feedback Review",
        body_text="Body content",
        body_html="<p>Body content</p>",
        force_simulation=True,
        db_path=test_db
    )

    assert result["success"] is True
    assert result["mode"] == "SIMULATED"
    assert result["status"] == "SIMULATED — NOT SENT"
    assert "SENT" != result["status"]
