# Internship Task Review Assistant — Chat-First AI Mentor

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit 1.55+](https://img.shields.io/badge/streamlit-1.55+-FF4B4B.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-30%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, conversational pair-programming and mentorship assistant for evaluating intern tasks, answering technical questions in multiple languages (English, Tamil, Hindi), scheduling review sessions, and dispatching audit-trailed notifications.

---

## 🌟 Key Features (Chat-First UI)

1. **Role-Based Conversational Portal**:
   - **HR / Company Interface**: Natural language chat where HR can type or speak instructions (e.g. *"Import interns from Excel and assign Module 1. Deadline is Friday"*), attach Excel/CSV rosters (`.xlsx`, `.csv`), attach official requirements docs, review assignment summary cards, and confirm task assignments.
   - **Employee / Intern AI Mentor Interface**: Dedicated 1-on-1 AI mentor chat providing conversational task walkthroughs, technical Q&A, and direct in-chat submissions.

2. **Multilingual Dialogue & Voice Interaction**:
   - AI Mentor welcomes interns and prompts for language preference: **English, Tamil (தமிழ்), or Hindi (हिंदी)**.
   - Explains official requirements conversationally in the intern's chosen language.
   - **Voice Output**: In-memory Text-to-Speech audio player (`gTTS` / Gemini Live API fallback) allowing interns to listen to mentor explanations.
   - **Voice Input**: Integrated microphone audio capture (`st.audio_input`).

3. **Multi-Provider Backend Hierarchy**:
   - Automatically and safely detects `.env` configurations (supporting `.env` files or `.env/api_key` directories, quoted or unquoted keys).
   - **Hierarchy**: Primary Gemini Key -> Secondary Gemini Key -> OpenAI -> Deterministic Rule-Based Fallback.
   - Never exposes secret keys or configuration dropdowns in the UI.

4. **In-Chat Candidate Submission & Evaluation**:
   - Directly attach project files / ZIP archives or paste public GitHub repository URLs inside the chat.
   - Instant structural & code comparison against official company requirements using Gemini or the deterministic fallback engine.
   - In-chat conversational feedback breakdown: Score, Strengths, Things to fix, and Actionable next steps.
   - Retains full revision history ($1, 2, \dots$) upon resubmission.

4. **Next Review Scheduling & Safe Email Dispatch**:
   - Follow-up review sessions and email notifications previewed directly in chat.
   - Sends real emails via SMTP when configured in `.env`; otherwise records with status **`SIMULATED — NOT SENT`**.

5. **Clean & Minimalist Design**:
   - Zero UI clutter: No manual dashboard cards, no technical sidebars, no visible API keys, and no model configuration dropdowns. All sensitive credentials reside exclusively in the backend `.env`.

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

To enable Gemini or OpenAI model reviews, or real SMTP sending, configure the ignored `.env` file. If it does not exist, copy the template; if it already exists, edit it in place (do not overwrite it):
```bash
cp .env.example .env
```
Edit the ignored `.env` file (never put real credentials in `.env.example`):
```env
# Gemini API Key (Optional)
GEMINI_API_KEY=your_real_gemini_api_key
GEMINI_MODEL=gemini-3.6-flash

# OpenAI (optional; used when Gemini is unavailable)
OPENAI_API_KEY=your_real_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# SMTP Email Dispatch (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM=your_email@gmail.com
SMTP_USE_TLS=true
```

The OpenAI key can also be supplied as `OPEN_AI_API_KEY`, `Open_AI_KEY`, or
`OPENAI_KEY`. For secret-file deployments, `.env/open_ai/api_key` is supported.
The review and mentor chat use the configured model; if all configured LLM APIs
fail or no key is set, the app keeps using its labeled deterministic fallback.

### 4. Running the Web Application
Launch the local Streamlit server:
```bash
python -m streamlit run app.py
```
*(Or `streamlit run app.py` if python scripts are on your PATH)*

Open your browser to: **`http://localhost:8501`**

---

## 🧪 Running Automated Tests

Run the deterministic suite without the optional live API check:
```bash
python -m pytest tests/ -v -m "not live_api"
```

To test a configured Gemini key and model separately, use the **Test Gemini connection** button in the HR attachment drawer. This makes one live provider request and reports the provider/model result.

---

## 🎬 End-to-End Demo Workflow (Chat-First Experience)

Follow this 5-minute walkthrough to demonstrate the full conversational workflow:

### Step 1: Login Screen
1. Open **`http://localhost:8501`**.
2. Notice the clean, minimalist role selection:
   - **🏢 HR / Company**
   - **🎓 Employee / Intern**

### Step 2: HR Chat & Task Assignment
1. Click **"Enter as HR Coordinator"**.
2. In the attachment drawer (`📎 Attach Documents & Voice Input`), click **"⚡ Use Sample Roster & Requirements"** (attaches `interns_roster.xlsx` and `company_requirements.md`).
3. Type in the chatbox:
   > *"Import these interns from the Excel file and assign them Full-Stack Task Tracker Module 1. Deadline is Friday."*
4. The AI assistant responds with an **Assignment Summary Card** displaying the 3 parsed interns, task title, and deadline.
5. Click **"✅ Confirm & Assign Tasks to Interns"**.
6. The assistant confirms: *"Successfully created tasks for 3 interns: Aarav Sharma, Priya Patel, Karthik Raja."*
7. Ask in chat: *"What is the status of the interns?"* to see live progress tracking!
8. Click **"Sign Out"** at the top right.

### Step 3: Intern AI Mentor Chat & Language Selection
1. Back on the login screen, select **Aarav Sharma** from the dropdown and click **"Log In as Intern"**.
2. Notice the minimal top banner: `📌 Task: Module 1 — Full-Stack Task Tracker Core`.
3. The AI Mentor greets Aarav and asks for their language preference:
   - Click **`🇬🇧 English`**, **`🇮🇳 தமிழ் (Tamil)`**, or **`🇮🇳 हिंदी (Hindi)`** (or speak/type your answer).
4. The Mentor introduces the task conversationally in the selected language and plays **Mentor Voice Audio**!
5. Ask any technical question (e.g. *"How do I validate the title length?"*) to see the mentor's pedagogical response.

### Step 4: In-Chat Code Submission & Evaluation (Revision 1)
1. In the attachment drawer, click **"📂 Attach Sample V1 (Partial)"**.
2. Type in the chat: *"Here is my first draft for review."* and press Send.
3. The AI Mentor evaluates the code against the company requirements and replies directly in chat with:
   - Overall Outcome (**Needs Changes**) and Score (e.g. 50/100).
   - Strengths, Areas for Improvement, and Actionable Next Steps.
   - **AI Mentor Voice** playing spoken feedback!
   - Follow-up meeting details and a **"Save Feedback Notification (Demo)"** button logging status: `SIMULATED — NOT SENT`.

### Step 5: In-Chat Resubmission (Revision 2 - Completed)
1. Click **"📂 Attach Sample V2 (Completed)"**.
2. Send message: *"I have implemented the validation rules, filters, and unit tests."*
3. The AI Mentor evaluates the new revision, automatically updating to **Revision 2**, and congratulates the intern with a **Completed** status and higher score!

### Step 6: HR Progress Inquiry
1. Click **"Sign Out"** and log back in as **HR Coordinator**.
2. Type: *"Show me the progress of all interns."*
3. The HR bot reports: *"Aarav Sharma: Status: Completed (Score: 88/100, Revisions: 2)"*.

---

## ⚙️ How Gemini and SMTP Fallbacks Work

| Feature | When Configured in `.env` | When Unconfigured / Missing |
| :--- | :--- | :--- |
| **AI Status & Indicator** | UI displays configured provider/model, marked as unverified until the connection test succeeds. Queries follow Gemini → secondary Gemini → OpenAI. | UI displays limited mode; reviews use the clearly labeled deterministic fallback and mentor answers use verified local references. |
| **Review Engine** | Uses configured Google Gemini / OpenAI models for reasoning. UI displays: `🤖 AI REVIEW (Powered by Gemini)`. | Uses deterministic keyword and pattern matching. UI displays: `⚖️ RULE-BASED DEMO RESULTS (Fallback Engine)`. |
| **Offline Knowledge Base** | Full local dataset reference library available in UI and via search service (`src/offline_knowledge.py`). | Full local dataset reference library available in UI and via search service (`src/offline_knowledge.py`). |
| **Email Dispatch** | Reviewer can click **"Send Real Email via SMTP"** to dispatch real TLS emails. | Button is safely disabled. Reviewer clicks **"Save Simulated Email"**, recorded as `SIMULATED — NOT SENT`. |

---

## 📚 Offline Knowledge Base & Dataset Validation

The application includes a curated, verified offline dataset in `data/` providing instant, reliable reference information without external APIs:

- `data/python_learning.json`: Python core, data structures, exceptions, OOP, context managers.
- `data/web_development.json`: REST principles, HTTP status codes, DOM, Flexbox/Grid, CORS, ORM.
- `data/ai_ml_learning.json`: Machine learning basics, evaluation metrics, TF-IDF, embeddings.
- `data/git_github.json`: Staging, branch workflows, merge conflict resolution, rebase.
- `data/internship_tasks.json`: Educational reference tasks with objectives, deliverables, and rubrics.
- `data/faq.json`: Portal procedures, submissions, offline mode, and review policies.

To validate dataset integrity:
```bash
python scripts/validate_dataset.py
```

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
