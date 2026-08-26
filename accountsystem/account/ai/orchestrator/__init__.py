"""Orchestrator：View 入口之后 → 寒暄短路 → 加载记忆 → 顶层分流 → 业务 Agent。

顶层分流三层：开放式规划(CrewAI) → 跨域组合(Task Planner，多 Workflow 依序执行)
→ 简单固定业务(Supervisor 单域路由)。
寒暄在分流之前处理。记忆来自 LangchainChatMessage（最近 3 轮 + 更早摘要）。
对外只暴露 run_orchestrator，返回 {output, intermediate_steps[, confirm]}。
"""

from __future__ import annotations

from account.ai.agent.func import quick_agent_greeting_prompt
from account.ai.llm import prompt
from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import extract_content
from account.ai.llm.schemas import DEFAULT_CHAT_REPLY, TextReply

from .executor import execute, execute_plan
from .memory import load_chat_memory
from .open_task_router import is_open_planning
from .router import decide
from .state import AgentState, new_state
from .task_planner import is_probably_multi, plan_workflows
from .task_schema import WorkflowPlan

__all__ = ["run_orchestrator", "AgentState", "new_state"]

_CANCEL_REPLY = "好的，已取消啦～"

# 带 human_confirm 机制的业务域，确认卡片回传时直达对应 Workflow
_CONFIRM_ENTITIES = frozenset({"bill", "asset", "invoice"})


def _try_greeting(text: str) -> str | None:
    g = quick_agent_greeting_prompt(text)
    if not g.is_greeting:
        return None
    raw = extract_content(llm.invoke(prompt.build_greeting_prompt(text, g.prompt)))
    return TextReply(reply=raw or DEFAULT_CHAT_REPLY).reply


def run_orchestrator(user_input: str, user=None, conversation_id=None, confirm=None) -> dict:
    text = user_input or ""
    confirm = confirm or None

    # 前端确认卡片：取消直接短路；确认按卡片所属业务域直达该 Workflow，跳过寒暄与 Supervisor
    if isinstance(confirm, dict) and "confirm" in confirm:
        if confirm.get("confirm") is False:
            return {"output": _CANCEL_REPLY, "intermediate_steps": []}
        if confirm.get("confirm") is True:
            state = new_state(text, user=user, conversation_id=conversation_id)
            memory_messages, memory_text = load_chat_memory(user, text)
            state["memory_messages"] = memory_messages
            state["memory_text"] = memory_text
            state["messages"] = list(memory_messages)

            confirm_extra = confirm.get("confirm_extra") or {}
            plan_tasks = confirm_extra.get("plan_tasks") or []
            if plan_tasks:
                state["task_type"] = "workflow_plan"
                state["current_agent"] = "task_planner"
                state["confirm"] = {**confirm, "confirmed_plan": True}
                plan = WorkflowPlan.model_validate({"tasks": plan_tasks})
                execute_plan(state, plan)
                return state["final_response"]

            entity = str(confirm.get("entity") or "bill")
            task = entity if entity in _CONFIRM_ENTITIES else "bill"
            state["task_type"] = task
            state["current_agent"] = task
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

    # 顶层任务分流（三层）：
    # 1) 开放式规划 → CrewAI
    if is_open_planning(text, memory_text):
        state["task_type"] = "open_planning"
        state["current_agent"] = "finance_planner"
        execute(state)
        return state["final_response"]

    # 2) 疑似跨域组合 → Task Planner 产出计划，按依赖序执行多个 Workflow
    if is_probably_multi(text, memory_text):
        plan = plan_workflows(text, memory_text)
        if plan is not None and len(plan.tasks) > 1:
            state["task_type"] = "workflow_plan"
            state["current_agent"] = "task_planner"
            execute_plan(state, plan)
            return state["final_response"]
        if plan is not None:
            # 规划结论是单任务：直接采纳，省一次 Supervisor 调用
            state["task_type"] = plan.tasks[0].type
            state["current_agent"] = plan.tasks[0].type
            execute(state)
            return state["final_response"]
        # 规划失败 → 回落 Supervisor

    # 3) 简单固定业务 → 原 Supervisor 快速路由（保持不变）
    decide(state)
    execute(state)
    return state["final_response"]
