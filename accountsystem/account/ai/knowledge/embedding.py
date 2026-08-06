"""知识库 Embedding：统一走阿里云 DashScope 原生 SDK，本地与线上一致（不再使用本地 Ollama）。

只暴露底层 embed 函数；LlamaIndex 适配在 index/chroma_store.py 完成。
"""

from __future__ import annotations

from http import HTTPStatus

import dashscope

from config.dotenv_loader import env_str

# DashScope text-embedding 单批上限较小，保守取 10 条一批
_BATCH_SIZE = 10


def _api_key() -> str:
    key = env_str("DASHSCOPE_API_KEY")
    if not key:
        raise ValueError(
            "DASHSCOPE_API_KEY 未设置，请在 accountsystem/.env 中配置（可复制 .env.example）"
        )
    return key


def _model() -> str:
    return env_str("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v2")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量文本向量化，返回与输入等长、同序的向量列表。"""
    if not texts:
        return []
    api_key, model = _api_key(), _model()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), _BATCH_SIZE):
        batch = texts[start : start + _BATCH_SIZE]
        resp = dashscope.TextEmbedding.call(model=model, input=batch, api_key=api_key)
        if resp.status_code != HTTPStatus.OK:
            raise RuntimeError(
                f"DashScope embedding 失败：{resp.status_code} {getattr(resp, 'message', '')}"
            )
        ordered = sorted(resp.output["embeddings"], key=lambda e: e["text_index"])
        vectors.extend(item["embedding"] for item in ordered)
    return vectors


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
