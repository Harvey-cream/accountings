import os

from config.dotenv_loader import env_str
from langchain_community.vectorstores import Chroma


def get_chroma_persist_root() -> str:
    root = env_str("CHROMA_PERSIST_DIR")
    if root:
        os.makedirs(root, exist_ok=True)
        return root
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.join(here, "chroma_data")
    os.makedirs(root, exist_ok=True)
    return root


def _has_persisted_collection(persist_dir: str) -> bool:
    if not os.path.isdir(persist_dir):
        return False
    return any(name.endswith(".sqlite3") for name in os.listdir(persist_dir))


def build_chroma_from_documents(
    collection_name: str,
    documents,
    embedding,
):
    """持久化向量库；磁盘已有 collection 时直接加载，避免每次启动重复 embed。"""
    persist = os.path.join(get_chroma_persist_root(), collection_name)
    os.makedirs(persist, exist_ok=True)
    if _has_persisted_collection(persist):
        try:
            return Chroma(
                collection_name=collection_name,
                embedding_function=embedding,
                persist_directory=persist,
            )
        except Exception as e:
            print(f"[CHROMA] load {collection_name!r} failed, rebuilding: {e}")
    return Chroma.from_documents(
        documents=documents,
        embedding=embedding,
        collection_name=collection_name,
        persist_directory=persist,
    )
