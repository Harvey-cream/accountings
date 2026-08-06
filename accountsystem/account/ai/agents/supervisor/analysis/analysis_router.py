"""Analysis Workflow 条件边。"""

from __future__ import annotations

from langchain_core.messages import AIMessage

from account.ai.llm.llm import AGENT_MAX_ITERATIONS

from .analysis_state import AnalysisAgentState


def route_after_params(state: AnalysisAgentState) -> str:
    """参数齐全 → agent；缺参追问 → 直接结束。"""
    params = state.get("parameters") or {}
    if params.get("need_input") or state.get("final_response"):
        return "end"
    return "analysis_agent"


def route_after_agent(state: AnalysisAgentState) -> str:
    messages = state.get("messages") or []
    last = messages[-1] if messages else None
    has_calls = isinstance(last, AIMessage) and bool(getattr(last, "tool_calls", None))
    if has_calls and int(state.get("loops") or 0) < AGENT_MAX_ITERATIONS:
        return "analysis_tools"
    return "insight_generate"
