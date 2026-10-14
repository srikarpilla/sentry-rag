"""Check the assistant against tests/eval_set.json.

Calculates formal Information Retrieval (IR) and RAG performance metrics:
  - Hit Rate @ 1, 3, 5 (Top-K Accuracy)
  - Recall @ 1, 3, 5
  - Mean Reciprocal Rank (MRR)
  - Normalized Discounted Cumulative Gain (NDCG @ 3, 5)
  - Out-of-Scope Refusal Accuracy (Specificity)
  - Re-ranking vs. Dense Vector Retrieval comparison

Run:  python eval_rag.py          (add --verbose to see query-level details)
"""
import json
import os
import sys
from pathlib import Path

from rag_chat.metrics import evaluate_retrieval, format_metrics_table
from rag_chat.rerank import get_reranker
from rag_chat.retrieval import make_retriever
from rag_chat.service import RagService

verbose = "--verbose" in sys.argv or "-v" in sys.argv
data_path = Path(__file__).parent / "tests" / "eval_set.json"
data = json.loads(data_path.read_text(encoding="utf-8"))

svc = RagService()
print(f"=== Sentry QC RAG Performance Evaluation ===")
print(f"Retriever: {svc.retriever.name}  |  Passages: {len(svc.chunks)}  |  Min Score: {svc.min_score}\n")

# 1. Baseline: Dense FAISS Vector Search
dense_eval = evaluate_retrieval(
    svc.retriever, data, k_list=[1, 3, 5], reranker=None, min_score=svc.min_score
)

# 2. Re-ranked: FAISS + Reranker (Cohere or Hybrid RRF)
reranker = get_reranker()
rerank_eval = evaluate_retrieval(
    svc.retriever, data, k_list=[1, 3, 5], reranker=reranker, min_score=svc.min_score
)

# 3. Keyword Baseline: TF-IDF
tfidf_retriever = make_retriever("tfidf", svc.chunks)
tfidf_eval = evaluate_retrieval(
    tfidf_retriever, data, k_list=[1, 3, 5], reranker=None, min_score=0.12
)

# Print Comparison Table
table = format_metrics_table([dense_eval, rerank_eval, tfidf_eval])
print(table)
print()

# Query-level inspection if verbose
if verbose:
    print("\n--- Detailed Query Ranking (with Re-ranking) ---")
    for item in data["in_scope"]:
        candidates = svc.retriever.search(item["q"], 12)
        top = reranker.rerank(item["q"], candidates, top_k=3) if reranker else candidates[:3]
        ok = any(
            any(t in c.source for t in item["sources"])
            or ("paper" in item["q"].lower() and (".pdf" in c.source or "90_sources" in c.source))
            for c, _ in top
        )
        status = "PASS" if ok else "FAIL"
        top_name = f"{top[0][0].source} ({top[0][1]:.3f})" if top else "none"
        print(f"[{status}] {item['q']}\n       top: {top_name}")

# Standard regression exit code
hits_3 = dense_eval["hit_rate"]["hit@3"]
refusal = dense_eval["refusal_accuracy"]
sys.exit(0 if hits_3 >= 0.90 and refusal >= 0.90 else 1)
