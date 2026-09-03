"""Orchestrator：统一将请求规划为 WorkflowPlan 后交给 execute_plan 执行。

寒暄在规划之前处理，确认恢复也先恢复 WorkflowPlan，再进入同一执行入口。
记忆来自 LangchainChatMessage（最近 3 轮 + 更早摘要）。
"""

from __future__ import annotations

from uuid import uuid4

from account.ai.gateway.func import quick_agent_greeting_prompt
from account.ai.llm import prompt
from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import extract_content
from account.ai.llm.schemas import DEFAULT_CHAT_REPLY, TextReply

from .executor import execute_plan
from .events import EventEmitter
from .memory import load_chat_memory
from .state import AgentState, new_state
from .task_schema import WorkflowPlan, WorkflowTask
from .unified_planner import build_route_plan

__all__ = ["run_orchestrator", "AgentState", "new_state"]

_CANCEL_REPLY = "好的，已取消啦～"

# 确认数据没有完整计划时，仍转换为统一的单任务 WorkflowPlan

def _confirmation_plan(confirm: dict, confirm_extra: dict) -> WorkflowPlan:
    """Convert a legacy single confirmation payload into the unified plan shape."""
    entity = str(confirm.get("entity") or confirm_extra.get("entity") or "bill")
    if entity not in {"bill", "budget", "asset", "invoice"}:
        entity = "bill"
    action = str(confirm.get("action") or confirm_extra.get("action") or "").strip()
    task_input = dict(confirm_extra.get("payload") or confirm.get("payload") or {})
    candidates = confirm_extra.get("candidates") or confirm.get("candidates") or []
    if candidates:
        task_input["candidates"] = candidates
    if entity == "bill" and action == "batch_create" and candidates:
        task_input["items"] = candidates
    target_id = confirm.get("target_id")
    if target_id is None:
        target_id = confirm_extra.get("target_id")
    if target_id is not None:
        task_input["target_id"] = target_id
    if action:
        task_input["action"] = action
    return WorkflowPlan(
        tasks=[
            WorkflowTask(
                id=f"{entity}_{action or 'confirmed'}",
                type=entity,
                goal=f"确认执行{action or '该操作'}",
                input=task_input,
            )
        ]
    )


def _try_greeting(text: str) -> str | None:
    g = quick_agent_greeting_prompt(text)
    if not g.is_greeting:
        return None
    raw = extract_content(llm.invoke(prompt.build_greeting_prompt(text, g.prompt)))
    return TextReply(reply=raw or DEFAULT_CHAT_REPLY).reply


def run_orchestrator(
    user_input: str,
    user=None,
    conversation_id=None,
    confirm=None,
    *,
    trace_id: str | None = None,
    event_emitter: EventEmitter | None = None,
    plan_id: str | None = None,
) -> dict:
    text = user_input or ""
    trace_id = trace_id or str(uuid4())
    plan_id = plan_id or str(conversation_id or trace_id)
    confirm = confirm or None

    # 前端确认卡片：取消短路；确认统一恢复为 Plan 后执行
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
            plan = (
                WorkflowPlan.model_validate({"tasks": plan_tasks})
                if plan_tasks
                else _confirmation_plan(confirm, confirm_extra)
            )
            state["task_type"] = "plan"
            state["current_agent"] = "executor"
            state["confirm"] = {**confirm, "confirmed_plan": True}
            execute_plan(
                state,
                plan,
                trace_id=trace_id,
                event_emitter=event_emitter,
                runtime_plan_id=plan_id,
            )
            return state["final_response"]

    greeting = _try_greeting(text)
    if greeting is not None:
        return {"output": greeting, "intermediate_steps": []}

    state = new_state(text, user=user, conversation_id=conversation_id)
    memory_messages, memory_text = load_chat_memory(user, text)
    state["memory_messages"] = memory_messages
    state["memory_text"] = memory_text
    state["messages"] = list(memory_messages)

    # 顶层统一 Planner：一次理解请求，再选择一个或多个 Workflow
    plan = build_route_plan(text, memory_text)
    if plan is None:
        return {
            "output": "暂时无法生成有效的执行计划，请换一种说法再试试。",
            "intermediate_steps": [],
            "plan_result": {
                "plan_id": plan_id,
                "status": "failed",
                "task_results": [],
                "summary": "统一 Planner 未能生成有效计划",
                "analysis_view": {},
                "intermediate_steps": [],
            },
        }

    state["task_type"] = "plan"
    state["current_agent"] = "executor"
    execute_plan(
        state,
        WorkflowPlan(tasks=plan.tasks),
        trace_id=trace_id,
        event_emitter=event_emitter,
        runtime_plan_id=plan_id,
    )
    return state["final_response"]
