"""Bill Workflow 条件边：只做分支判断，不产生副作用。"""

from __future__ import annotations

from langchain_core.messages import AIMessage

from account.ai.llm.llm import AGENT_MAX_ITERATIONS

from .bill_state import BillAgentState

MUTATION_INTENTS = ("update", "delete")


def route_by_intent(state: BillAgentState) -> str:
    """create/query 直接执行；批量记账先拆草稿；update/delete 先过定位与确认。"""
    intent = state.get("intent")
    if intent == "batch_create":
        return "batch_parse"
    return "mutation_check" if intent in MUTATION_INTENTS else "bill_agent"


def route_after_mutation_check(state: BillAgentState) -> str:
    if state.get("result"):
        return "result_formatter"
    return "human_confirm" if state.get("need_confirm") and not state.get("confirmed") else "bill_agent"


def route_after_batch_parse(state: BillAgentState) -> str:
    """拆不出草稿就直接收尾；未确认先出汇总卡片；已确认交给 bill_agent 批量落库。"""
    if state.get("result"):
        return "result_formatter"
    return "human_confirm" if state.get("need_confirm") and not state.get("confirmed") else "bill_agent"


def route_after_agent(state: BillAgentState) -> str:
    """还有 tool_calls 且没打满轮次就去执行工具，否则收尾。"""
    messages = state.get("messages") or []
    last = messages[-1] if messages else None
    has_calls = isinstance(last, AIMessage) and bool(getattr(last, "tool_calls", None))
    if has_calls and int(state.get("loops") or 0) < AGENT_MAX_ITERATIONS:
        return "bill_tools"
    return "result_formatter"
