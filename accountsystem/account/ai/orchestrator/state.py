"""统一 Agent 状态：贯穿 orchestrator -> supervisor -> 业务 Agent。

字段设计对齐多 Agent 协作场景，并预留给未来 LangGraph / CrewAI 接入：
messages / tool_results 可作为共享上下文，current_agent / task_type 可映射任务节点。
"""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    # --- 会话身份 ---
    user_id: Any
    conversation_id: Any
    # 运行期携带的 Django User（Tool 构建需要），Agent 层不得据此访问 ORM
    user: Any

    # --- 输入 ---
    user_input: str

    # --- 路由结果 ---
    task_type: str      # bill / analysis / budget
    current_agent: str  # 当前执行的业务 Agent 名

    # --- 执行上下文 ---
    messages: list          # 预留：跨 Agent 共享的消息序列
    tool_results: list      # intermediate_steps: [(tool_call, observation), ...]

    # --- 输出 ---
    final_response: dict    # {"output": str, "intermediate_steps": list}


def new_state(user_input: str, user: Any = None, conversation_id: Any = None) -> AgentState:
    return AgentState(
        user_id=getattr(user, "id", None),
        conversation_id=conversation_id,
        user=user,
        user_input=user_input or "",
        messages=[],
        tool_results=[],
    )
