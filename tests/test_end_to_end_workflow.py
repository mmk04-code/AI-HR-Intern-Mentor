"""
End-to-End integration test covering the complete Module 1 review & revision loop.
"""

import os
import pytest
from src.database import init_db, get_submissions_for_task, get_reviews_for_task, get_schedule_for_review, get_email_logs
from src.review_service import (
    register_candidate_and_task,
    process_submission_and_evaluate,
    schedule_and_notify
)

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data")


@pytest.fixture
def workflow_db(tmp_path):
    db_file = tmp_path / "workflow_test.db"
    db_path = str(db_file)
    init_db(db_path)
    return db_path


def test_full_review_and_revision_cycle(workflow_db):
    req_file = os.path.join(SAMPLE_DIR, "company_requirements.md")
    assert os.path.exists(req_file)

    # Step 1: Register Candidate and Task
    reg_res = register_candidate_and_task(
        name="Vikram Seth",
        email="vikram@example.com",
        role="Backend Engineering Intern",
        batch="Batch-2026-Fall",
        module_name="Module 1",
        title="Full-Stack Task Tracker Core",
        description="Build task models, endpoints, validation, and dashboard.",
        requirements_file_source=req_file,
        requirements_filename="company_requirements.md",
        db_path=workflow_db
    )
    assert reg_res["success"] is True
    task_id = reg_res["task_id"]

    # Step 2: Candidate Submits Revision 1 (Partial work)
    zip_v1 = os.path.join(SAMPLE_DIR, "candidate_submission_v1_partial.zip")
    with open(zip_v1, "rb") as f:
        v1_bytes = f.read()

    sub1_res = process_submission_and_evaluate(
        task_id=task_id,
        submission_type="upload",
        file_source=v1_bytes,
        filename="candidate_submission_v1_partial.zip",
        candidate_notes="Submitted models and basic routes.",
        known_issues="Validation rules and unit tests are pending.",
        language="English",
        db_path=workflow_db
    )
    assert sub1_res["success"] is True
    review1_id = sub1_res["review_id"]
    eval1 = sub1_res["review_result"]
    assert eval1["overall_status"] in ["Needs Changes", "Incomplete"]

    # Step 3: Reviewer schedules next review and sends simulated email
    sched_res = schedule_and_notify(
        review_id=review1_id,
        review_date="2026-11-02",
        review_time="11:00",
        session_link="http://localhost:8501 (Local Demo Session)",
        reviewer_message="Please implement the validation rules and unit tests before our call.",
        send_real_email=False,
        db_path=workflow_db
    )
    assert sched_res["success"] is True
    assert sched_res["email_status"] == "SIMULATED — NOT SENT"

    # Step 4: Candidate Submits Revision 2 (Completed work)
    zip_v2 = os.path.join(SAMPLE_DIR, "candidate_submission_v2_completed.zip")
    with open(zip_v2, "rb") as f:
        v2_bytes = f.read()

    sub2_res = process_submission_and_evaluate(
        task_id=task_id,
        submission_type="upload",
        file_source=v2_bytes,
        filename="candidate_submission_v2_completed.zip",
        candidate_notes="Added all validations, filters, error handling, and unit tests.",
        known_issues="None known.",
        language="English",
        db_path=workflow_db
    )
    assert sub2_res["success"] is True
    review2_id = sub2_res["review_id"]
    eval2 = sub2_res["review_result"]

    # In Revision 2, score and status should improve significantly
    assert eval2["overall_score"] >= eval1["overall_score"]

    # Step 5: Verify Revision History and Audit Trail
    submissions = get_submissions_for_task(task_id, db_path=workflow_db)
    assert len(submissions) == 2
    assert submissions[0]["revision_number"] == 2
    assert submissions[1]["revision_number"] == 1

    reviews = get_reviews_for_task(task_id, db_path=workflow_db)
    assert len(reviews) == 2

    email_records = get_email_logs(review_id=review1_id, db_path=workflow_db)
    assert len(email_records) == 1
    assert email_records[0]["status"] == "SIMULATED — NOT SENT"
