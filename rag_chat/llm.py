"""LLM providers. Chosen with the LLM_PROVIDER environment variable.

  none       (default) no LLM: the app returns the best matching passages. Free, offline.
  cohere     free tier API key from https://cohere.com. Needs COHERE_API_KEY. Model: COHERE_MODEL (default command-r-08-2024)
  anthropic  needs ANTHROPIC_API_KEY. Model: ANTHROPIC_MODEL (default claude-haiku-4-5-20251001)
  ollama     local model through Ollama (https://ollama.com). Model: OLLAMA_MODEL (default llama3.2)
"""
from __future__ import annotations

import os
from pathlib import Path

import requests


def _load_dotenv() -> None:
    """Auto-load .env file from project root if present."""
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


_load_dotenv()

SYSTEM_PROMPT = """You are the documentation assistant for Sentry QC, an image classifier that labels industrial parts as good or defective.
Answer ONLY from the numbered context passages you are given.
Rules:
- Cite the passages you used with their numbers, like [1] or [2][3].
- Use only numbers and facts that appear in the passages. Never estimate or invent figures.
- If the passages do not contain the answer, reply exactly: I don't have that in my documents.
- Do not explain what causes defects or give manufacturing advice unless a passage does.
- Keep answers short and plain: 1 to 4 sentences, or a short list when the user asks for several items."""


def provider() -> str:
    p = os.getenv("LLM_PROVIDER")
    if p:
        return p.lower()
    if os.getenv("COHERE_API_KEY") or os.getenv("CO_API_KEY"):
        return "cohere"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "none"


def generate(system: str, user: str) -> str | None:
    """Returns the model's text, or None when no LLM is configured."""
    p = provider()
    if p == "none":
        return None

    if p == "cohere":
        key = os.getenv("COHERE_API_KEY") or os.getenv("CO_API_KEY")
        if not key:
            raise RuntimeError("LLM_PROVIDER=cohere but COHERE_API_KEY (or CO_API_KEY) is not set.")
        model = os.getenv("COHERE_MODEL", "command-r-08-2024")
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.0,
        }
        r = requests.post("https://api.cohere.com/v2/chat", headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            data = r.json()
            content = data.get("message", {}).get("content", [])
            if isinstance(content, list):
                return "".join(c.get("text", "") for c in content if isinstance(c, dict)).strip()
            if isinstance(content, str):
                return content.strip()
            return data.get("text", "").strip()

        # Fallback to v1 endpoint if needed
        v1_payload = {
            "model": model,
            "preamble": system,
            "message": user,
            "temperature": 0.0,
        }
        r1 = requests.post("https://api.cohere.com/v1/chat", headers=headers, json=v1_payload, timeout=60)
        r1.raise_for_status()
        return r1.json().get("text", "").strip()

    if p == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set.")
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"), "max_tokens": 500,
                  "temperature": 0, "system": system, "messages": [{"role": "user", "content": user}]},
            timeout=60,
        )
        r.raise_for_status()
        return "".join(b.get("text", "") for b in r.json()["content"]).strip()

    if p == "ollama":
        r = requests.post(
            os.getenv("OLLAMA_URL", "http://localhost:11434") + "/api/chat",
            json={"model": os.getenv("OLLAMA_MODEL", "llama3.2"), "stream": False, "options": {"temperature": 0},
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["message"]["content"].strip()

    raise RuntimeError(f"Unknown LLM_PROVIDER '{p}'. Use none, cohere, anthropic or ollama.")
