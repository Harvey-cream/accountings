"""财务知识 Retriever：从 Chroma 向量库检索内部知识片段。

对外仅提供 retrieve_finance_knowledge(query) -> [{text, metadata}]。
这是唯一直接使用 LlamaIndex 检索能力的地方；上层 Tool 只调用本函数，
Agent 不得直接 import llama_index。
"""

from __future__ import annotations

from llama_index.core import VectorStoreIndex

from account.ai.knowledge.index.chroma_store import get_embed_model, get_vector_store
from account.ai.llm.llm_utils import log_agent_exc
from account.ai.observability import (
    mark_span_ok,
    record_exception,
    set_span_attribute,
    set_span_attributes,
    start_span,
)

_DEFAULT_TOP_K = 3
_index: VectorStoreIndex | None = None


def _get_index() -> VectorStoreIndex:
    global _index
    if _index is None:
        _index = VectorStoreIndex.from_vector_store(
            vector_store=get_vector_store(),
            embed_model=get_embed_model(),
        )
    return _index


def retrieve_finance_knowledge(query: str, top_k: int = _DEFAULT_TOP_K) -> list[dict]:
    """检索与 query 最相关的知识片段。失败或无结果时返回空列表。"""
    q = (query or "").strip()
    with start_span("rag.retrieve", {"rag.top_k": top_k}) as span:
        if not q:
            set_span_attributes(span, {"rag.result_count": 0, "rag.status": "completed"})
            mark_span_ok(span)
            return []
        try:
            retriever = _get_index().as_retriever(similarity_top_k=top_k)
            nodes = retriever.retrieve(q)
        except Exception as exc:
            set_span_attribute(span, "rag.status", "failed")
            record_exception(span, exc)
            log_agent_exc("KNOWLEDGE", exc, query=q[:40])
            return []

        results: list[dict] = []
        scores: list[float] = []
        for node in nodes:
            meta = node.node.metadata or {}
            score = round(float(node.score), 4) if node.score is not None else None
            if score is not None:
                scores.append(score)
            results.append(
                {
                    "text": node.node.get_content(),
                    "metadata": {
                        "category": meta.get("category"),
                        "source": meta.get("source"),
                        "document_type": meta.get("document_type"),
                        "score": score,
                    },
                }
            )
        set_span_attributes(
            span,
            {
                "rag.result_count": len(results),
                "rag.status": "completed",
                "rag.max_score": max(scores) if scores else None,
                "rag.min_score": min(scores) if scores else None,
            },
        )
        mark_span_ok(span)
        return results


def prewarm_knowledge() -> None:
    """应用启动时预热向量索引，避免首个请求冷启动。"""
    try:
        _get_index()
        print("[PREWARM] finance knowledge index ready")
    except Exception as e:
        print(f"[PREWARM] knowledge skipped: {e}")
