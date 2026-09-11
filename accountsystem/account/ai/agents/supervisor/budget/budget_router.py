"""Budget Workflow 条件边。"""

from __future__ import annotations

from langchain_core.messages import AIMessage

from account.ai.llm.llm import AGENT_MAX_ITERATIONS

from .budget_state import BudgetAgentState


def route_after_validator(state: BudgetAgentState) -> str:
    result = state.get("validation_result") or {}
    if state.get("need_input") or result.get("ok") is False:
        return "end"
    if state.get("need_confirm") and not state.get("confirmed"):
        return "human_confirm"
    return "policy_check"


def route_after_policy(state: BudgetAgentState) -> str:
    result = state.get("policy_result") or {}
    if result.get("ok") is False:
        return "end"
    if state.get("intent") == "set_budget" and not state.get("confirmed"):
        return "human_confirm"
    if state.get("final_response"):
        return "end"
    return "budget_agent"


def route_after_agent(state: BudgetAgentState) -> str:
    messages = state.get("messages") or []
    last = messages[-1] if messages else None
    has_calls = isinstance(last, AIMessage) and bool(getattr(last, "tool_calls", None))
    if has_calls and int(state.get("loops") or 0) < AGENT_MAX_ITERATIONS:
        return "budget_tools"
    return "response_generator"
