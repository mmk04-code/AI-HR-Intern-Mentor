"""
tests/test_dataset.py — Unit tests for offline JSON datasets.
Verifies file presence, UTF-8 encoding, schema compliance, and educational disclaimers.
"""

import json
from pathlib import Path
import pytest

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXPECTED_FILES = [
    "dataset_metadata.json",
    "python_learning.json",
    "web_development.json",
    "ai_ml_learning.json",
    "git_github.json",
    "internship_tasks.json",
    "faq.json"
]


def test_all_expected_dataset_files_exist():
    assert DATA_DIR.is_dir(), f"Data directory {DATA_DIR} does not exist."
    for fname in EXPECTED_FILES:
        fpath = DATA_DIR / fname
        assert fpath.is_file(), f"Missing dataset file: {fname}"


def test_metadata_file_schema():
    meta_path = DATA_DIR / "dataset_metadata.json"
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert "version" in meta
    assert "description" in meta
    assert "disclaimer" in meta
    assert "topics" in meta
    assert isinstance(meta["topics"], list)
    assert len(meta["topics"]) >= 5
    assert "example" in meta["disclaimer"].lower() or "reference" in meta["disclaimer"].lower()


@pytest.mark.parametrize("fname", [
    "python_learning.json",
    "web_development.json",
    "ai_ml_learning.json",
    "git_github.json",
    "internship_tasks.json",
    "faq.json"
])
def test_dataset_item_schema(fname):
    fpath = DATA_DIR / fname
    with open(fpath, "r", encoding="utf-8") as f:
        content = json.load(f)

    assert "items" in content, f"{fname} must contain top-level 'items' key."
    items = content["items"]
    assert isinstance(items, list)
    assert len(items) >= 4, f"{fname} must contain at least 4 items."

    seen_ids = set()
    for idx, item in enumerate(items):
        assert "id" in item, f"{fname} item #{idx} missing 'id'."
        assert item["id"] not in seen_ids, f"{fname} duplicate id '{item['id']}'."
        seen_ids.add(item["id"])

        for req in ["topic", "question", "answer", "keywords", "difficulty"]:
            assert req in item, f"{fname} item {item['id']} missing required key '{req}'."

        assert isinstance(item["keywords"], list)
        assert len(item["keywords"]) > 0
        assert item["difficulty"] in {"beginner", "intermediate", "advanced"}
        assert len(item["answer"]) > 20, f"{fname} item {item['id']} answer too short."


def test_sample_tasks_labeled_as_examples():
    tasks_path = DATA_DIR / "internship_tasks.json"
    with open(tasks_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    for task in items:
        q = task.get("question", "").lower()
        ans = task.get("answer", "").lower()
        src = task.get("source", "").lower()
        assert "sample" in q or "example" in q or "sample" in ans or "example" in src, (
            f"Task {task.get('id')} must be clearly labeled as an example or reference task."
        )

