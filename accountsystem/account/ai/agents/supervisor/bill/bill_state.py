"""Bill Agent Workflow 的图状态。只在账单域内流转，不外泄给其他 Agent。"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class BillAgentState(TypedDict, total=False):
    """账单 Workflow 状态。

    messages 用 add_messages 累积，最终由 bill_agent 的 _graph_to_result 还原
    成 {output, intermediate_steps}，保持与 SSE / to_api_dict 的协议不变。
    """

    messages: Annotated[list[AnyMessage], add_messages]  # 对话历史 + 本轮各节点追加的消息
    user_id: int | None  # 当前用户 id（仅标识，节点内不查 ORM）
    input: str  # 本轮用户原始输入
    intent: str  # 账单操作类型：create / batch_create / query / update / delete
    target_bill: dict | None  # 已定位的目标账单，至少含 id
    candidates: list[dict]  # 搜到多笔时的候选列表
    drafts: list[dict]  # batch_create 解析出的多笔草稿，供汇总确认与批量落库
    need_confirm: bool  # 改删前是否还需向用户确认
    confirmed: bool  # 前端确认卡片点确认后由外壳置 True
    loops: int  # bill_agent 已循环次数，防无限 tool 调用
    result: dict | None  # 提前结束的统一出参 {success, message, data}
