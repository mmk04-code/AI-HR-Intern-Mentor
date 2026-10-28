# Agent Instructions — Internship Task Review Assistant

This document contains tool-neutral development instructions for any AI assistant (Codex, Antigravity, VS Code, Cursor).

## Environment Setup
1. Use Python 3.10 or higher.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configuration:
   - Copy `.env.example` to `.env` if configuring Gemini or SMTP.
   - If `.env` is omitted, the app operates automatically in Fallback Rule-Based Demo Mode.

## Running Tests
Run pytest across all unit and integration tests:
```bash
python -m pytest tests/ -v
```

## Running the Web Application
Start Streamlit on default local port 8501:
```bash
streamlit run app.py
```

## Core Behavioral Constraints
1. **Zero Execution of Candidate Code**: Never execute candidate submissions using `exec()`, `subprocess`, or direct imports.
2. **Deterministic Fallback Engine**: If Gemini API is unreachable, the system must produce rule-based evaluation and explicitly label results as `Rule-Based Demo Results (Fallback)`.
3. **Audit Trail**: Every submission creates a new revision ($1, 2, \dots$). Email logs must record `SIMULATED — NOT SENT` when SMTP is inactive.
4. **Localization**: Maintain English, Tamil, and Hindi language support across review outputs.
