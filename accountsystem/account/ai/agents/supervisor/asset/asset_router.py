"""Asset Workflow 条件边：只做分支判断，不产生副作用。"""

from __future__ import annotations

from langchain_core.messages import AIMessage

from account.ai.llm.llm import AGENT_MAX_ITERATIONS

from .asset_state import AssetAgentState

MUTATION_INTENTS = ("create", "update", "delete", "adjust_balance")


def route_by_intent(state: AssetAgentState) -> str:
    """query 直接执行；写操作先过定位与确认。"""
    return "mutation_check" if state.get("intent") in MUTATION_INTENTS else "asset_agent"


def route_after_mutation_check(state: AssetAgentState) -> str:
    if state.get("result"):
        return "result_formatter"
    return "human_confirm" if state.get("need_confirm") else "asset_agent"


def route_after_agent(state: AssetAgentState) -> str:
    """还有 tool_calls 且没打满轮次就去执行工具，否则收尾。"""
    messages = state.get("messages") or []
    last = messages[-1] if messages else None
    has_calls = isinstance(last, AIMessage) and bool(getattr(last, "tool_calls", None))
    if has_calls and int(state.get("loops") or 0) < AGENT_MAX_ITERATIONS:
        return "asset_tools"
    return "result_formatter"
