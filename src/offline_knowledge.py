"""
src/offline_knowledge.py — Offline Knowledge Retrieval Service.
Implements TF-IDF vectorization and keyword scoring across local JSON datasets.
Operates completely offline without external APIs or network calls.
Explicitly labels local reference materials and never claims offline data is a live AI response.
"""

import json
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class OfflineKnowledgeService:
    """
    Offline retrieval service indexing local curated datasets in data/.
    Uses TF-IDF and keyword matching for fast, deterministic reference lookup.
    """

    NO_MATCH_MESSAGE = (
        "No relevant offline reference was found. Connect an available AI provider "
        "or add verified knowledge to the local dataset."
    )

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or (Path(__file__).resolve().parent.parent / "data")
        self.documents: List[Dict[str, Any]] = []
        self.idf: Dict[str, float] = {}
        self.doc_vectors: List[Dict[str, float]] = []
        self.loaded: bool = False
        self.load_dataset()

    def _tokenize(self, text: str) -> List[str]:
        """Convert input text into normalized alphanumeric word tokens."""
        return re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())

    def load_dataset(self) -> None:
        """Load and index all topic JSON files from data directory."""
        if not self.data_dir.is_dir():
            self.loaded = False
            return

        self.documents = []
        for jpath in sorted(self.data_dir.glob("*.json")):
            if jpath.name == "dataset_metadata.json":
                continue
            try:
                with open(jpath, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    items = content.get("items", []) if isinstance(content, dict) else content
                    for item in items:
                        if isinstance(item, dict):
                            doc_entry = dict(item)
                            doc_entry["source_file"] = jpath.name
                            self.documents.append(doc_entry)
            except Exception:
                continue

        if not self.documents:
            self.loaded = False
            return

        self._build_tfidf_index()
        self.loaded = True

    def _build_tfidf_index(self) -> None:
        """Build TF-IDF vocabulary, document frequencies, and document vectors."""
        num_docs = len(self.documents)
        df_counts: Dict[str, int] = {}
        doc_tf: List[Dict[str, float]] = []

        for doc in self.documents:
            corpus = (
                f"{doc.get('question', '')} {doc.get('answer', '')} "
                f"{' '.join(doc.get('keywords', []))} {doc.get('topic', '')}"
            )
            tokens = self._tokenize(corpus)
            tf: Dict[str, float] = {}
            total = len(tokens) or 1
            unique_tokens = set(tokens)

            for token in tokens:
                tf[token] = tf.get(token, 0.0) + (1.0 / total)

            for ut in unique_tokens:
                df_counts[ut] = df_counts.get(ut, 0) + 1

            doc_tf.append(tf)

        # Calculate IDF: smooth IDF = log((1 + N) / (1 + df)) + 1
        self.idf = {}
        for token, df in df_counts.items():
            self.idf[token] = math.log((1.0 + num_docs) / (1.0 + df)) + 1.0

        # Build normalized TF-IDF document vectors
        self.doc_vectors = []
        for tf in doc_tf:
            vec: Dict[str, float] = {}
            norm_sq = 0.0
            for term, val in tf.items():
                tfidf_val = val * self.idf.get(term, 1.0)
                vec[term] = tfidf_val
                norm_sq += tfidf_val * tfidf_val
            norm = math.sqrt(norm_sq) or 1.0
            for term in vec:
                vec[term] /= norm
            self.doc_vectors.append(vec)

    def search(
        self,
        query: str,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        max_results: int = 3,
        threshold: float = 0.08
    ) -> Dict[str, Any]:
        """
        Search local offline dataset for references relevant to user question.
        Returns matched records with source tags, or explicit no-match message.
        """
        if not self.loaded or not query or not query.strip():
            return {
                "found": False,
                "results": [],
                "message": self.NO_MATCH_MESSAGE,
                "is_offline_reference": True
            }

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return {
                "found": False,
                "results": [],
                "message": self.NO_MATCH_MESSAGE,
                "is_offline_reference": True
            }

        # Build query TF-IDF vector
        q_tf: Dict[str, float] = {}
        total_q = len(q_tokens)
        for t in q_tokens:
            q_tf[t] = q_tf.get(t, 0.0) + (1.0 / total_q)

        q_vec: Dict[str, float] = {}
        norm_sq = 0.0
        for t, val in q_tf.items():
            tfidf_val = val * self.idf.get(t, 1.0)
            q_vec[t] = tfidf_val
            norm_sq += tfidf_val * tfidf_val
        norm = math.sqrt(norm_sq) or 1.0
        for t in q_vec:
            q_vec[t] /= norm

        scored_docs: List[Tuple[float, Dict[str, Any]]] = []

        for idx, doc in enumerate(self.documents):
            # Apply optional topic and difficulty filters
            if topic and topic.lower() not in ("all", "any"):
                if doc.get("topic", "").lower() != topic.lower():
                    continue
            if difficulty and difficulty.lower() not in ("all", "any"):
                if doc.get("difficulty", "").lower() != difficulty.lower():
                    continue

            d_vec = self.doc_vectors[idx]

            # Cosine similarity dot product
            dot = sum(q_vec[t] * d_vec.get(t, 0.0) for t in q_vec)

            # Keyword matching bonus for high-precision matches
            kw_set = set(k.lower() for k in doc.get("keywords", []))
            matched_kws = set(q_tokens).intersection(kw_set)
            kw_bonus = 0.15 * len(matched_kws)

            # Title / question substring bonus
            question_lower = doc.get("question", "").lower()
            if any(qt in question_lower for qt in q_tokens):
                kw_bonus += 0.10

            final_score = dot + kw_bonus

            if final_score >= threshold:
                scored_docs.append((final_score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_matches = [doc for _, doc in scored_docs[:max_results]]

        if not top_matches:
            return {
                "found": False,
                "results": [],
                "message": self.NO_MATCH_MESSAGE,
                "is_offline_reference": True
            }

        return {
            "found": True,
            "results": top_matches,
            "count": len(top_matches),
            "message": f"Found {len(top_matches)} offline reference material(s).",
            "is_offline_reference": True
        }


# Singleton instance
_INSTANCE: Optional[OfflineKnowledgeService] = None

def get_offline_knowledge_service() -> OfflineKnowledgeService:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = OfflineKnowledgeService()
    return _INSTANCE

