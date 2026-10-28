"""
scripts/validate_dataset.py — Standalone Dataset Validation Utility.
Validates all JSON files in data/ for UTF-8 encoding, valid JSON syntax,
and presence of required schema keys without modifying application code.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple


REQUIRED_ITEM_KEYS = {"id", "topic", "question", "answer", "keywords", "difficulty"}
EXPECTED_FILES = [
    "dataset_metadata.json",
    "python_learning.json",
    "web_development.json",
    "ai_ml_learning.json",
    "git_github.json",
    "internship_tasks.json",
    "faq.json"
]


def validate_metadata(data: Dict[str, Any], filepath: Path) -> List[str]:
    """Validate dataset_metadata.json structure."""
    errors = []
    for key in ["version", "created_at", "description", "disclaimer", "topics"]:
        if key not in data:
            errors.append(f"{filepath.name}: Missing required top-level key '{key}'")
    if not isinstance(data.get("topics"), list) or len(data.get("topics", [])) == 0:
        errors.append(f"{filepath.name}: 'topics' must be a non-empty list.")
    return errors


def validate_item_dataset(data: Dict[str, Any], filepath: Path) -> Tuple[List[str], int]:
    """Validate standard question-answer dataset files."""
    errors = []
    items = data.get("items")
    if not isinstance(items, list):
        errors.append(f"{filepath.name}: Root JSON must contain an 'items' array.")
        return errors, 0

    if len(items) == 0:
        errors.append(f"{filepath.name}: 'items' array is empty.")
        return errors, 0

    seen_ids = set()
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{filepath.name} item #{idx}: Must be a JSON object.")
            continue

        item_id = item.get("id")
        if not item_id:
            errors.append(f"{filepath.name} item #{idx}: Missing 'id'.")
        elif item_id in seen_ids:
            errors.append(f"{filepath.name} item #{idx}: Duplicate id '{item_id}'.")
        else:
            seen_ids.add(item_id)

        missing = REQUIRED_ITEM_KEYS - set(item.keys())
        if missing:
            errors.append(f"{filepath.name} item #{idx} ({item_id}): Missing required keys: {sorted(missing)}")

        if not isinstance(item.get("keywords"), list) or len(item.get("keywords", [])) == 0:
            errors.append(f"{filepath.name} item #{idx} ({item_id}): 'keywords' must be a non-empty list.")

        diff = item.get("difficulty")
        if diff not in {"beginner", "intermediate", "advanced"}:
            errors.append(f"{filepath.name} item #{idx} ({item_id}): Invalid difficulty '{diff}'. Must be beginner/intermediate/advanced.")

    return errors, len(items)


def run_validation(data_dir: Path) -> bool:
    """Run validation across all dataset files in data_dir."""
    print(f"Validating dataset in: {data_dir.resolve()}")
    if not data_dir.is_dir():
        print(f"Error: {data_dir} is not a directory.")
        return False

    all_errors: List[str] = []
    total_items = 0

    # 1. Check all expected files exist
    for fname in EXPECTED_FILES:
        fpath = data_dir / fname
        if not fpath.is_file():
            all_errors.append(f"Missing expected dataset file: {fname}")

    # 2. Validate individual files
    for jpath in sorted(data_dir.glob("*.json")):
        try:
            with open(jpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except UnicodeDecodeError as e:
            all_errors.append(f"{jpath.name}: UTF-8 decoding error: {e}")
            continue
        except json.JSONDecodeError as e:
            all_errors.append(f"{jpath.name}: Malformed JSON syntax: {e}")
            continue

        if jpath.name == "dataset_metadata.json":
            meta_errs = validate_metadata(data, jpath)
            all_errors.extend(meta_errs)
        else:
            item_errs, count = validate_item_dataset(data, jpath)
            all_errors.extend(item_errs)
            total_items += count

    if all_errors:
        print("\n[FAIL] Dataset validation FAILED with errors:")
        for err in all_errors:
            print(f"  * {err}")
        return False
    else:
        print(f"\n[PASS] Dataset validation PASSED: 7 files and {total_items} items successfully validated (UTF-8, schema compliant).")
        return True


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent / "data"
    success = run_validation(base)
    sys.exit(0 if success else 1)
