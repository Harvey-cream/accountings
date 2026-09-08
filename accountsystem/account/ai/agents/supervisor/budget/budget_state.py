"""Budget Agent Workflow 状态。只在预算域内流转。"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class BudgetAgentState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: int | None
    input: str
    intent: str  # set_budget / query_budget / budget_advice
    budget_params: dict
    validation_result: dict
    policy_result: dict
    tool_result: Any
    need_input: bool
    confirmed: bool
    need_confirm: bool
    final_response: str
    loops: int
