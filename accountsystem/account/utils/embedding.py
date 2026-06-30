from urllib.parse import urlparse, urlunparse

from config.dotenv_loader import env_str
from langchain_community.embeddings import DashScopeEmbeddings, OllamaEmbeddings


def _ollama_base_url_from_env() -> str:
    """
    Ollama 原生 API 根地址，例如 http://127.0.0.1:11434
    兼容用户把 LOCAL_EMBEDDING_BASE_URL 配成 OpenAI 兼容地址 .../v1 的情况。
    """
    raw = env_str("LOCAL_OLLAMA_BASE_URL")
    if not raw:
        raw = env_str("LOCAL_EMBEDDING_BASE_URL", "http://127.0.0.1:11434")
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
    runtime = env_str("EMBEDDING_RUNTIME").lower()
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
    provider = env_str("EMBEDDING_PROVIDER", "auto").lower()
    if provider == "auto":
        provider = "dashscope"
    print(f"[EMBEDDING_START] provider={provider}")

    if provider == "local":
        local_model = env_str("LOCAL_EMBEDDING_MODEL", "bge-m3")
        ollama_base = _ollama_base_url_from_env()
        print(
            f"[EMBEDDING_READY] provider=local(ollama) model={local_model} base_url={ollama_base}"
        )
        return OllamaEmbeddings(model=local_model, base_url=ollama_base)

    if provider == "dashscope":
        dashscope_api_key = env_str("DASHSCOPE_API_KEY")
        if not dashscope_api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY 未设置，请在 accountsystem/.env 中配置（可复制 .env.example）"
            )
        dashscope_model = env_str("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v2")
        print(
            f"[EMBEDDING_READY] provider=dashscope model={dashscope_model} "
            f"key_prefix={dashscope_api_key[:8]}..."
        )
        return DashScopeEmbeddings(
            model=dashscope_model,
            dashscope_api_key=dashscope_api_key,
        )

    raise ValueError(f"不支持的 EMBEDDING_PROVIDER: {provider}")
