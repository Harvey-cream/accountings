"""内部财务知识库（RAG）。

分层（仅 ingestion / index / retriever 接触 LlamaIndex）：
  data/finance_rules/   知识源文档（md/txt/pdf）
  ingestion/            离线入库 Pipeline：loader -> parser -> build_index
  index/                Chroma 向量库与 Embedding 适配
  retriever/            检索封装 retrieve_finance_knowledge
  tools/                LangChain Tool search_finance_knowledge（供 Agent 使用）
"""

from account.ai.knowledge.retriever import prewarm_knowledge

__all__ = ["prewarm_knowledge"]
