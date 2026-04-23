import os

from langchain_community.vectorstores import Chroma


def get_chroma_persist_root() -> str:
    root = os.getenv("CHROMA_PERSIST_DIR", "").strip()
    if root:
        os.makedirs(root, exist_ok=True)
        return root
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.join(here, "chroma_data")
    os.makedirs(root, exist_ok=True)
    return root


def build_chroma_from_documents(
    collection_name: str,
    documents,
    embedding,
):
    """
    持久化到磁盘的小封装；每个 collection 独立子目录，避免和别的集合冲突。
    """
    persist = os.path.join(get_chroma_persist_root(), collection_name)
    os.makedirs(persist, exist_ok=True)
    return Chroma.from_documents(
        documents=documents,
        embedding=embedding,
        collection_name=collection_name,
        persist_directory=persist,
    )
