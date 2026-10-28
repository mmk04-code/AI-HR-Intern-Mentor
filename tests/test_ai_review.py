"""
Unit tests for src/ai_review.py
"""

import pytest
from src.ai_review import analyze_submission, _run_rule_based_review


def test_rule_based_review_structure():
    requirements = """
    1. Database Schema: Implement models for User, Project, TaskItem with foreign keys.
    2. API Endpoints: Task creation, listing, updating, and validation.
    3. Unit Tests: Test task creation and title validation.
    4. README Documentation: Installation and execution guide.
    """

    submission_code = """
    # models.py
    class TaskItem:
        title = "Sample"

    # app.py
    def list_tasks():
        return []
    """

    result = analyze_submission(
        task_requirements=requirements,
        candidate_submission_text=submission_code,
        candidate_notes="First version",
        known_issues="Tests not added yet",
        files_summary=[{"path": "models.py", "size": 100}, {"path": "app.py", "size": 150}],
        language="English"
    )

    assert result["success"] is True
    assert result["is_ai_generated"] is False  # Fallback since no API key provided
    assert "overall_status" in result
    assert result["overall_status"] in ["Needs Changes", "Incomplete", "Completed"]
    assert 0 <= result["overall_score"] <= 100
    assert "structured_data" in result

    data = result["structured_data"]
    assert "requirements_analysis" in data
    assert len(data["requirements_analysis"]) > 0
    assert "prioritized_checklist" in data
    assert "limitations" in data


def test_multilingual_rule_based_reviews():
    reqs = "Implement User authentication and task management."
    code = "def authenticate(): pass"

    for lang in ["English", "Tamil", "Hindi"]:
        res = analyze_submission(
            task_requirements=reqs,
            candidate_submission_text=code,
            language=lang
        )
        assert res["success"] is True
        assert res["language"] == lang
        assert res["structured_data"]["summary"] != ""
