"""Question in -> grounded answer + sources out."""
from __future__ import annotations

import os
import re
from pathlib import Path

from . import llm
from .retrieval import load_chunks, make_retriever

NOT_COVERED = ("I don't have that in my documents. I can answer questions about the Sentry QC model, "
               "its results and limits, the MVTec AD dataset, and its 15 product categories.")
DEFAULT_KB = Path(__file__).resolve().parent.parent / "rag_kb"


class RagService:
    def __init__(self, kb_dir=None, retriever_kind=None, min_score=None, top_k=4, use_rerank=None):
        self.chunks = load_chunks(kb_dir or os.getenv("KB_DIR", DEFAULT_KB))
        self.retriever = make_retriever(retriever_kind or os.getenv("RETRIEVER", "faiss"), self.chunks)
        env_min = os.getenv("MIN_SCORE")
        self.min_score = min_score if min_score is not None else float(env_min) if env_min else self.retriever.default_min_score
        self.top_k = top_k
        self.min_coverage = float(os.getenv("MIN_COVERAGE", getattr(self.retriever, "default_min_coverage", 0.0)))

        # Re-ranking configuration
        if use_rerank is not None:
            self.use_rerank = use_rerank
        else:
            self.use_rerank = os.getenv("USE_RERANK", "true").lower() in ("true", "1", "yes")
        from .rerank import get_reranker
        self.reranker = get_reranker() if self.use_rerank else None

    # ---- helpers
    def _retrieval_query(self, question, history):
        """Short follow-ups ('and for screws?') borrow the previous user question."""
        if history and len(question.split()) <= 5:
            prev = []
            for t in history:
                role = t.get("role") if isinstance(t, dict) else getattr(t, "role", None)
                content = t.get("content") if isinstance(t, dict) else getattr(t, "content", None)
                if role == "user" and content:
                    prev.append(content)
            if prev:
                last_q = prev[-1]
                from .retrieval import analyze
                q_terms = set(analyze(question))
                last_terms = set(analyze(last_q))
                cat_tokens_map = getattr(self.retriever, "cat_tokens", {})
                new_cats = [src for src, toks in cat_tokens_map.items() if toks & q_terms]
                old_cats = [src for src, toks in cat_tokens_map.items() if toks & last_terms]
                if new_cats and old_cats and new_cats != old_cats:
                    old_toks = set().union(*[cat_tokens_map[c] for c in old_cats])
                    filtered = " ".join(
                        w for w in last_q.split() if not (set(analyze(w)) & old_toks)
                    )
                    return f"{filtered} {question}".strip()
                return f"{last_q} {question}"
        return question

    @staticmethod
    def _source(n, chunk, score):
        return {"n": n, "source": chunk.source, "heading": chunk.heading, "score": round(score, 3)}

    # ---- main entry
    def ask(self, question: str, history=None, use_llm: bool = True) -> dict:
        question = question.strip()
        query = self._retrieval_query(question, history)

        fetch_k = max(self.top_k * 3, 12) if (self.use_rerank and self.reranker) else self.top_k
        candidates = self.retriever.search(query, fetch_k)

        if not candidates or candidates[0][1] < self.min_score:
            return {"answer": NOT_COVERED, "sources": [], "grounded": False, "mode": "refused"}

        # Re-ranking stage
        if self.use_rerank and self.reranker and candidates:
            hits = self.reranker.rerank(query, candidates, top_k=self.top_k)
        else:
            hits = candidates[:self.top_k]


        # Coverage check: for follow-ups, evaluate coverage against question and query to avoid false refusal from denominator dilution
        coverage_ok = True
        if hasattr(self.retriever, "coverage") and hits:
            cov_score = max(
                self.retriever.coverage(question, hits[0][0]),
                self.retriever.coverage(query, hits[0][0])
            )
            coverage_ok = cov_score >= self.min_coverage

        top_sc = round(hits[0][1], 3) if hits else None
        ret_name = getattr(self.retriever, "name", "faiss")
        rr_name = getattr(self.reranker, "name", "none") if (self.use_rerank and self.reranker) else "none"

        if not hits or hits[0][1] < self.min_score or not coverage_ok:
            return {
                "answer": NOT_COVERED,
                "sources": [],
                "grounded": False,
                "mode": "refused",
                "retriever": ret_name,
                "reranker": rr_name,
                "top_score": None,
            }

        if not use_llm or llm.provider() == "none":
            top = hits[:2]
            body = "\n\n".join(f"From {c.label}:\n{c.text}" for c, _ in top)
            return {
                "answer": body + "\n\n(Retrieval-only mode: these are the closest passages. "
                                  "Set LLM_PROVIDER to get written answers.)",
                "sources": [self._source(i + 1, c, s) for i, (c, s) in enumerate(top)],
                "grounded": True,
                "mode": "retrieval",
                "retriever": ret_name,
                "reranker": rr_name,
                "top_score": top_sc,
            }

        context = "\n\n".join(f"[{i + 1}] ({c.label})\n{c.text}" for i, (c, _) in enumerate(hits))
        earlier = ""
        if history:
            turns = []
            for t in history[-4:]:
                role = t.get("role") if isinstance(t, dict) else getattr(t, "role", None)
                content = t.get("content") if isinstance(t, dict) else getattr(t, "content", None)
                if role and content:
                    turns.append(f"{role}: {content}")
            if turns:
                earlier = "Earlier in this chat:\n" + "\n".join(turns) + "\n\n"

        user = f"Context passages:\n\n{context}\n\n{earlier}Question: {question}"
        answer = llm.generate(llm.SYSTEM_PROMPT, user) or NOT_COVERED

        clean_answer = answer.strip().strip('"\'').lower()
        if (clean_answer.startswith("i don't have that in my documents") or
                clean_answer.startswith("i do not have that in my documents") or
                "i don't have that in my documents" in clean_answer or
                "i do not have that in my documents" in clean_answer):
            return {
                "answer": NOT_COVERED,
                "sources": [],
                "grounded": False,
                "mode": "refused",
                "retriever": ret_name,
                "reranker": rr_name,
                "top_score": None,
            }

        cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", answer) if 1 <= int(n) <= len(hits)})
        shown = cited or list(range(1, len(hits) + 1))
        return {
            "answer": answer,
            "sources": [self._source(n, hits[n - 1][0], hits[n - 1][1]) for n in shown],
            "grounded": True,
            "mode": llm.provider(),
            "retriever": ret_name,
            "reranker": rr_name,
            "top_score": top_sc,
        }

