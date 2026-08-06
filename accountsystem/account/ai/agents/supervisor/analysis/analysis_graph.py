"""Analysis Workflow 组装：StateGraph 编排分析域流程。"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from account.ai.tools.finance_tools import build_analysis_tools

from .analysis_nodes import (
    context_prepare_node,
    make_analysis_agent_node,
    make_insight_generate_node,
    make_intent_router_node,
    make_parameter_normalize_node,
)
from .analysis_router import route_after_agent, route_after_params
from .analysis_state import AnalysisAgentState


def build_analysis_graph(user):
    """按用户构建分析工作流；工具在此处绑定用户。"""
    tools = build_analysis_tools(user)

    graph = StateGraph(AnalysisAgentState)
    graph.add_node("context_prepare", context_prepare_node)
    graph.add_node("intent_router", make_intent_router_node())
    graph.add_node("parameter_normalize", make_parameter_normalize_node())
    graph.add_node("analysis_agent", make_analysis_agent_node(tools))
    graph.add_node("analysis_tools", ToolNode(tools))
    graph.add_node("insight_generate", make_insight_generate_node())

    graph.add_edge(START, "context_prepare")
    graph.add_edge("context_prepare", "intent_router")
    graph.add_edge("intent_router", "parameter_normalize")
    graph.add_conditional_edges(
        "parameter_normalize",
        route_after_params,
        {"analysis_agent": "analysis_agent", "end": END},
    )
    graph.add_conditional_edges(
        "analysis_agent",
        route_after_agent,
        {"analysis_tools": "analysis_tools", "insight_generate": "insight_generate"},
    )
    graph.add_edge("analysis_tools", "insight_generate")
    graph.add_edge("insight_generate", END)

    return graph.compile()
