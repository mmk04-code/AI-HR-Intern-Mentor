# Claude Code Instructions — Internship Task Review Assistant

## Project Architecture
- Stack: Python 3.14+, Streamlit, SQLite (`data/assistant.db`), Google Gemini API (`google-generativeai`).
- Entry point: `app.py`.
- Logic modules in `src/`:
  - `database.py`: SQLite initialization & CRUD.
  - `document_parser.py`: PDF, DOCX, TXT, MD parser.
  - `submission_reader.py`: ZIP extractor and GitHub API fetcher (zero code execution).
  - `ai_review.py`: Gemini AI client with multilingual deterministic fallback engine.
  - `review_service.py`: High-level workflow orchestration.
  - `email_service.py`: Real SMTP and safe simulation logger.

## Build and Test Commands
- Run tests: `python -m pytest tests/ -v`
- Run single test file: `python -m pytest tests/test_database.py -v`
- Launch app: `python -m streamlit run app.py`

## Coding Guidelines
- Maintain zero execution of untrusted candidate code.
- Always preserve revision numbers and historical submissions; never overwrite past reviews.
- Differentiate clearly between genuine Gemini AI review and Rule-Based Demo Results in UI.
- Simulated emails must always have status `SIMULATED — NOT SENT`.
- Keep `.env` and `data/*.db` out of git.
