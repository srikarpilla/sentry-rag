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
        "min_score": s.min_score,
        "llm_provider": llm.provider()
    }


app = FastAPI(title="Sentry QC documentation assistant")
app.include_router(router)


@app.get("/")
def home():
    index_file = Path(__file__).parent / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return FileResponse(Path(__file__).parent / "chat.html")
