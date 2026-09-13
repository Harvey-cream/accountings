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
from .unified_planner import PlannerError, build_route_plan

__all__ = ["run_orchestrator", "AgentState", "new_state"]

_CANCEL_REPLY = "好的，已取消啦～"

# 确认恢复：只信服务端持久化的 entity/action/payload，客户端仅能"从候选里选一个目标"
_SUPPORTED_ENTITIES = {"bill", "budget", "asset", "invoice"}
_TARGET_ID_FIELDS = {"bill": "bill_id", "asset": "account_id", "invoice": "invoice_id"}


def _candidate_ids(candidates) -> set[int]:
    ids: set[int] = set()
    for row in candidates or []:
        if not isinstance(row, dict):
            continue
        rid = row.get("id")
        if isinstance(rid, bool):
            continue
        if isinstance(rid, int):
            ids.add(rid)
        elif isinstance(rid, str) and rid.strip().lstrip("-").isdigit():
            ids.add(int(rid))
    return ids


def _explicit_target_id(entity: str, task_input: dict) -> int | None:
    field = _TARGET_ID_FIELDS.get(entity)
    value = task_input.get(field) if field else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _confirmation_plan(confirm: dict, confirm_extra: dict) -> WorkflowPlan:
    """只用服务端持久化的确认数据恢复执行；客户端 target_id 必须命中持久化候选。"""
    entity = confirm_extra.get("entity")
    action = str(confirm_extra.get("action") or "").strip()
    if entity not in _SUPPORTED_ENTITIES or not action:
        raise ValueError("persisted confirmation must include a supported entity and action")
    if entity == "budget" and action == "update":
        action = "set_budget"

    payload = confirm_extra.get("payload")
    task_input = dict(payload) if isinstance(payload, dict) else {}
    candidates = confirm_extra.get("candidates") or []
    if entity == "bill" and action == "batch_create":
        items = candidates or task_input.get("items")
        if not items:
            raise ValueError("bill batch confirmation requires candidates or items")
        task_input["items"] = items

    target_id = _explicit_target_id(entity, task_input)
    if target_id is None:
        client_target = confirm.get("target_id")
        if isinstance(client_target, int) and client_target in _candidate_ids(candidates):
            target_id = client_target
    field = _TARGET_ID_FIELDS.get(entity)
    if target_id is not None and field:
        task_input[field] = target_id

    return WorkflowPlan(
        tasks=[
            WorkflowTask(
                id=f"{entity}_{action}",
                type=entity,
                action=action,
                goal=f"确认执行{action}",
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
            workflow_plan = confirm_extra.get("workflow_plan") or []
            try:
                plan = (
                    WorkflowPlan.model_validate({"tasks": workflow_plan})
                    if workflow_plan
                    else _confirmation_plan(confirm, confirm_extra)
                )
            except (TypeError, ValueError):
                return {
                    "output": "确认信息无效，计划未执行。",
                    "intermediate_steps": [],
                    "plan_result": {
                        "plan_id": plan_id,
                        "status": "failed",
                        "task_results": [],
                        "summary": "确认信息未通过计划校验",
                        "analysis_view": {},
                        "intermediate_steps": [],
                    },
                }
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

    # Planner 调用较慢，先播报状态，避免前端看起来完全卡死
    if event_emitter is not None:
        event_emitter.emit(
            "plan.started",
            trace_id=trace_id,
            plan_id=plan_id,
            message="正在分析你的请求…",
        )

    # 顶层统一 Planner：一次理解请求，再选择一个或多个 Workflow
    try:
        plan = build_route_plan(text, memory_text)
    except PlannerError as exc:
        return {
            "output": exc.user_message,
            "intermediate_steps": [],
            "plan_result": {
                "plan_id": plan_id,
                "status": "failed",
                "task_results": [],
                "summary": exc.user_message,
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
