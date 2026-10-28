"""
tests/test_offline_knowledge.py — Unit tests for OfflineKnowledgeService.
Verifies keyword and TF-IDF search, topic filtering, difficulty filtering,
and explicit no-match fallback behavior.
"""

import pytest
from src.offline_knowledge import OfflineKnowledgeService, get_offline_knowledge_service


@pytest.fixture
def service():
    return get_offline_knowledge_service()


def test_service_initialization(service):
    assert service.loaded is True
    assert len(service.documents) >= 30
    assert len(service.doc_vectors) == len(service.documents)
    assert len(service.idf) > 50


def test_search_git_merge_conflict(service):
    res = service.search("how do I resolve a git merge conflict?")
    assert res["found"] is True
    assert res["count"] >= 1
    assert res["is_offline_reference"] is True
    top_doc = res["results"][0]
    assert "conflict" in top_doc["question"].lower() or "merge" in top_doc["question"].lower()
    assert "source_file" in top_doc


def test_search_python_virtual_environment(service):
    res = service.search("what is a virtualenv venv in python?", topic="python")
    assert res["found"] is True
    top = res["results"][0]
    assert top["topic"] == "python"
    assert "venv" in top["keywords"] or "virtualenv" in top["keywords"]


def test_search_rest_api_status_codes(service):
    res = service.search("standard http response status codes", topic="web_development")
    assert res["found"] is True
    assert any("status code" in d["question"].lower() for d in res["results"])


def test_search_topic_filtering(service):
    # Searching python topic should not return git items
    res = service.search("list append extend", topic="python")
    assert res["found"] is True
    for d in res["results"]:
        assert d["topic"] == "python"


def test_search_difficulty_filtering(service):
    res = service.search("python", difficulty="beginner")
    if res["found"]:
        for d in res["results"]:
            assert d["difficulty"] == "beginner"


def test_search_no_match_behavior(service):
    res = service.search("xyzzy12345nonexistentconceptneverpresent")
    assert res["found"] is False
    assert len(res["results"]) == 0
    assert res["is_offline_reference"] is True
    assert "No relevant offline reference was found" in res["message"]


def test_search_empty_query(service):
    res = service.search("")
    assert res["found"] is False
    assert "No relevant offline reference was found" in res["message"]

