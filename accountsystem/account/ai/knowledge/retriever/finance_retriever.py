"""财务知识 Retriever：从 Chroma 向量库检索内部知识片段。

对外仅提供 retrieve_finance_knowledge(query) -> [{text, metadata}]。
这是唯一直接使用 LlamaIndex 检索能力的地方；上层 Tool 只调用本函数，
Agent 不得直接 import llama_index。
"""

from __future__ import annotations

from llama_index.core import VectorStoreIndex

from account.ai.knowledge.index.chroma_store import get_embed_model, get_vector_store
from account.ai.llm.llm_utils import log_agent_exc

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
    if not q:
        return []
    try:
        retriever = _get_index().as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(q)
    except Exception as e:
        log_agent_exc("KNOWLEDGE", e, query=q[:40])
        return []

    results: list[dict] = []
    for n in nodes:
        meta = n.node.metadata or {}
        results.append(
            {
                "text": n.node.get_content(),
                "metadata": {
                    "category": meta.get("category"),
                    "source": meta.get("source"),
                    "document_type": meta.get("document_type"),
                    "score": round(float(n.score), 4) if n.score is not None else None,
                },
            }
        )
    return results


def prewarm_knowledge() -> None:
    """应用启动时预热向量索引，避免首个请求冷启动。"""
    try:
        _get_index()
        print("[PREWARM] finance knowledge index ready")
    except Exception as e:
        print(f"[PREWARM] knowledge skipped: {e}")
