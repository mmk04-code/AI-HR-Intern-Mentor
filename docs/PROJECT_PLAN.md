# Project Plan — Internship Task Review Assistant

## 1. Executive Summary
The **Internship Task Review Assistant** is an intelligent pairing and evaluation system designed to streamline the lifecycle of assigning technical modules to interns, evaluating their code submissions against official company requirements, generating actionable pedagogical feedback, scheduling follow-up technical reviews, and dispatching audit-trailed notifications.

---

## 2. Core Architectural Principles
- **Separation of Concerns**: Decoupled document parsing, submission ingestion, AI evaluation, persistent data storage, and email notification.
- **Resilience & Fault Tolerance**: Deterministic Rule-Based Fallback ensures continuous demo capability even without an active Gemini API key or external internet connectivity.
- **Zero-Execution Sandbox**: Candidate code is statically analyzed via parsed ASTs and raw string tokenizers; candidate code is **never** executed.
- **Data Integrity & Immutability**: All submissions are strictly versioned as Revisions ($1, 2, \dots$). Historical reviews, scores, and schedules are preserved indefinitely.
- **Audit Transparency**: Simulated emails are recorded with status `SIMULATED — NOT SENT`. The system never misrepresents simulated activity as delivered.

---

## 3. Module Breakdown

### Module 1: Core Review & Revision Engine (Current Scope)
- **HR & Task Setup**: Intern onboarding, module configuration, and ground-truth requirements ingestion (PDF, DOCX, TXT, Markdown).
- **Candidate Ingestion**: Dual-channel support (ZIP file upload and Public GitHub API retrieval with rate-limiting and size safeguards).
- **Evaluation Engine**: Gemini API structured output with configurable model (`gemini-2.0-flash`), combined with a multilingual rule-based fallback engine (English, Tamil, Hindi).
- **Feedback & Actionable Reporting**: Overall outcome status (`Completed`, `Needs Changes`, `Incomplete`), requirement-by-requirement verification, bugs/issues, missing components, and prioritized next-action checklists.
- **Scheduling & Dispatch**: Local-time scheduling, meeting link registration, and dual-mode email notification (Real SMTP vs Simulated Demo Mode).
- **Revision History Loop**: Incremental submission cycles tracking candidate progression from preliminary drafts to completed solutions.

### Module 2: Enhanced Capabilities (Future Planned Scope)
- **Voice-Based Conversational Tutor**: Interactive audio debriefing using WebRTC or speech-to-text / text-to-speech APIs.
- **Automated Dockerized Sandboxed Execution**: Optional containerized test runner with isolated runtime limits for running unit test suites.
- **Enterprise Multi-Tenant Authentication**: Role-based access control (RBAC) with OAuth2 / SAML for corporate HR teams.
- **GitHub PR / Webhook Automation**: Automatic triggering of review pipeline when a candidate opens a pull request.
- **LMS & Spreadsheet Sync**: Real-time webhook connectors to Google Sheets, Notion, or Canvas LMS.

---

## 4. Technology Stack
| Layer | Technology | Justification |
| :--- | :--- | :--- |
| **Language** | Python 3.14+ | Standardized, cross-platform, extensive standard library |
| **UI Framework** | Streamlit 1.55+ | Rapid, interactive local web application |
| **Storage Engine** | SQLite 3 | Zero-configuration, ACID compliant local persistence |
| **AI LLM** | Google Gemini API | High context window, structured JSON schemas |
| **Document Processing** | `pypdf`, `python-docx` | Native parsing of PDF, Word, and text documents |
| **Networking** | `requests` | Public GitHub API integration with rate-limit awareness |
| **Testing** | `pytest`, `AppTest` | Unit, integration, and UI smoke test automation |
