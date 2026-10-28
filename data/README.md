# Offline Knowledge Base Documentation

This directory contains the verified offline knowledge base for the **Internship Task Review Assistant**. It enables full reference lookup, technical concept learning, and curriculum guidance even when no external internet or AI API connection is available.

---

## Dataset Schema

All knowledge files in this directory are UTF-8 encoded JSON with the following structure:

```json
{
  "topic": "<topic_name>",
  "description": "<overview_of_the_topic>",
  "items": [
    {
      "id": "<unique_id>",
      "topic": "<topic_name>",
      "question": "<technical_concept_or_question>",
      "answer": "<beginner_friendly_explanation>",
      "keywords": ["<keyword1>", "<keyword2>"],
      "difficulty": "beginner | intermediate | advanced",
      "example": "<code_snippet_or_command>",
      "source": "<canonical_documentation_or_spec>"
    }
  ]
}
```

---

## File Inventory

| File | Topic | Purpose | Count |
| :--- | :--- | :--- | :--- |
| `dataset_metadata.json` | `metadata` | Dataset version, creation date, disclaimer, and topic indices | 1 spec |
| `python_learning.json` | `python` | Python core, data structures, exceptions, context managers, OOP | 8 items |
| `web_development.json` | `web_development` | REST APIs, HTTP status codes, DOM, Flexbox/Grid, CORS, ORM | 8 items |
| `ai_ml_learning.json` | `ai_ml` | Machine learning paradigms, evaluation metrics, TF-IDF, embeddings | 7 items |
| `git_github.json` | `git_github` | Staging, merge conflict resolution, rebase, branch workflows | 7 items |
| `internship_tasks.json` | `internship_tasks` | Sample project tasks, deliverables, and evaluation rubrics (Examples only) | 5 items |
| `faq.json` | `faq` | Portal procedures, submission instructions, offline mode, email simulation | 7 items |

---

## How to Extend the Dataset

To add new technical topics or reference questions:

1. Open the relevant JSON file (or create a new `<topic>_learning.json`).
2. Add a new item object to the `"items"` array:
   - Provide a unique `"id"` (e.g. `py-009` or `git-008`).
   - Fill in `"topic"`, `"question"`, `"answer"`, `"keywords"`, and `"difficulty"`.
   - Optionally add `"example"`.
3. Validate your changes using the dataset validator:
   ```bash
   python scripts/validate_dataset.py
   ```
4. Run the automated test suite to ensure schema compliance:
   ```bash
   python -m pytest tests/test_dataset.py -v
   ```

No application code modifications are needed—the `OfflineKnowledgeService` automatically loads, tokenizes, and indexes any compliant JSON file in `data/`.

