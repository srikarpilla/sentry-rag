"""Run:  pytest -q     (no API key or internet needed; the LLM is mocked)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from rag_chat import llm
from rag_chat.service import NOT_COVERED, RagService


@pytest.fixture(scope="module")
def svc():
    return RagService()


@pytest.fixture(autouse=True)
def no_llm_by_default(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")


def test_in_scope_question_returns_sources(svc):
    r = svc.ask("What is the balanced accuracy on the test set?")
    assert r["grounded"] and r["sources"]
    assert any("02_model_card" in s["source"] for s in r["sources"])


def test_out_of_scope_is_refused(svc):
    r = svc.ask("What is the capital of France?")
    assert r["answer"] == NOT_COVERED and not r["grounded"] and r["sources"] == []


def test_category_question_routes_to_that_category(svc):
    r = svc.ask("Which defects can a metal nut have?")
    assert r["sources"][0]["source"] == "categories/08_metal_nut.md"


def test_generic_defect_question_does_not_return_a_random_category(svc):
    r = svc.ask("Does the model tell me which defect type it found?")
    assert not r["sources"][0]["source"].startswith("categories/")


def test_followup_uses_previous_question(svc):
    hist = [{"role": "user", "content": "What defect types exist for screws?"}, {"role": "assistant", "content": "..."}]
    r = svc.ask("and zippers?", hist)
    assert r["grounded"] and "zipper" in r["sources"][0]["source"]


def test_llm_answer_keeps_only_cited_sources(svc, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    seen = {}

    def fake(system, user):
        seen["user"] = user
        return "Test balanced accuracy is 95.0% [1]."

    monkeypatch.setattr(llm, "generate", fake)
    r = svc.ask("What is the balanced accuracy on the test set?")
    assert r["mode"] == "anthropic" and [s["n"] for s in r["sources"]] == [1]
    assert "Context passages:" in seen["user"] and "[1]" in seen["user"]


def test_llm_refusal_phrase_becomes_standard_refusal(svc, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setattr(llm, "generate", lambda s, u: "I don't have that in my documents.")
    r = svc.ask("What causes scratches on a screw?")
    assert not r["grounded"] and r["answer"] == NOT_COVERED


def test_cohere_llm_provider(svc, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "cohere")
    monkeypatch.setattr(llm, "generate", lambda s, u: "The MVTec AD dataset has 15 categories [1].")
    r = svc.ask("What is the dataset?")
    assert r["mode"] == "cohere" and r["grounded"] and len(r["sources"]) == 1



def test_api_endpoint():
    try:
        import httpx2  # noqa: F401  (newer Starlette versions prefer this)
    except ModuleNotFoundError:
        pytest.importorskip("httpx", reason="pip install httpx to run the API test")
    from fastapi.testclient import TestClient
    from rag_chat.server import app
    c = TestClient(app)
    assert c.get("/chat/health").json()["chunks"] > 50
    ok = c.post("/chat", json={"question": "What threshold does the model use?"})
    assert ok.status_code == 200 and ok.json()["sources"]
    assert c.post("/chat", json={"question": ""}).status_code == 422
    assert c.get("/").status_code == 200
