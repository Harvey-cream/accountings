"""Chat Workflow 组装：StateGraph 编排普通聊天 + 知识检索。

图结构与 bill 等业务域一致：入参 → 聊天 Agent → （可选）知识检索 Tool → 收尾。
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from account.ai.knowledge.tools.knowledge_tools import build_knowledge_tools

from .chat_nodes import (
    context_prepare_node,
    make_chat_agent_node,
    result_formatter_node,
)
from .chat_router import route_after_agent
from .chat_state import ChatState


def build_chat_graph(user=None):
    """聊天工作流：不绑定用户业务工具，只挂知识检索工具。"""
    tools = build_knowledge_tools()

    graph = StateGraph(ChatState)
    graph.add_node("context_prepare", context_prepare_node)
    graph.add_node("chat_agent", make_chat_agent_node(tools))
    graph.add_node("chat_tools", ToolNode(tools))
    graph.add_node("result_formatter", result_formatter_node)

    graph.add_edge(START, "context_prepare")
    graph.add_edge("context_prepare", "chat_agent")
    graph.add_conditional_edges(
        "chat_agent",
        route_after_agent,
        {"chat_tools": "chat_tools", "result_formatter": "result_formatter"},
    )
    graph.add_edge("chat_tools", "chat_agent")
    graph.add_edge("result_formatter", END)

    return graph.compile()
