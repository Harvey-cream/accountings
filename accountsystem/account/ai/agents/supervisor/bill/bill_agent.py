"""Bill Agent 外壳：LCEL 管道 → Bill Workflow(StateGraph) → 结果适配。

图与节点在 bill_graph / bill_nodes 里，本文件只负责入参整形与出参兼容。
强 Schema 下 action 由计划任务显式给出，不再从自然语言重新猜测。
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableLambda

from account.ai.llm.llm import AGENT_MAX_ITERATIONS
from account.ai.llm.llm_utils import extract_content
from account.ai.observability import (
    mark_span_ok,
    record_exception,
    set_span_attribute,
    start_span,
)
from account.ai.observability.context import (
    WorkflowContext,
    confirmation_granted,
    use_workflow_context,
    workflow_status,
)

from .bill_graph import build_bill_graph


def _tool_call_id(tc) -> str:
    if isinstance(tc, dict):
        return str(tc.get("id") or "")
    return str(getattr(tc, "id", "") or "")


def _graph_to_result(graph_state: dict) -> dict:
    """Bill 结果适配：messages + result -> {output, intermediate_steps[, confirm]}。"""
    messages = graph_state.get("messages") or []
    pending = {}
    steps = []
    for msg in messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                pending[_tool_call_id(tc)] = tc
        elif isinstance(msg, ToolMessage):
            tc = pending.get(str(msg.tool_call_id))
            if tc is not None:
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                steps.append((tc, content))
    result = graph_state.get("result") or {}
    output = (result.get("message") or "").strip()
    if not output and messages:
        output = extract_content(messages[-1]).strip()
    out = {"output": output, "intermediate_steps": steps}
    data = result.get("data") or {}
    if data:
        out["data"] = data
    if data.get("need_confirm"):
        out["confirm"] = {
            "need_confirm": True,
            "entity": "bill",
            "action": data.get("action") or "",
            "candidates": data.get("candidates") or [],
        }
    return out


def _to_graph_input(payload: dict) -> dict:
    user = payload.get("user")
    task_action = payload.get("task_action")
    task_confirmed = bool(payload.get("task_confirmed"))
    task_input = payload.get("task_input") or {}
    state = {
        "input": payload.get("input") or "",
        "messages": list(payload.get("history") or []),
        "user_id": getattr(user, "id", None),
        "need_confirm": False,
        "confirmed": False,
        "loops": 0,
        "task_input": task_input,
    }
    confirm = payload.get("confirm") or {}
    if confirm.get("confirm") is True:
        action = str(confirm.get("action") or "").strip()
        if action in {"update", "delete"} and confirm.get("target_id") is not None:
            state["intent"] = action
            state["target_bill"] = {"id": int(confirm["target_id"])}
            state["confirmed"] = True
            return state
    if task_action in {"update", "delete"}:
        state["intent"] = task_action
        target = int(task_input.get("bill_id")) if task_input.get("bill_id") is not None else None
        if target is not None:
            state["target_bill"] = {"id": target}
        state["confirmed"] = task_confirmed
        return state
    if task_action in {"create", "batch_create", "query"}:
        state["intent"] = task_action
        state["confirmed"] = task_confirmed
        if task_action == "batch_create":
            state["drafts"] = list(task_input.get("items") or [])
    return state


def _build_chain(user):
    """账单域专属管道：input -> bill workflow -> result。"""
    return (
        RunnableLambda(_to_graph_input)
        | build_bill_graph(user)
        | RunnableLambda(_graph_to_result)
    )


def run(
    user_input: str,
    user=None,
    history=None,
    confirm=None,
    task_action=None,
    task_input=None,
    task_confirmed=False,
    task_id=None,
) -> dict:
    confirmed = confirmation_granted(task_confirmed, confirm)
    context = WorkflowContext("bill", str(task_action or "unspecified"), str(task_id or ""), confirmed)
    with use_workflow_context(context):
        with start_span(
            "workflow.run",
            {
                "agent.domain": "bill",
                "agent.action": context.action,
                "agent.task_id": task_id,
                "workflow.name": "bill",
            },
        ) as span:
            try:
                chain = _build_chain(user)
                result = chain.invoke(
                    {
                        "input": user_input or "",
                        "history": history or [],
                        "user": user,
                        "confirm": confirm,
                        "task_action": task_action,
                        "task_input": task_input or {},
                        "task_confirmed": task_confirmed,
                    },
                    config={"recursion_limit": max(AGENT_MAX_ITERATIONS * 2 + 10, 16)},
                )
            except Exception as exc:
                set_span_attribute(span, "workflow.status", "failed")
                record_exception(span, exc)
                raise
            set_span_attribute(span, "workflow.status", workflow_status(result))
            mark_span_ok(span)
            return result
