# Sentry QC documentation assistant (RAG)

Answers questions about the Sentry QC model, its results and limits, and the MVTec AD dataset, using only the
markdown files in `rag_kb/`. Every answer shows the passages it came from. Questions the documents do not cover
are refused instead of guessed.

How it works: markdown files are split into passages by heading -> the question is matched against them (TF-IDF
with category routing and a coverage check) -> the best passages go to an LLM with strict "answer only from
these, cite them" rules -> answer + sources. With no LLM configured it returns the closest passages instead.

## Run it on your Windows desktop

1. Unzip the folder, e.g. to `C:\Users\Srikar\sentry_rag`, and open Command Prompt there:
   `cd C:\Users\Srikar\sentry_rag`
2. Make a separate environment (keeps it apart from TensorFlow) and install:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements-chat.txt
   ```
3. Check it works (no key, no internet needed):
   ```
   python eval_rag.py      # expect: In-scope retrieval 20/20, Out-of-scope refused 6/6
   pytest -q               # expect: 8 passed
   ```
4. Chat in the terminal: `python chat_cli.py`  (type `quit` to leave)
5. Chat in the browser: `uvicorn rag_chat.server:app --port 8001`, then open http://localhost:8001
   (port 8001 so it does not clash with the Sentry QC app on 8000).

## Get written answers (optional, pick one)

Without this the assistant shows the closest passages ("retrieval-only mode"). Set variables in the same
Command Prompt before starting the server or the CLI.

**A. Cohere API (Free Developer Key from dashboard.cohere.com):**
```
set LLM_PROVIDER=cohere
set COHERE_API_KEY=your-cohere-key-here
```
Or create a `.env` file in the folder with `COHERE_API_KEY=your-cohere-key-here` (auto-loaded).
Default model is `command-r-08-2024` (specifically optimized for RAG and citations).

**B. Anthropic API** (needs an API key from console.anthropic.com):
```
set LLM_PROVIDER=anthropic
set ANTHROPIC_API_KEY=your-key-here
```
Default model is `claude-haiku-4-5-20251001`; change it with `set ANTHROPIC_MODEL=...`.

**B. Free local model with Ollama:** install from https://ollama.com, then
```
ollama pull llama3.2
set LLM_PROVIDER=ollama
```
Local models are slower and follow the "cite and refuse" rules less reliably. Run `python eval_rag.py`
and ask a few off-topic questions to check.

PowerShell uses `$env:LLM_PROVIDER="ollama"` instead of `set`.

## Change what it knows
Edit or add `.md` files in `rag_kb/`, then restart. Use `##` headings, and make them read like the questions people
ask (for example "## Is it ready for real factory use?"): the heading text is searched too.
Run `per_category_report.py` (from the main project) to create `06_per_category_results.md`, and copy it into `rag_kb/`.

## Add it to your existing FastAPI app
```python
from rag_chat.server import router as chat_router
app.include_router(chat_router)          # adds POST /chat and GET /chat/health
```
Copy the `rag_chat/` and `rag_kb/` folders next to your app. `rag_chat/chat.html` is a ready chat page.

## Settings (environment variables)
| Variable | Default | Meaning |
|---|---|---|
| LLM_PROVIDER | none | none, anthropic or ollama |
| RETRIEVER | tfidf | `dense` uses sentence-transformers (extra install, downloads a model; not tested here) |
| MIN_SCORE / MIN_COVERAGE | 0.12 / 0.34 | how strict the "not in my documents" check is |
| KB_DIR | rag_kb | knowledge base folder |

## Known limits
- Keyword retrieval misses questions worded very differently from the documents. The `dense` retriever helps.
- Test it with your own questions: `tests/eval_set.json` was used while tuning, so its score is optimistic.
- It answers from the documents only. It does not see live predictions.
