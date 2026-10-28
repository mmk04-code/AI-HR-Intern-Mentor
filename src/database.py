"""
Database module for Internship Task Review Assistant.
Manages local SQLite database initialization and CRUD operations.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "assistant.db")


def get_db_path() -> str:
    """Return the database path from environment or default."""
    path = os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    return path


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get a SQLite connection with row_factory set to sqlite3.Row."""
    target_path = db_path or get_db_path()
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables if they do not exist."""
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL,
            batch TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
            module_name TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            requirements_text TEXT NOT NULL,
            source_filename TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            revision_number INTEGER NOT NULL,
            submission_type TEXT NOT NULL, -- 'upload' or 'github'
            github_url TEXT,
            candidate_notes TEXT,
            known_issues TEXT,
            files_summary TEXT, -- JSON string of file names/sizes
            raw_content TEXT, -- Extracted text of submission
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
            overall_status TEXT NOT NULL, -- 'Completed', 'Needs Changes', 'Incomplete'
            overall_score INTEGER NOT NULL,
            is_ai_generated INTEGER NOT NULL DEFAULT 0, -- 1 for Gemini AI, 0 for Rule-based Fallback
            model_used TEXT,
            language TEXT DEFAULT 'English',
            structured_data_json TEXT NOT NULL,
            feedback_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS review_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
            review_date TEXT NOT NULL,
            review_time TEXT NOT NULL,
            session_link TEXT,
            reviewer_message TEXT,
            scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
            recipient_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            body_text TEXT NOT NULL,
            body_html TEXT,
            mode TEXT NOT NULL, -- 'REAL' or 'SIMULATED'
            status TEXT NOT NULL, -- 'SENT', 'SIMULATED — NOT SENT', 'FAILED'
            error_message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
    conn.close()


# Candidate CRUD
def create_candidate(name: str, email: str, role: str, batch: str, db_path: Optional[str] = None) -> int:
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            "INSERT INTO candidates (name, email, role, batch) VALUES (?, ?, ?, ?)",
            (name.strip(), email.strip(), role.strip(), batch.strip())
        )
        candidate_id = cursor.lastrowid
    conn.close()
    return candidate_id


def get_candidates(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM candidates ORDER BY created_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_candidate(candidate_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# Task CRUD
def create_task(
    candidate_id: int,
    module_name: str,
    title: str,
    description: str,
    requirements_text: str,
    source_filename: Optional[str] = None,
    db_path: Optional[str] = None
) -> int:
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            """INSERT INTO tasks (candidate_id, module_name, title, description, requirements_text, source_filename)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (candidate_id, module_name.strip(), title.strip(), description.strip(), requirements_text.strip(), source_filename)
        )
        task_id = cursor.lastrowid
    conn.close()
    return task_id


def get_all_tasks(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.execute("""
        SELECT t.*, c.name as candidate_name, c.email as candidate_email, c.role as candidate_role, c.batch as candidate_batch
        FROM tasks t
        JOIN candidates c ON t.candidate_id = c.id
        ORDER BY t.created_at DESC
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_tasks_for_candidate(candidate_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM tasks WHERE candidate_id = ? ORDER BY created_at DESC", (candidate_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_task(task_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.execute("""
        SELECT t.*, c.name as candidate_name, c.email as candidate_email, c.role as candidate_role, c.batch as candidate_batch
        FROM tasks t
        JOIN candidates c ON t.candidate_id = c.id
        WHERE t.id = ?
    """, (task_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# Submission CRUD
def get_next_revision_number(task_id: int, db_path: Optional[str] = None) -> int:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT MAX(revision_number) as max_rev FROM submissions WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row["max_rev"] is not None:
        return int(row["max_rev"]) + 1
    return 1


def create_submission(
    task_id: int,
    submission_type: str,
    github_url: Optional[str] = None,
    candidate_notes: Optional[str] = None,
    known_issues: Optional[str] = None,
    files_summary: Optional[List[Dict[str, Any]]] = None,
    raw_content: Optional[str] = None,
    db_path: Optional[str] = None
) -> int:
    rev_num = get_next_revision_number(task_id, db_path)
    summary_str = json.dumps(files_summary or [])
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            """INSERT INTO submissions (task_id, revision_number, submission_type, github_url, candidate_notes, known_issues, files_summary, raw_content)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (task_id, rev_num, submission_type, github_url, candidate_notes or "", known_issues or "", summary_str, raw_content or "")
        )
        submission_id = cursor.lastrowid
    conn.close()
    return submission_id


def get_submissions_for_task(task_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM submissions WHERE task_id = ? ORDER BY revision_number DESC", (task_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    for r in rows:
        if r.get("files_summary"):
            try:
                r["files_summary"] = json.loads(r["files_summary"])
            except Exception:
                pass
    return rows


def get_submission(submission_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        if d.get("files_summary"):
            try:
                d["files_summary"] = json.loads(d["files_summary"])
            except Exception:
                pass
        return d
    return None


# Review CRUD
def create_review(
    submission_id: int,
    overall_status: str,
    overall_score: int,
    is_ai_generated: bool,
    model_used: Optional[str],
    language: str,
    structured_data: Dict[str, Any],
    feedback_summary: str,
    db_path: Optional[str] = None
) -> int:
    data_json = json.dumps(structured_data, ensure_ascii=False)
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            """INSERT INTO reviews (submission_id, overall_status, overall_score, is_ai_generated, model_used, language, structured_data_json, feedback_summary)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (submission_id, overall_status, overall_score, 1 if is_ai_generated else 0, model_used or "Fallback Rule-Based", language, data_json, feedback_summary)
        )
        review_id = cursor.lastrowid
    conn.close()
    return review_id


def get_review_for_submission(submission_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM reviews WHERE submission_id = ? ORDER BY created_at DESC LIMIT 1", (submission_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        try:
            d["structured_data"] = json.loads(d["structured_data_json"])
        except Exception:
            d["structured_data"] = {}
        return d
    return None


def get_review(review_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        try:
            d["structured_data"] = json.loads(d["structured_data_json"])
        except Exception:
            d["structured_data"] = {}
        return d
    return None


def get_reviews_for_task(task_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.execute("""
        SELECT r.*, s.revision_number, s.submission_type, s.submitted_at
        FROM reviews r
        JOIN submissions s ON r.submission_id = s.id
        WHERE s.task_id = ?
        ORDER BY s.revision_number DESC
    """, (task_id,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    for r in rows:
        try:
            r["structured_data"] = json.loads(r["structured_data_json"])
        except Exception:
            r["structured_data"] = {}
    return rows


# Schedule CRUD
def save_review_schedule(
    review_id: int,
    review_date: str,
    review_time: str,
    session_link: Optional[str] = None,
    reviewer_message: Optional[str] = None,
    db_path: Optional[str] = None
) -> int:
    conn = get_connection(db_path)
    with conn:
        # Check if schedule exists for this review
        existing = conn.execute("SELECT id FROM review_schedules WHERE review_id = ?", (review_id,)).fetchone()
        if existing:
            conn.execute(
                """UPDATE review_schedules
                   SET review_date = ?, review_time = ?, session_link = ?, reviewer_message = ?, scheduled_at = CURRENT_TIMESTAMP
                   WHERE review_id = ?""",
                (review_date, review_time, session_link or "", reviewer_message or "", review_id)
            )
            schedule_id = existing["id"]
        else:
            cursor = conn.execute(
                """INSERT INTO review_schedules (review_id, review_date, review_time, session_link, reviewer_message)
                   VALUES (?, ?, ?, ?, ?)""",
                (review_id, review_date, review_time, session_link or "", reviewer_message or "")
            )
            schedule_id = cursor.lastrowid
    conn.close()
    return schedule_id


def get_schedule_for_review(review_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM review_schedules WHERE review_id = ?", (review_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# Email Log CRUD
def log_email(
    review_id: int,
    recipient_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str],
    mode: str,
    status: str,
    error_message: Optional[str] = None,
    db_path: Optional[str] = None
) -> int:
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            """INSERT INTO email_logs (review_id, recipient_email, subject, body_text, body_html, mode, status, error_message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (review_id, recipient_email, subject, body_text, body_html or "", mode, status, error_message or "")
        )
        log_id = cursor.lastrowid
    conn.close()
    return log_id


def get_email_logs(review_id: Optional[int] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    if review_id:
        cursor = conn.execute("SELECT * FROM email_logs WHERE review_id = ? ORDER BY sent_at DESC", (review_id,))
    else:
        cursor = conn.execute("SELECT * FROM email_logs ORDER BY sent_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
