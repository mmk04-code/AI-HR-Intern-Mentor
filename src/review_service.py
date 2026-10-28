"""
Review service module for Internship Task Review Assistant.
Orchestrates task creation, candidate submissions (revisions), AI/rule-based reviews,
scheduling, and feedback notification dispatch.
"""

from typing import Dict, List, Any, Optional, Union
import io
import os

from src.database import (
    create_candidate,
    create_task,
    create_submission,
    create_review,
    save_review_schedule,
    get_task,
    get_submissions_for_task,
    get_submission,
    get_reviews_for_task,
    get_review_for_submission,
    get_review,
    get_schedule_for_review,
    get_email_logs
)
from src.document_parser import parse_document
from src.submission_reader import process_uploaded_submission, fetch_github_repository
from src.ai_review import analyze_submission
from src.email_service import generate_feedback_email_content, send_or_simulate_email, is_smtp_configured


def register_candidate_and_task(
    name: str,
    email: str,
    role: str,
    batch: str,
    module_name: str,
    title: str,
    description: str,
    requirements_file_source: Optional[Union[str, bytes, io.BytesIO]] = None,
    requirements_filename: Optional[str] = None,
    raw_requirements_text: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Register a candidate and create their initial task with parsed requirements.
    """
    req_text = ""
    source_filename = None

    if requirements_file_source and requirements_filename:
        parsed = parse_document(requirements_file_source, requirements_filename)
        if not parsed["success"]:
            return {
                "success": False,
                "error": f"Failed to parse requirements document: {parsed['error']}"
            }
        req_text = parsed["text"]
        source_filename = requirements_filename
    elif raw_requirements_text and raw_requirements_text.strip():
        req_text = raw_requirements_text.strip()
        source_filename = "Manual_Requirements.txt"
    else:
        return {
            "success": False,
            "error": "A requirements document or manual requirements text must be provided."
        }

    try:
        cand_id = create_candidate(name, email, role, batch, db_path=db_path)
        task_id = create_task(
            candidate_id=cand_id,
            module_name=module_name,
            title=title,
            description=description,
            requirements_text=req_text,
            source_filename=source_filename,
            db_path=db_path
        )
        return {
            "success": True,
            "candidate_id": cand_id,
            "task_id": task_id,
            "requirements_length": len(req_text)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Database error during registration: {str(e)}"
        }


def process_submission_and_evaluate(
    task_id: int,
    submission_type: str,  # 'upload' or 'github'
    file_source: Optional[Union[str, bytes, io.BytesIO]] = None,
    filename: Optional[str] = None,
    github_url: Optional[str] = None,
    candidate_notes: str = "",
    known_issues: str = "",
    language: str = "English",
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process candidate work (file/ZIP upload or GitHub repo), create a revision,
    run the evaluation (Gemini or Fallback), and persist review results.
    """
    task = get_task(task_id, db_path=db_path)
    if not task:
        return {"success": False, "error": f"Task ID {task_id} not found."}

    # 1. Ingest submission content
    if submission_type == "github":
        if not github_url or not github_url.strip():
            return {"success": False, "error": "GitHub repository URL is required."}
        ingest_result = fetch_github_repository(github_url.strip())
    elif submission_type == "upload":
        if not file_source or not filename:
            return {"success": False, "error": "A submission file (document, code, or ZIP archive) is required."}
        ingest_result = process_uploaded_submission(file_source, filename)
    else:
        return {"success": False, "error": f"Unknown submission type: {submission_type}"}

    if not ingest_result.get("success"):
        return {
            "success": False,
            "error": ingest_result.get("error", "Failed to process candidate submission.")
        }

    # 2. Persist submission revision
    sub_id = create_submission(
        task_id=task_id,
        submission_type=submission_type,
        github_url=github_url if submission_type == "github" else None,
        candidate_notes=candidate_notes,
        known_issues=known_issues,
        files_summary=ingest_result.get("files_summary", []),
        raw_content=ingest_result.get("raw_content", ""),
        db_path=db_path
    )

    # 3. Perform AI or Fallback Review
    review_output = analyze_submission(
        task_requirements=task["requirements_text"],
        candidate_submission_text=ingest_result.get("raw_content", ""),
        candidate_notes=candidate_notes,
        known_issues=known_issues,
        files_summary=ingest_result.get("files_summary", []),
        language=language
    )

    # 4. Save review in database
    rev_id = create_review(
        submission_id=sub_id,
        overall_status=review_output["overall_status"],
        overall_score=review_output["overall_score"],
        is_ai_generated=review_output["is_ai_generated"],
        model_used=review_output["model_used"],
        language=review_output["language"],
        structured_data=review_output["structured_data"],
        feedback_summary=review_output["summary"],
        db_path=db_path
    )

    return {
        "success": True,
        "submission_id": sub_id,
        "review_id": rev_id,
        "review_result": review_output
    }


def schedule_and_notify(
    review_id: int,
    review_date: str,
    review_time: str,
    session_link: str,
    reviewer_message: str,
    send_real_email: bool = False,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Save scheduling details and dispatch/simulate candidate feedback email.
    """
    review = get_review(review_id, db_path=db_path)
    if not review:
        return {"success": False, "error": f"Review ID {review_id} not found."}

    sub = get_submission(review["submission_id"], db_path=db_path)
    task = get_task(sub["task_id"], db_path=db_path) if sub else None
    if not task:
        return {"success": False, "error": "Associated task not found."}

    # 1. Save schedule
    save_review_schedule(
        review_id=review_id,
        review_date=review_date,
        review_time=review_time,
        session_link=session_link,
        reviewer_message=reviewer_message,
        db_path=db_path
    )

    # 2. Build email content
    structured = review.get("structured_data", {})
    subject, body_text, body_html = generate_feedback_email_content(
        candidate_name=task["candidate_name"],
        module_name=task["module_name"],
        task_title=task["title"],
        review_status=review["overall_status"],
        review_score=review["overall_score"],
        strengths=structured.get("strengths", []),
        missing_items=structured.get("missing_components", []),
        actionable_corrections=structured.get("actionable_corrections", []),
        review_date=review_date,
        review_time=review_time,
        session_link=session_link,
        reviewer_message=reviewer_message
    )

    # 3. Send real email or simulate safely
    email_dispatch = send_or_simulate_email(
        review_id=review_id,
        recipient_email=task["candidate_email"],
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        force_simulation=not send_real_email,
        db_path=db_path
    )

    return {
        "success": email_dispatch["success"],
        "email_mode": email_dispatch["mode"],
        "email_status": email_dispatch["status"],
        "email_subject": subject,
        "email_preview_text": body_text,
        "email_preview_html": body_html,
        "message": email_dispatch.get("message") or email_dispatch.get("error")
    }
