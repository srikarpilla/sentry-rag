"""Re-ranking module for Sentry QC RAG pipeline.

Supports:
1. Cohere Rerank API (v3.5) when COHERE_API_KEY is available (state-of-the-art semantic cross-encoder).
2. Local Reciprocal Rank Fusion (RRF) & hybrid scoring fallback when running fully offline.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from .retrieval import Chunk


def _load_dotenv_if_needed():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip("'\"")
            if k not in os.environ:
                os.environ[k] = v


_load_dotenv_if_needed()


class BaseReranker:
    name: str = "base"

    def rerank(
        self, query: str, candidates: list[tuple[Chunk, float]], top_k: int = 4
    ) -> list[tuple[Chunk, float]]:
        raise NotImplementedError


class CohereReranker(BaseReranker):
    name = "cohere"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("COHERE_API_KEY") or os.getenv("CO_API_KEY")
        self.model = model or os.getenv("COHERE_RERANK_MODEL", "rerank-v3.5")

    def rerank(
        self, query: str, candidates: list[tuple[Chunk, float]], top_k: int = 4
    ) -> list[tuple[Chunk, float]]:
        if not self.api_key or not candidates:
            return candidates[:top_k]

        doc_texts = [f"{c.title}. {c.heading}. {c.text}" for c, _ in candidates]
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "model": self.model,
            "query": query,
            "documents": doc_texts,
            "top_n": min(len(candidates), top_k),
        }

        try:
            r = requests.post(
                "https://api.cohere.com/v2/rerank",
                headers=headers,
                json=payload,
                timeout=15,
            )
            if r.status_code == 200:
                results = r.json().get("results", [])
                reranked = []
                for item in results:
                    idx = int(item["index"])
                    score = float(item["relevance_score"])
                    reranked.append((candidates[idx][0], score))
                return reranked
        except Exception:
            pass

        # Fallback to candidate list
        return candidates[:top_k]


class HybridRRFReranker(BaseReranker):
    """Offline Reciprocal Rank Fusion (RRF) combining vector rank and lexical term overlap."""
    name = "hybrid_rrf"

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k

    def rerank(
        self, query: str, candidates: list[tuple[Chunk, float]], top_k: int = 4
    ) -> list[tuple[Chunk, float]]:
        if not candidates:
            return []

        from .retrieval import analyze

        qterms = set(analyze(query))
        scored = []

        # RRF calculation
        for rank_dense, (c, dense_score) in enumerate(candidates):
            c_terms = set(analyze(c.search_text))
            lex_overlap = len(qterms & c_terms) / max(len(qterms), 1)

            # Reciprocal rank score + lexical boost
            rrf_score = (1.0 / (self.rrf_k + rank_dense + 1)) + (0.015 * lex_overlap)
            combined_score = (0.7 * float(dense_score)) + (0.3 * float(lex_overlap))
            scored.append((c, combined_score, rrf_score))

        scored.sort(key=lambda x: (x[2], x[1]), reverse=True)
        return [(c, s) for c, s, _ in scored[:top_k]]


def get_reranker(kind: str | None = None) -> BaseReranker:
    kind = kind or os.getenv("RERANKER")
    if not kind:
        if os.getenv("COHERE_API_KEY") or os.getenv("CO_API_KEY"):
            kind = "cohere"
        else:
            kind = "hybrid_rrf"

    if kind.lower() == "cohere":
        return CohereReranker()
    return HybridRRFReranker()
