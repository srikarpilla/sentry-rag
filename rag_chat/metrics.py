"""Information Retrieval (IR) and RAG performance metrics calculation.

Computes:
- Hit Rate @ K (Top-K Accuracy)
- Recall @ K
- Mean Reciprocal Rank (MRR)
- Normalized Discounted Cumulative Gain @ K (NDCG@K)
- Out-of-Scope Refusal Specificity
- Average Query Latency (ms)
"""
from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .rerank import BaseReranker
    from .retrieval import Chunk


def calculate_hit_rate(first_ranks: list[int | None], k: int) -> float:
    """Proportion of queries with at least one relevant passage in top K."""
    if not first_ranks:
        return 0.0
    hits = sum(1 for r in first_ranks if r is not None and r <= k)
    return hits / len(first_ranks)


def calculate_mrr(first_ranks: list[int | None]) -> float:
    """Mean Reciprocal Rank across queries."""
    if not first_ranks:
        return 0.0
    reciprocal_sum = sum(1.0 / r for r in first_ranks if r is not None and r > 0)
    return reciprocal_sum / len(first_ranks)


def calculate_ndcg(relevance_vectors: list[list[int]], k: int) -> float:
    """Normalized Discounted Cumulative Gain at rank K."""
    if not relevance_vectors:
        return 0.0
    ndcg_list = []
    for rels in relevance_vectors:
        top_k_rels = rels[:k]
        dcg = sum(r / math.log2(i + 2) for i, r in enumerate(top_k_rels))
        ideal_rels = sorted(top_k_rels, reverse=True)
        idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal_rels))
        if idcg > 0:
            ndcg_list.append(dcg / idcg)
        else:
            ndcg_list.append(0.0)
    return sum(ndcg_list) / len(ndcg_list)


def evaluate_retrieval(
    retriever: Any,
    eval_data: dict[str, Any],
    k_list: list[int] | None = None,
    reranker: BaseReranker | None = None,
    min_score: float = 0.25,
) -> dict[str, Any]:
    """Run full benchmark evaluation on eval_data containing in_scope and out_of_scope."""
    if k_list is None:
        k_list = [1, 3, 5]

    max_k = max(k_list)
    in_scope = eval_data.get("in_scope", [])
    out_scope = eval_data.get("out_of_scope", [])

    first_ranks: list[int | None] = []
    relevance_vectors: list[list[int]] = []
    recall_sums = {k: 0.0 for k in k_list}
    latencies: list[float] = []

    for item in in_scope:
        query = item["q"]
        expected_sources = item["sources"]

        t0 = time.perf_counter()
        # Retrieve candidate pool (3x max_k)
        candidate_count = max(max_k * 3, 15)
        candidates = retriever.search(query, candidate_count)

        if reranker is not None:
            results = reranker.rerank(query, candidates, top_k=max_k)
        else:
            results = candidates[:max_k]
        latencies.append((time.perf_counter() - t0) * 1000.0)

        # Relevance matching
        def is_rel(src: str) -> bool:
            return any(tag in src for tag in expected_sources) or (
                "paper" in query.lower() and (".pdf" in src or "90_sources" in src)
            )

        q_rel_vector: list[int] = []
        first_rel_rank: int | None = None

        for idx, (chunk, _) in enumerate(results):
            match = 1 if is_rel(chunk.source) else 0
            q_rel_vector.append(match)
            if match and first_rel_rank is None:
                first_rel_rank = idx + 1

        first_ranks.append(first_rel_rank)
        relevance_vectors.append(q_rel_vector)

        # Recall at each K
        for k in k_list:
            covered = sum(
                1
                for tag in expected_sources
                if any(tag in c.source for c, _ in results[:k])
            )
            recall_sums[k] += covered / max(len(expected_sources), 1)

    n_queries = max(len(in_scope), 1)
    hit_rates = {f"hit@{k}": round(calculate_hit_rate(first_ranks, k), 4) for k in k_list}
    recalls = {f"recall@{k}": round(recall_sums[k] / n_queries, 4) for k in k_list}
    mrr_score = round(calculate_mrr(first_ranks), 4)
    ndcg_scores = {f"ndcg@{k}": round(calculate_ndcg(relevance_vectors, k), 4) for k in [3, 5]}

    # Out of scope refusal testing
    refused_count = 0
    for q in out_scope:
        top_hit = retriever.search(q, 1)
        if not top_hit or top_hit[0][1] < min_score:
            refused_count += 1
    refusal_acc = round(refused_count / max(len(out_scope), 1), 4)
    avg_latency = round(sum(latencies) / max(len(latencies), 1), 2)

    return {
        "retriever": getattr(retriever, "name", "unknown"),
        "reranker": getattr(reranker, "name", "none") if reranker else "none",
        "total_queries": len(in_scope),
        "hit_rate": hit_rates,
        "recall": recalls,
        "mrr": mrr_score,
        "ndcg": ndcg_scores,
        "refusal_accuracy": refusal_acc,
        "avg_latency_ms": avg_latency,
    }


def format_metrics_table(results: list[dict[str, Any]]) -> str:
    """Format multiple evaluation results into a comparison table."""
    headers = [
        "System Configuration",
        "Hit@1",
        "Hit@3",
        "Recall@1",
        "Recall@3",
        "MRR",
        "NDCG@3",
        "Refusal Acc",
        "Latency",
    ]
    rows = []
    for r in results:
        config_name = f"{r['retriever']} + {r['reranker']}" if r['reranker'] != 'none' else r['retriever']
        rows.append([
            config_name,
            f"{r['hit_rate'].get('hit@1', 0.0) * 100:.1f}%",
            f"{r['hit_rate'].get('hit@3', 0.0) * 100:.1f}%",
            f"{r['recall'].get('recall@1', 0.0) * 100:.1f}%",
            f"{r['recall'].get('recall@3', 0.0) * 100:.1f}%",
            f"{r['mrr']:.3f}",
            f"{r['ndcg'].get('ndcg@3', 0.0):.3f}",
            f"{r['refusal_accuracy'] * 100:.1f}%",
            f"{r['avg_latency_ms']} ms",
        ])

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))

    def make_row(cols):
        return "| " + " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(cols)) + " |"

    sep = "|-" + "-|-".join("-" * col_widths[i] for i in range(len(headers))) + "-|"

    lines = [make_row(headers), sep]
    for row in rows:
        lines.append(make_row(row))
    return "\n".join(lines)
