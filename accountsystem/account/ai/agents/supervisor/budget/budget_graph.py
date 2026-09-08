"""Budget Workflow 组装：规则驱动 StateGraph。"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from account.ai.knowledge.tools import build_knowledge_tools
from account.ai.tools.finance_tools import build_budget_tools

from .budget_nodes import (
    context_prepare_node,
    make_budget_agent_node,
    make_budget_policy_check_node,
    make_intent_router_node,
    make_parameter_validator_node,
    make_response_generator_node,
    human_confirm_node,
)
from .budget_router import route_after_agent, route_after_policy, route_after_validator
from .budget_state import BudgetAgentState


def build_budget_graph(user):
    # 预算域工具 + 只读的内部知识库工具（预算规则查询）
    tools = [*build_budget_tools(user), *build_knowledge_tools()]
    tools_by_name = {t.name: t for t in tools}

    graph = StateGraph(BudgetAgentState)
    graph.add_node("context_prepare", context_prepare_node)
    graph.add_node("intent_router", make_intent_router_node())
    graph.add_node("parameter_validator", make_parameter_validator_node())
    graph.add_node("policy_check", make_budget_policy_check_node(tools_by_name))
    graph.add_node("human_confirm", human_confirm_node)
    graph.add_node("budget_agent", make_budget_agent_node(tools))
    graph.add_node("budget_tools", ToolNode(tools))
    graph.add_node("response_generator", make_response_generator_node())

    graph.add_edge(START, "context_prepare")
    graph.add_edge("context_prepare", "intent_router")
    graph.add_edge("intent_router", "parameter_validator")
    graph.add_conditional_edges(
        "parameter_validator",
        route_after_validator,
        {"policy_check": "policy_check", "end": END},
    )
    graph.add_conditional_edges(
        "policy_check",
        route_after_policy,
        {"budget_agent": "budget_agent", "human_confirm": "human_confirm", "end": END},
    )
    graph.add_edge("human_confirm", END)
    graph.add_conditional_edges(
        "budget_agent",
        route_after_agent,
        {"budget_tools": "budget_tools", "response_generator": "response_generator"},
    )
    graph.add_edge("budget_tools", "response_generator")
    graph.add_edge("response_generator", END)

    return graph.compile()
