"""Chat Workflow 条件边：只在有工具调用时进入 ToolNode，否则收尾。"""

from __future__ import annotations

from langchain_core.messages import AIMessage

from account.ai.llm.llm import AGENT_MAX_ITERATIONS

from .chat_state import ChatState


def route_after_agent(state: ChatState) -> str:
    """还有 tool_calls 且没打满轮次就去执行工具（search_finance_knowledge），否则收尾。"""
    messages = state.get("messages") or []
    last = messages[-1] if messages else None
    has_calls = isinstance(last, AIMessage) and bool(getattr(last, "tool_calls", None))
    if has_calls and int(state.get("loops") or 0) < AGENT_MAX_ITERATIONS:
        return "chat_tools"
    return "result_formatter"
