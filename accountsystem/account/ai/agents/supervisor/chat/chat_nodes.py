"""Chat Workflow 节点实现。节点只调 LLM / 知识检索工具，不碰 ORM。"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import extract_content

from .chat_prompt import CHAT_SYSTEM
from .chat_state import ChatState


# ----- 1. context_prepare -----


def context_prepare_node(state: ChatState) -> dict:
    """把本轮要回复的原话追加为 HumanMessage。"""
    text = (state.get("input") or "").strip()
    return {"messages": [HumanMessage(content=text)], "loops": 0}


# ----- 2. chat_agent -----


def make_chat_agent_node(tools, model=llm):
    """普通聊天 Agent：只暴露 search_finance_knowledge，无任何业务工具。"""
    agent_llm = model.bind_tools(tools)

    def chat_agent_node(state: ChatState) -> dict:
        system = SystemMessage(content=CHAT_SYSTEM)
        reply = agent_llm.invoke([system, *(state.get("messages") or [])])
        return {"messages": [reply], "loops": int(state.get("loops") or 0) + 1}

    return chat_agent_node


# ----- 3. result_formatter -----


def result_formatter_node(state: ChatState) -> dict:
    """统一出参 {success, message, data}，messages 保留给 _graph_to_result 抽取工具步骤。"""
    if state.get("result"):
        return {}
    messages = state.get("messages") or []
    text = extract_content(messages[-1]).strip() if messages else ""
    return {
        "result": {
            "success": True,
            "message": text,
            "data": {},
        }
    }
