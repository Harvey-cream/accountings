"""Node Parser：把 Document 切分为带元数据的 Node（元数据自动继承自 Document）。"""

from __future__ import annotations

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, Document

_CHUNK_SIZE = 512
_CHUNK_OVERLAP = 64


def build_node_parser(
    chunk_size: int = _CHUNK_SIZE, chunk_overlap: int = _CHUNK_OVERLAP
) -> SentenceSplitter:
    return SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def parse_nodes(
    documents: list[Document],
    chunk_size: int = _CHUNK_SIZE,
    chunk_overlap: int = _CHUNK_OVERLAP,
) -> list[BaseNode]:
    parser = build_node_parser(chunk_size, chunk_overlap)
    return parser.get_nodes_from_documents(documents)
