"""路由层：调用 Supervisor 决策，把 task_type / current_agent 写回 state。"""

from __future__ import annotations

from account.ai.agents.supervisor import route

from .state import AgentState


def decide(state: AgentState) -> AgentState:
    decision = route(state.get("user_input") or "")
    state["task_type"] = decision.task_type
    state["current_agent"] = decision.task_type
    return state
