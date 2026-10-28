# Engineering Handoff Document — Internship Task Review Assistant (Module 1)

**Date**: 2026-10-28  
**Current Milestone**: Module 1 — Core Review & Revision Engine (Complete & Tested)  
**Target Environment**: Local Python 3.14+ / Windows PowerShell / Streamlit  

---

## 1. Project Overview & Current State
The project is fully implemented, self-contained, tested, and locally runnable. It satisfies all P0 and P1 requirements for Module 1:
- HR can onboard candidates, define tasks, and upload requirements documents (PDF, DOCX, TXT, MD).
- Candidates can submit work via ZIP archive/code files or a public GitHub repository URL.
- Submissions are evaluated against requirements using either **Gemini API** or a **Deterministic Multilingual Rule-Based Fallback Engine** (English, Tamil, Hindi).
- Reviews produce transparent scores, requirement-by-requirement breakdowns, bugs, actionable corrections, and prioritized checklists.
- Next reviews can be scheduled with local date/time and meeting links.
- Email feedback can be previewed, transmitted via Real SMTP, or saved safely as `SIMULATED — NOT SENT`.
- Complete revision history is preserved in a local SQLite database (`data/assistant.db`).

---

## 2. Directory Structure & Key Files
```text
a:/ai_assistant/
├── app.py                     # Main Streamlit web application (5 navigation views)
├── requirements.txt           # Python package requirements
├── .env.example               # Template for Gemini and SMTP configuration
├── .gitignore                 # Excludes .env, *.db, cache, uploads
├── README.md                  # Comprehensive setup and user guide
├── CLAUDE.md                  # Claude Code session instructions
├── AGENTS.md                  # Tool-neutral instructions for coding agents
├── src/
│   ├── database.py            # SQLite schema, tables, and CRUD operations
│   ├── document_parser.py     # Resilient parser for PDF, DOCX, TXT, MD
│   ├── submission_reader.py   # ZIP extraction, file caps, public GitHub fetcher
│   ├── ai_review.py           # Gemini evaluation & Multilingual Fallback Engine
│   ├── review_service.py      # Workflow orchestration for tasks, reviews, and emails
│   └── email_service.py       # Plain-text/HTML templating, SMTP, and simulated logging
├── sample_data/
│   ├── company_requirements.md   # Ground truth task specification
│   ├── company_requirements.txt  # Plain-text version
│   ├── company_requirements.docx # Word document version
│   ├── candidate_submission_v1_partial.zip   # Revision 1 demo archive
│   ├── candidate_submission_v2_completed.zip # Revision 2 demo archive
│   └── generate_samples.py       # Data generator utility
├── tests/
│   ├── test_document_parser.py   # Document parsing test suite (6 tests)
│   ├── test_submission_reader.py # Submission ingestion test suite (4 tests)
│   ├── test_database.py          # SQLite persistence test suite (5 tests)
│   ├── test_ai_review.py         # AI & fallback evaluation test suite (2 tests)
│   ├── test_email_service.py     # Email rendering & simulation test suite (2 tests)
│   ├── test_end_to_end_workflow.py # Full review loop integration test (1 test)
│   └── test_app_smoke.py         # Streamlit AppTest smoke test (1 test)
└── docs/
    ├── PROJECT_PLAN.md        # Architecture, roadmap, Module 1 & 2 breakdown
    ├── TASKS.md               # Task completion status checklist
    └── HANDOFF.md             # This document
```

---

## 3. Verified Execution & Test Results
The automated test suite was executed on Python 3.14.3:
```powershell
python -m pytest tests/ -v
```
**Output**:
```text
============================= 21 passed in 4.39s ==============================
tests/test_ai_review.py::test_rule_based_review_structure PASSED         [  4%]
tests/test_ai_review.py::test_multilingual_rule_based_reviews PASSED     [  9%]
tests/test_app_smoke.py::test_app_smoke PASSED                           [ 14%]
tests/test_database.py::test_candidate_crud PASSED                       [ 19%]
tests/test_database.py::test_task_crud PASSED                            [ 23%]
tests/test_database.py::test_submission_revisions PASSED                 [ 28%]
tests/test_database.py::test_review_and_schedule_persistence PASSED      [ 33%]
tests/test_database.py::test_email_logs PASSED                           [ 38%]
tests/test_document_parser.py::test_parse_markdown_file PASSED           [ 42%]
tests/test_document_parser.py::test_parse_txt_file PASSED                [ 47%]
tests/test_document_parser.py::test_parse_docx_file PASSED               [ 52%]
tests/test_document_parser.py::test_parse_empty_file PASSED              [ 57%]
tests/test_document_parser.py::test_parse_unsupported_file PASSED        [ 61%]
tests/test_document_parser.py::test_parse_nonexistent_file PASSED        [ 66%]
tests/test_email_service.py::test_email_content_generation PASSED        [ 71%]
tests/test_email_service.py::test_simulated_email_dispatch_never_claims_sent PASSED [ 76%]
tests/test_end_to_end_workflow.py::test_full_review_and_revision_cycle PASSED [ 80%]
tests/test_submission_reader.py::test_process_zip_submission PASSED      [ 85%]
tests/test_submission_reader.py::test_process_single_code_file PASSED    [ 90%]
tests/test_submission_reader.py::test_parse_github_urls PASSED           [ 95%]
tests/test_submission_reader.py::test_corrupted_zip_file PASSED          [100%]
```

---

## 4. How to Run the Application
1. **Launch Streamlit**:
   ```powershell
   streamlit run app.py
   ```
2. **Access in Browser**:
   Open `http://localhost:8501`.

---

## 5. Step-by-Step Demo Script for Screen Recording
1. **Dashboard**: Navigate to `📊 Dashboard` to observe the system metric cards.
2. **HR Setup**:
   - Go to `👤 HR: Candidate & Task Setup`.
   - Click **"⚡ Fill Sample Demo Data"**.
   - Check **"Or use bundled sample requirements (`sample_data/company_requirements.md`)"**.
   - Click **"💾 Save Task & Register Candidate"**.
3. **Candidate Submission (Revision 1)**:
   - Go to `📥 Submit Candidate Work`.
   - Select the created candidate.
   - Click **"📂 Use Sample V1 (Partial Submission)"**.
   - Select explanation language (e.g. English, Tamil, or Hindi).
   - Click **"🚀 Analyze Submission & Generate Review"**.
4. **Review Report & Scheduling**:
   - Go to `📝 Review & Feedback Report`.
   - Observe the Engine Banner (`Rule-Based Demo Results` or `AI Review`).
   - Inspect the Requirement Analysis, Strengths, Bugs, and Prioritized Checklist.
   - Under Scheduling: select review date, time, and session link.
   - Click **"💾 Save Simulated Email (Demo Mode)"**; observe the status `SIMULATED — NOT SENT`.
5. **Candidate Resubmission (Revision 2)**:
   - Go to `📥 Submit Candidate Work`.
   - Click **"📂 Use Sample V2 (Completed Submission)"**.
   - Click **"🚀 Analyze Submission & Generate Review"**.
   - Observe the improved score and `Completed` status in `📝 Review & Feedback Report`.
6. **Revision History**:
   - Go to `🔁 Revision History & Email Logs` to review the full timeline and email audit log.

---

## 6. Known Limitations & Constraints
- **Public GitHub API Rate Limits**: GitHub limits unauthenticated requests to 60 per hour per IP. If exceeded, users should upload a ZIP archive of their repository.
- **Zero-Execution Environment**: Candidate code is statically analyzed; dynamic integration testing requires Module 2's Docker runner.
- **Local Time**: Scheduled dates/times use the host machine's local system time.

---

## 7. Instructions for Continuing Agent (VS Code / Codex / Antigravity)
- To configure Gemini API: create a `.env` file from `.env.example` and set `GEMINI_API_KEY=your_key`.
- The database schema is managed in `src/database.py`. Any new fields should include `ALTER TABLE` migrations or defaults.
- UI changes should remain inside `app.py` or modular components under `src/`.
