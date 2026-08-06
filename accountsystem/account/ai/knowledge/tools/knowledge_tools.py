"""知识库 LangChain Tool：search_finance_knowledge。

Tool 内部只调用 retriever（retrieve_finance_knowledge），不接触 LlamaIndex，
返回与财务 Tools 一致的 {success, data, message} JSON 字符串，供 LLM 阅读。
"""

from __future__ import annotations

import json

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from account.ai.knowledge.retriever.finance_retriever import retrieve_finance_knowledge


class SearchFinanceKnowledgeInput(BaseModel):
    query: str = Field(
        ..., description="要检索的财务知识问题，如 预算超支怎么办、餐饮消费如何优化、记账分类标准"
    )
    top_k: int = Field(default=3, ge=1, le=5, description="返回的知识片段数量，默认 3")


def _search_finance_knowledge(query: str, top_k: int = 3) -> str:
    items = retrieve_finance_knowledge(query, top_k=top_k)
    message = "检索成功" if items else "未检索到相关知识"
    return json.dumps(
        {"success": True, "data": items, "message": message},
        ensure_ascii=False,
        default=str,
    )


def search_finance_knowledge_tool() -> StructuredTool:
    return StructuredTool.from_function(
        func=_search_finance_knowledge,
        name="search_finance_knowledge",
        description=(
            "检索系统内部财务知识库（预算规则、消费优化建议、记账规范）。"
            "当需要给出预算规则依据或消费分析建议时调用，作为回复的专业支撑。"
        ),
        args_schema=SearchFinanceKnowledgeInput,
    )


def build_knowledge_tools() -> list[StructuredTool]:
    return [search_finance_knowledge_tool()]
