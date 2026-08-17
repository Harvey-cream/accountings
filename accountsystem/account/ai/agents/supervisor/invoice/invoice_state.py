"""Invoice Agent Workflow 的图状态。只在发票域内流转，不外泄给其他 Agent。"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class InvoiceAgentState(TypedDict, total=False):
    """发票 Workflow 状态。

    出参由 invoice_agent 的 _graph_to_result 还原成 {output, intermediate_steps[, confirm]}，
    与 Bill Workflow 保持同一协议。
    """

    messages: Annotated[list[AnyMessage], add_messages]  # 对话历史 + 本轮各节点追加的消息
    user_id: int | None  # 当前用户 id（仅标识，节点内不查 ORM）
    input: str  # 本轮用户原始输入
    intent: str  # create / query / update / delete
    target_invoice: dict | None  # 已定位的目标发票信息，至少含 id
    candidates: list[dict]  # 搜到多条时的候选列表
    need_confirm: bool  # 改删前是否还需向用户确认
    confirmed: bool  # 前端确认卡片点确认后由外壳置 True
    loops: int  # invoice_agent 已循环次数，防无限 tool 调用
    result: dict | None  # 提前结束的统一出参 {success, message, data}
