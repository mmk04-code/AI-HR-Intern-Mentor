# Internship Task Review Assistant (Module 1)

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit 1.55+](https://img.shields.io/badge/streamlit-1.55+-FF4B4B.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-21%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, local developer tool that streamlines the evaluation of intern tasks, compares candidate submissions against official company requirements, generates structured pedagogical feedback, schedules follow-up review sessions, and manages revision cycles.

---

## 🌟 Key Features (Module 1)

1. **HR & Task Setup**:
   - Register intern profile (Name, Email, Role, Batch).
   - Configure module and task title.
   - Ingest official company requirements documents (**PDF, DOCX, TXT, Markdown**).
   - Ground-truth enforcement: only requirements in the document or explicitly entered are evaluated.

2. **Candidate Work Ingestion**:
   - **Upload Mode**: Supports single code/document files or **ZIP archives** with automatic safe extraction.
   - **Public GitHub Mode**: Ingests repository tree and file contents via GitHub REST API without requiring credentials.
   - **Zero-Execution Guarantee**: Candidate code is statically analyzed and **never executed**.
   - Input fields for candidate completion notes and declared known issues.

3. **Intelligent Comparison & Feedback**:
   - **Dual Evaluation Engine**:
     - **Gemini AI**: High-reasoning evaluation via Google Gemini API (`gemini-2.0-flash` or configurable).
     - **Multilingual Fallback Engine**: Deterministic rule-based comparison when API keys are absent or network is unavailable.
     - **Explicit Engine Labelling**: The UI visibly identifies whether results are genuine AI output or Rule-Based Demo Results.
   - **Detailed Output**: Overall Status (`Completed`, `Needs Changes`, `Incomplete`), transparent score (0-100), requirement-by-requirement comparison with evidence snippets, identified bugs, missing components, and actionable corrections.
   - **Language Support**: Explanations available in **English, Tamil, and Hindi**.

4. **Next Review Scheduling**:
   - Reviewer sets follow-up date, time (host local timezone), meeting/session link, and personalized message.
   - Visual notification if a localhost link is used.

5. **Feedback Notification & Dispatch**:
   - Full plain-text and HTML email previews.
   - **Real SMTP Mode**: Sends live emails if SMTP credentials are provided in `.env`.
   - **Safe Simulation Mode**: When SMTP is unconfigured, logs email with status `SIMULATED — NOT SENT`.

6. **Revision Loop & Audit Trail**:
   - Preserves all historical submissions and reviews.
   - Supports multiple revisions per task ($1, 2, \dots$), tracking candidate improvement over time.
   - Persistent SQLite database with immutable audit logs.

---

## 📁 Project Structure

```text
ai_assistant/
├── app.py                     # Main Streamlit web application
├── requirements.txt           # Python dependencies
├── .env.example               # Configuration template
├── .gitignore                 # Git ignore rules
├── README.md                  # System documentation
├── CLAUDE.md                  # Claude Code agent instructions
├── AGENTS.md                  # Tool-neutral agent guide
├── src/
│   ├── database.py            # SQLite schema and CRUD operations
│   ├── document_parser.py     # PDF, DOCX, TXT, MD parser
│   ├── submission_reader.py   # ZIP and public GitHub repository reader
│   ├── ai_review.py           # Gemini AI and Rule-Based Fallback Engine
│   ├── review_service.py      # Business logic orchestration
│   └── email_service.py       # Email templating, SMTP dispatch, and simulation
├── sample_data/
│   ├── company_requirements.md   # Ground-truth task requirements
│   ├── company_requirements.txt  # Plain-text requirements
│   ├── company_requirements.docx # Word document requirements
│   ├── candidate_submission_v1_partial.zip   # Revision 1 sample archive
│   ├── candidate_submission_v2_completed.zip # Revision 2 sample archive
│   └── generate_samples.py       # Data generator utility
├── tests/
│   ├── test_document_parser.py   # Document parsing tests
│   ├── test_submission_reader.py # ZIP and GitHub parsing tests
│   ├── test_database.py          # SQLite database tests
│   ├── test_ai_review.py         # AI & fallback engine tests
│   ├── test_email_service.py     # Email rendering & simulation tests
│   ├── test_end_to_end_workflow.py # End-to-end integration test
│   └── test_app_smoke.py         # Streamlit AppTest smoke test
└── docs/
    ├── PROJECT_PLAN.md        # System architecture and Module 1/2 roadmap
    ├── TASKS.md               # Task completion tracking
    └── HANDOFF.md             # Developer handoff and session notes
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher (tested on Python 3.14).
- Git installed.

### 2. Installation
Clone or navigate to the project directory and install dependencies:
```bash
cd a:/ai_assistant
pip install -r requirements.txt
```

### 3. Optional Configuration (`.env`)
The application is designed to run **out-of-the-box without any API keys or configuration**. It defaults to the **Rule-Based Fallback Demo Engine** and **Simulated Email Mode**.

To enable genuine Gemini AI review or Real SMTP sending, create a `.env` file:
```bash
cp .env.example .env
```
Edit `.env`:
```env
# Gemini API Key (Optional)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# SMTP Email Dispatch (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=your_email@gmail.com
SMTP_USE_TLS=true
```

### 4. Running the Web Application
Launch the local Streamlit server:
```bash
python -m streamlit run app.py
```
*(Or `streamlit run app.py` if python scripts are on your PATH)*

Open your browser to: **`http://localhost:8501`**

---

## 🧪 Running Automated Tests

Run the full pytest suite (21 automated tests covering units, integration, and UI smoke testing):
```bash
python -m pytest tests/ -v
```

Expected output:
```text
============================= 21 passed in 4.39s ==============================
```

---

## 🎬 End-to-End Demo Workflow (For Screen Recording)

Follow this 5-minute walkthrough to demonstrate the full workflow:

### Step 1: Dashboard Overview
1. Open `http://localhost:8501`.
2. Notice the metric tiles on the **📊 Dashboard** (Registered Candidates, Active Tasks, Completed Tasks, Average Score).

### Step 2: HR Candidate & Task Setup
1. In the sidebar, select **👤 HR: Candidate & Task Setup**.
2. Click **"⚡ Fill Sample Demo Data"** to auto-populate the intern's details.
3. Keep **"Or use bundled sample requirements (`sample_data/company_requirements.md`)"** checked.
4. Click **"💾 Save Task & Register Candidate"**.
5. Notice the success confirmation with parsed character count.

### Step 3: Candidate Submission — Revision 1 (Partial Work)
1. Select **📥 Submit Candidate Work** from the sidebar.
2. The newly created candidate and task are selected by default.
3. Click **"📂 Use Sample V1 (Partial Submission)"** (loads a partial Flask implementation missing validation and tests).
4. Select your preferred explanation language (**English**, **Tamil**, or **Hindi**).
5. Click **"🚀 Analyze Submission & Generate Review"**.

### Step 4: Review Report, Scheduling & Feedback Email
1. The app automatically navigates to **📝 Review & Feedback Report**.
2. Note the **Engine Status Banner** (Rule-Based Fallback or Gemini AI).
3. Review the status badge (**Needs Changes**), score, requirement-by-requirement analysis, strengths, bugs, and prioritized checklist.
4. Scroll to **📅 Schedule Next Review Session**:
   - Choose a date and time.
   - Enter a meeting link or keep the default localhost session note.
5. Under **📧 Candidate Feedback Email**:
   - Preview the plain-text and HTML email formatting.
   - Click **"💾 Save Simulated Email (Demo Mode)"**.
   - Notice the green confirmation indicating status: `SIMULATED — NOT SENT`.

### Step 5: Candidate Resubmission — Revision 2 (Completed Work)
1. Navigate back to **📥 Submit Candidate Work**.
2. Notice the indicator: **"This will be registered as Revision 2"**.
3. Click **"📂 Use Sample V2 (Completed Submission)"** (loads the complete implementation with validation and unit tests).
4. Click **"🚀 Analyze Submission & Generate Review"**.
5. View the updated report: outcome changes to **Completed** with a higher score!

### Step 6: Revision History & Audit Trail
1. In the sidebar, click **🔁 Revision History & Email Logs**.
2. Inspect the **Submission & Review Timeline** showing both Revision 1 and Revision 2 with scores and timestamps.
3. Review the **Persistent Email Dispatch Audit Logs** table showing the recorded email with status `SIMULATED — NOT SENT`.

---

## ⚙️ How Gemini and SMTP Fallbacks Work

| Feature | When Configured in `.env` | When Unconfigured / Missing |
| :--- | :--- | :--- |
| **Review Engine** | Uses Google Gemini (`gemini-2.0-flash`) for multi-modal reasoning. UI displays: `🤖 AI REVIEW (Powered by Gemini)`. | Uses deterministic keyword and pattern matching. UI displays: `⚖️ RULE-BASED DEMO RESULTS (Fallback Engine)`. |
| **Email Dispatch** | Reviewer can click **"Send Real Email via SMTP"** to dispatch real TLS emails. | Button is safely disabled. Reviewer clicks **"Save Simulated Email"**, recorded as `SIMULATED — NOT SENT`. |

---

## ⚠️ Known Limitations & Assumptions

1. **GitHub API Rate Limits**: Unauthenticated anonymous requests to public GitHub repositories are subject to GitHub's IP rate limit (60 requests/hour). If rate limits are reached, candidates can upload a ZIP archive of their project.
2. **Localhost Session Links**: Meeting links using `http://localhost:...` are only accessible on the local laptop; a warning indicator is displayed in the UI.
3. **Static Analysis vs Execution**: For security reasons, candidate code is statically analyzed and **never executed**. Live test execution is reserved for Module 2's sandboxed container architecture.

---

## 🔮 Roadmap: Planned Module 2 Scope

- [ ] **Voice-Based Conversational Tutor**: Interactive voice debriefing using Gemini Live Audio or WebRTC speech synthesis.
- [ ] **Dockerized Sandbox Execution**: Isolated container execution for running candidate test suites with CPU/memory limits.
- [ ] **Enterprise SSO & Role-Based Access**: Role management for HR Managers, Technical Reviewers, and Interns.
- [ ] **GitHub Webhook Integration**: Automatic triggering of review pipeline on Pull Request events.

---

## 📤 Publishing to GitHub

To publish this project to your GitHub account:

1. Create a new public repository on GitHub (e.g. `internship-task-review-assistant`).
2. Verify that local secrets and databases are ignored:
   ```bash
   git status
   ```
3. Add and commit all project files:
   ```bash
   git add .
   git commit -m "feat: complete Module 1 Internship Task Review Assistant"
   ```
4. Set the main branch and add the remote URL:
   ```bash
   git branch -M main
   git remote add origin https://github.com/<YOUR-GITHUB-USERNAME>/internship-task-review-assistant.git
   ```
5. Push to GitHub:
   ```bash
   git push -u origin main
   ```
