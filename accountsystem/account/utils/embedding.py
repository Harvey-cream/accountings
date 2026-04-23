import os
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv
from langchain_community.embeddings import DashScopeEmbeddings, OllamaEmbeddings

# 私有仓库可写默认 Key；环境变量 DASHSCOPE_API_KEY 优先。
_DEFAULT_DASHSCOPE_API_KEY = "sk-4e2f0a91dd2a4f36b7be88ffdcc0b294"

load_dotenv()


def _ollama_base_url_from_env() -> str:
    """
    Ollama 原生 API 根地址，例如 http://127.0.0.1:11434
    兼容用户把 LOCAL_EMBEDDING_BASE_URL 配成 OpenAI 兼容地址 .../v1 的情况。
    """
    raw = os.getenv("LOCAL_OLLAMA_BASE_URL", "").strip()
    if not raw:
        raw = os.getenv("LOCAL_EMBEDDING_BASE_URL", "http://127.0.0.1:11434").strip()
    parsed = urlparse(raw)
    path = (parsed.path or "").rstrip("/")
    if path.endswith("/v1"):
        path = path[: -len("/v1")]
    new_parsed = parsed._replace(path=path or "", params="", query="", fragment="")
    return urlunparse(new_parsed).rstrip("/")


def _is_local_env() -> bool:
    """
    判定本地环境：
    - 优先使用 EMBEDDING_RUNTIME=local|prod
    - 未设置时，回退到 Django DEBUG
    """
    runtime = os.getenv("EMBEDDING_RUNTIME", "").strip().lower()
    if runtime in {"local", "dev", "development"}:
        return True
    if runtime in {"prod", "production", "online"}:
        return False

    try:
        from django.conf import settings

        return bool(getattr(settings, "DEBUG", False))
    except Exception:
        return True


def build_embeddings():
    """
    统一构建 Embedding 客户端：
    - auto: 默认走通义（DashScope，用 DASHSCOPE_API_KEY）；需要本地 Ollama 时设 EMBEDDING_PROVIDER=local
    - local: 走本地 Ollama embedding
    - dashscope: 走通义 embedding（独立 key）
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "auto").strip().lower()
    if provider == "auto":
        # 先统一用 key，避免本机未装/未拉 Ollama 模型导致 skill 向量失败
        provider = "dashscope"
    print(f"[EMBEDDING_START] provider={provider}")

    if provider == "local":
        local_model = os.getenv("LOCAL_EMBEDDING_MODEL", "bge-m3").strip()
        ollama_base = _ollama_base_url_from_env()
        print(
            f"[EMBEDDING_READY] provider=local(ollama) model={local_model} base_url={ollama_base}"
        )
        return OllamaEmbeddings(model=local_model, base_url=ollama_base)

    if provider == "dashscope":
        dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", _DEFAULT_DASHSCOPE_API_KEY).strip()
        dashscope_model = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v2").strip()
        print(
            f"[EMBEDDING_READY] provider=dashscope model={dashscope_model} "
            f"key_prefix={dashscope_api_key[:8] if dashscope_api_key else 'empty'}"
        )
        return DashScopeEmbeddings(
            model=dashscope_model,
            dashscope_api_key=dashscope_api_key,
        )

    raise ValueError(f"不支持的 EMBEDDING_PROVIDER: {provider}")
