"""离线知识入库 Pipeline 入口。

流程：Document Loader -> Node Parser -> Metadata -> Embedding -> Chroma Vector Index。
运行（在 accountsystem 目录下）：
    python -m account.ai.knowledge.ingestion.build_index
"""

from __future__ import annotations

from llama_index.core import VectorStoreIndex

from account.ai.knowledge.index.chroma_store import (
    get_embed_model,
    get_persist_dir,
    get_storage_context,
    reset_collection,
)

from .loader import load_finance_documents
from .parser import parse_nodes


def build_index(rebuild: bool = True) -> dict:
    """构建（或重建）财务知识向量索引，返回入库统计。"""
    documents = load_finance_documents()
    if not documents:
        raise RuntimeError("未加载到任何知识文档，请检查 data/finance_rules 目录。")

    nodes = parse_nodes(documents)

    if rebuild:
        reset_collection()

    VectorStoreIndex(
        nodes,
        storage_context=get_storage_context(),
        embed_model=get_embed_model(),
        show_progress=True,
    )

    return {
        "documents": len(documents),
        "nodes": len(nodes),
        "persist_dir": get_persist_dir(),
    }


def main() -> None:
    stats = build_index(rebuild=True)
    print(
        f"[KNOWLEDGE] 入库完成：documents={stats['documents']} "
        f"nodes={stats['nodes']} dir={stats['persist_dir']}"
    )


if __name__ == "__main__":
    main()
