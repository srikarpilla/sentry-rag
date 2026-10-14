"""FastAPI app. Run:  uvicorn rag_chat.server:app --port 8001
To add the chatbot to an existing FastAPI app instead:
    from rag_chat.server import router as chat_router
    app.include_router(chat_router)
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import llm
from .service import RagService

router = APIRouter()


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    history: list[Turn] = Field(default_factory=list)


class Source(BaseModel):
    n: int
    source: str
    heading: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    grounded: bool
    mode: str
    retriever: str | None = None
    reranker: str | None = None
    top_score: float | None = None


@lru_cache(maxsize=1)
def get_service() -> RagService:
    return RagService()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = [(t.model_dump() if hasattr(t, "model_dump") else t.dict()) for t in req.history[-12:]]
    return get_service().ask(req.question, history)


@router.get("/chat/health")
def chat_health():
    s = get_service()
    files = sorted({c.source for c in s.chunks})
    return {
        "status": "ok",
        "chunks": len(s.chunks),
        "files_count": len(files),
        "files": files,
        "retriever": s.retriever.name,
        "reranker": s.reranker.name if (s.use_rerank and s.reranker) else "none",
        "min_score": s.min_score,
        "llm_provider": llm.provider(),
    }


_cached_metrics = None


@router.get("/chat/metrics")
def chat_metrics(refresh: bool = False):
    global _cached_metrics
    if _cached_metrics and not refresh:
        return _cached_metrics

    import json
    from .metrics import evaluate_retrieval
    from .retrieval import make_retriever

    s = get_service()
    eval_file = Path(__file__).resolve().parent.parent / "tests" / "eval_set.json"
    if not eval_file.is_file():
        return {"status": "error", "message": "eval_set.json not found"}
    eval_data = json.loads(eval_file.read_text(encoding="utf-8"))

    dense = evaluate_retrieval(s.retriever, eval_data, reranker=None, min_score=s.min_score)
    reranked = (
        evaluate_retrieval(s.retriever, eval_data, reranker=s.reranker, min_score=s.min_score)
        if s.reranker
        else None
    )
    tfidf_retriever = make_retriever("tfidf", s.chunks)
    tfidf = evaluate_retrieval(tfidf_retriever, eval_data, reranker=None, min_score=0.12)

    _cached_metrics = {
        "status": "ok",
        "dense_faiss": dense,
        "reranked": reranked,
        "tfidf": tfidf,
    }
    return _cached_metrics


app = FastAPI(title="Sentry QC documentation assistant")
app.include_router(router)


@app.get("/")
def home():
    index_file = Path(__file__).parent / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return FileResponse(Path(__file__).parent / "chat.html")
