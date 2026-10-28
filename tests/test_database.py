"""
Unit tests for src/database.py
"""

import os
import pytest
from src.database import (
    init_db,
    create_candidate,
    get_candidates,
    get_candidate,
    create_task,
    get_all_tasks,
    get_task,
    create_submission,
    get_submissions_for_task,
    create_review,
    get_review_for_submission,
    save_review_schedule,
    get_schedule_for_review,
    log_email,
    get_email_logs
)


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_assistant.db"
    db_path = str(db_file)
    init_db(db_path)
    return db_path


def test_candidate_crud(test_db):
    cid = create_candidate("Priya Patel", "priya@example.com", "Backend Intern", "Batch-2026-A", db_path=test_db)
    assert cid > 0

    cand = get_candidate(cid, db_path=test_db)
    assert cand is not None
    assert cand["name"] == "Priya Patel"
    assert cand["email"] == "priya@example.com"

    all_cands = get_candidates(db_path=test_db)
    assert len(all_cands) == 1


def test_task_crud(test_db):
    cid = create_candidate("Karthik Raja", "karthik@example.com", "Full Stack Intern", "Batch-2026-A", db_path=test_db)
    tid = create_task(cid, "Module 1", "Build REST API", "Description text", "Must implement auth and CRUD", "req.md", db_path=test_db)
    assert tid > 0

    task = get_task(tid, db_path=test_db)
    assert task is not None
    assert task["candidate_name"] == "Karthik Raja"
    assert task["title"] == "Build REST API"


def test_submission_revisions(test_db):
    cid = create_candidate("Rohan Verma", "rohan@example.com", "DevOps Intern", "Batch 1", db_path=test_db)
    tid = create_task(cid, "Module 1", "Docker Setup", "Setup containers", "Reqs", "req.txt", db_path=test_db)

    # Revision 1
    sub1_id = create_submission(tid, "upload", candidate_notes="First draft", raw_content="code v1", db_path=test_db)
    # Revision 2
    sub2_id = create_submission(tid, "upload", candidate_notes="Fixed issues", raw_content="code v2", db_path=test_db)

    subs = get_submissions_for_task(tid, db_path=test_db)
    assert len(subs) == 2
    assert subs[0]["revision_number"] == 2  # Most recent first
    assert subs[1]["revision_number"] == 1


def test_review_and_schedule_persistence(test_db):
    cid = create_candidate("Ananya Sen", "ananya@example.com", "ML Intern", "Batch 2", db_path=test_db)
    tid = create_task(cid, "Module 1", "Pipeline", "Desc", "Reqs", "req.txt", db_path=test_db)
    sid = create_submission(tid, "upload", raw_content="code", db_path=test_db)

    rid = create_review(
        submission_id=sid,
        overall_status="Needs Changes",
        overall_score=70,
        is_ai_generated=False,
        model_used="Fallback Rule-Based",
        language="English",
        structured_data={"summary": "Good effort"},
        feedback_summary="Good effort",
        db_path=test_db
    )
    assert rid > 0

    review = get_review_for_submission(sid, db_path=test_db)
    assert review is not None
    assert review["overall_status"] == "Needs Changes"
    assert review["overall_score"] == 70

    # Schedule
    save_review_schedule(rid, "2026-11-01", "14:00", "https://meet.example.com/test", "Bring updated tests", db_path=test_db)
    sched = get_schedule_for_review(rid, db_path=test_db)
    assert sched is not None
    assert sched["review_date"] == "2026-11-01"
    assert sched["review_time"] == "14:00"


def test_email_logs(test_db):
    cid = create_candidate("Dev User", "dev@example.com", "Intern", "Batch 1", db_path=test_db)
    tid = create_task(cid, "Module 1", "Task", "Desc", "Reqs", "req.txt", db_path=test_db)
    sid = create_submission(tid, "upload", raw_content="code", db_path=test_db)
    rid = create_review(sid, "Completed", 95, False, "Fallback", "English", {}, "Summary", db_path=test_db)

    log_id = log_email(
        review_id=rid,
        recipient_email="dev@example.com",
        subject="Task Completed",
        body_text="Great work",
        body_html="<p>Great work</p>",
        mode="SIMULATED",
        status="SIMULATED — NOT SENT",
        error_message=None,
        db_path=test_db
    )
    assert log_id > 0

    logs = get_email_logs(review_id=rid, db_path=test_db)
    assert len(logs) == 1
    assert logs[0]["status"] == "SIMULATED — NOT SENT"
    assert logs[0]["mode"] == "SIMULATED"
