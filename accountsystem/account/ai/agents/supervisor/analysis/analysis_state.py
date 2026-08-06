"""Analysis Agent Workflow 状态。只在分析域内流转。"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AnalysisAgentState(TypedDict, total=False):
    """消费分析 Workflow 状态。"""

    messages: Annotated[list[AnyMessage], add_messages]
    user_id: int | None
    input: str
    intent: str  # summary / category / compare
    parameters: dict  # days, category, period_label, need_input, ask_message, ...
    tool_result: Any
    final_response: str
    loops: int
