"""Chat Workflow 的图状态。只在聊天域内流转，不外泄给其他 Agent。"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class ChatState(TypedDict, total=False):
    """聊天 Workflow 状态。

    messages 用 add_messages 累积，最终由 chat_agent 的 _graph_to_result 还原
    成 {output, intermediate_steps}，保持与 SSE / to_api_dict 的协议不变。
    """

    messages: Annotated[list[AnyMessage], add_messages]  # 对话历史 + 本轮各节点追加的消息
    user_id: int | None  # 当前用户 id（仅标识，节点内不查 ORM）
    input: str  # 本轮要回复的用户原话（优先取 task_input.message）
    task_input: dict  # Planner 结构化入参，含 message 字段
    loops: int  # chat_agent 已循环次数，防无限 tool 调用
    result: dict | None  # 提前结束的统一出参 {success, message, data}
