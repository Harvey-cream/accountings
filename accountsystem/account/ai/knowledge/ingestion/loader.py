"""Document Loader：读取 finance_rules 下的 md/txt/pdf，构建带元数据的 LlamaIndex Document。

Metadata 统一为 {category, source, document_type}：
- category：知识主题，取文件名（budget / consumption / accounting）
- source：来源文件名
- document_type：文档类型，第一阶段固定为 finance_rule
"""

from __future__ import annotations

import os

from llama_index.core import Document

_DATA_DIRNAME = "finance_rules"
_DOCUMENT_TYPE = "finance_rule"
_SUPPORTED_EXT = {".md", ".txt", ".pdf"}


def get_data_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))  # .../knowledge/ingestion
    return os.path.join(os.path.dirname(here), "data", _DATA_DIRNAME)


def _read_pdf(path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _read_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return _read_pdf(path)
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_finance_documents(data_dir: str | None = None) -> list[Document]:
    """加载知识目录下所有受支持文档；空文件与不支持的类型跳过。"""
    data_dir = data_dir or get_data_dir()
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"知识库目录不存在：{data_dir}")

    documents: list[Document] = []
    for name in sorted(os.listdir(data_dir)):
        path = os.path.join(data_dir, name)
        ext = os.path.splitext(name)[1].lower()
        if not os.path.isfile(path) or ext not in _SUPPORTED_EXT:
            continue
        text = (_read_text(path) or "").strip()
        if not text:
            continue
        category = os.path.splitext(name)[0]
        documents.append(
            Document(
                text=text,
                metadata={
                    "category": category,
                    "source": name,
                    "document_type": _DOCUMENT_TYPE,
                },
            )
        )
    return documents
