"""Asset Workflow 组装：StateGraph 编排资产域专属流程。"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from account.ai.tools.finance_tools import build_asset_tools

from .asset_nodes import (
    context_prepare_node,
    human_confirm_node,
    make_asset_agent_node,
    make_intent_router_node,
    make_mutation_check_node,
    result_formatter_node,
)
from .asset_router import route_after_agent, route_after_mutation_check, route_by_intent
from .asset_state import AssetAgentState


def build_asset_graph(user):
    """按用户构建资产工作流；工具在此处绑定用户，节点内不再感知 ORM。"""
    tools = build_asset_tools(user)
    tools_by_name = {t.name: t for t in tools}

    graph = StateGraph(AssetAgentState)
    graph.add_node("context_prepare", context_prepare_node)
    graph.add_node("intent_router", make_intent_router_node())
    graph.add_node("mutation_check", make_mutation_check_node(tools_by_name))
    graph.add_node("human_confirm", human_confirm_node)
    graph.add_node("asset_agent", make_asset_agent_node(tools))
    graph.add_node("asset_tools", ToolNode(tools))
    graph.add_node("result_formatter", result_formatter_node)

    graph.add_edge(START, "context_prepare")
    graph.add_edge("context_prepare", "intent_router")
    graph.add_conditional_edges(
        "intent_router",
        route_by_intent,
        {"asset_agent": "asset_agent", "mutation_check": "mutation_check"},
    )
    graph.add_conditional_edges(
        "mutation_check",
        route_after_mutation_check,
        {
            "human_confirm": "human_confirm",
            "asset_agent": "asset_agent",
            "result_formatter": "result_formatter",
        },
    )
    graph.add_edge("human_confirm", "result_formatter")
    graph.add_conditional_edges(
        "asset_agent",
        route_after_agent,
        {"asset_tools": "asset_tools", "result_formatter": "result_formatter"},
    )
    graph.add_edge("asset_tools", "asset_agent")
    graph.add_edge("result_formatter", END)

    return graph.compile()
