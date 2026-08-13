"""Orchestrator：View 入口之后 → 寒暄短路 → 加载记忆 → Supervisor → 业务 Agent。

寒暄在进入 Supervisor 之前处理。记忆来自 LangchainChatMessage（最近 3 轮 + 更早摘要）。
对外只暴露 run_orchestrator，返回 {output, intermediate_steps[, confirm]}。
"""

from __future__ import annotations

from account.ai.agent.func import quick_agent_greeting_prompt
from account.ai.llm import prompt
from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import extract_content
from account.ai.llm.schemas import DEFAULT_CHAT_REPLY, TextReply

from .executor import execute
from .memory import load_chat_memory
from .open_task_router import is_open_planning
from .router import decide
from .state import AgentState, new_state

__all__ = ["run_orchestrator", "AgentState", "new_state"]

_CANCEL_REPLY = "好的，已取消啦～"


def _try_greeting(text: str) -> str | None:
    g = quick_agent_greeting_prompt(text)
    if not g.is_greeting:
        return None
    raw = extract_content(llm.invoke(prompt.build_greeting_prompt(text, g.prompt)))
    return TextReply(reply=raw or DEFAULT_CHAT_REPLY).reply


def run_orchestrator(user_input: str, user=None, conversation_id=None, confirm=None) -> dict:
    text = user_input or ""
    confirm = confirm or None

    # 前端确认卡片：取消直接短路；确认强制走 bill，跳过寒暄与 Supervisor
    if isinstance(confirm, dict) and "confirm" in confirm:
        if confirm.get("confirm") is False:
            return {"output": _CANCEL_REPLY, "intermediate_steps": []}
        if confirm.get("confirm") is True:
            state = new_state(text, user=user, conversation_id=conversation_id)
            memory_messages, memory_text = load_chat_memory(user, text)
            state["memory_messages"] = memory_messages
            state["memory_text"] = memory_text
            state["messages"] = list(memory_messages)
            state["task_type"] = "bill"
            state["current_agent"] = "bill"
            state["confirm"] = confirm
            execute(state)
            return state["final_response"]

    greeting = _try_greeting(text)
    if greeting is not None:
        return {"output": greeting, "intermediate_steps": []}

    state = new_state(text, user=user, conversation_id=conversation_id)
    memory_messages, memory_text = load_chat_memory(user, text)
    state["memory_messages"] = memory_messages
    state["memory_text"] = memory_text
    state["messages"] = list(memory_messages)

    # 顶层任务分流：开放式规划 → CrewAI；其余 → 原 Supervisor 决策（保持不变）
    if is_open_planning(text, memory_text):
        state["task_type"] = "open_planning"
        state["current_agent"] = "finance_planner"
    else:
        decide(state)
    execute(state)
    return state["final_response"]
