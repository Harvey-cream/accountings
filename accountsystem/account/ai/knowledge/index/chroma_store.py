"""Chroma 向量库封装：持久化客户端、集合、StorageContext 与 Embedding 模型。

Embedding 复用项目统一的 DashScope 客户端（account.ai.knowledge.embedding.build_embeddings），
通过薄适配器接入 LlamaIndex，保证本地与线上使用同一套阿里云向量模型。
"""

from __future__ import annotations

import os

import chromadb
from llama_index.core import StorageContext
from llama_index.core.embeddings import BaseEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from account.ai.knowledge.embedding import embed_query, embed_texts
from config.dotenv_loader import env_str

COLLECTION_NAME = "finance_knowledge"
_EMBED_BATCH_SIZE = 10

_client = None


class _DashScopeEmbedding(BaseEmbedding):
    """把 DashScope 原生 embedding 适配成 LlamaIndex BaseEmbedding。

    只暴露给 index / ingestion / retriever 层，Agent 与 Tool 层不感知 LlamaIndex。
    """

    @classmethod
    def class_name(cls) -> str:
        return "dashscope_embedding"

    def _get_query_embedding(self, query: str) -> list[float]:
        return embed_query(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return embed_texts([text])[0]

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return embed_texts(list(texts))

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> list[float]:
        return self._get_text_embedding(text)


def get_persist_dir() -> str:
    """向量库持久化目录，默认 knowledge/chroma_db，可用 KNOWLEDGE_CHROMA_DIR 覆盖。"""
    root = env_str("KNOWLEDGE_CHROMA_DIR")
    if not root:
        here = os.path.dirname(os.path.abspath(__file__))  # .../knowledge/index
        root = os.path.join(os.path.dirname(here), "chroma_db")  # .../knowledge/chroma_db
    os.makedirs(root, exist_ok=True)
    return root


def _get_client() -> "chromadb.api.ClientAPI":
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=get_persist_dir())
    return _client


def get_chroma_collection():
    return _get_client().get_or_create_collection(COLLECTION_NAME)


def reset_collection() -> None:
    """清空并重建集合，用于离线重建索引时保证幂等。"""
    client = _get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    client.get_or_create_collection(COLLECTION_NAME)


def get_vector_store() -> ChromaVectorStore:
    return ChromaVectorStore(chroma_collection=get_chroma_collection())


def get_storage_context() -> StorageContext:
    return StorageContext.from_defaults(vector_store=get_vector_store())


def get_embed_model() -> BaseEmbedding:
    return _DashScopeEmbedding(embed_batch_size=_EMBED_BATCH_SIZE)
