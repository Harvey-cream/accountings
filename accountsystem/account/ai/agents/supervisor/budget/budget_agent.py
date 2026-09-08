"""Budget Agent 外壳：LCEL → Budget Workflow → 结果适配。"""

from __future__ import annotations

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableLambda

from account.ai.llm.llm import AGENT_MAX_ITERATIONS
from account.ai.llm.llm_utils import extract_content

from .budget_graph import build_budget_graph


def _tool_call_id(tc) -> str:
    if isinstance(tc, dict):
        return str(tc.get("id") or "")
    return str(getattr(tc, "id", "") or "")


def _graph_to_result(graph_state: dict) -> dict:
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
    output = (graph_state.get("final_response") or "").strip()
    if not output and messages:
        output = extract_content(messages[-1]).strip()
    result = graph_state.get("result") or {}
    out = {"output": output, "intermediate_steps": steps}
    if graph_state.get("need_confirm"):
        out["confirm"] = {
            "need_confirm": True,
            "entity": "budget",
            "action": "update",
            "payload": graph_state.get("budget_params") or {},
        }
    return out


def _to_graph_input(payload: dict) -> dict:
    user = payload.get("user")
    task_input = payload.get("task_input") or {}
    confirm = payload.get("confirm") or {}
    state = {
        "input": payload.get("input") or "",
        "messages": list(payload.get("history") or []),
        "user_id": getattr(user, "id", None),
        "loops": 0,
        "need_input": False,
        "confirmed": bool(confirm.get("confirmed_plan") or confirm.get("confirm")),
    }
    if task_input:
        state["intent"] = "set_budget" if task_input.get("action") == "update" else task_input.get("intent")
        state["budget_params"] = {
            key: task_input[key]
            for key in ("amount", "period", "budget_type", "is_total", "category")
            if key in task_input
        }
    return state


def _build_chain(user):
    return (
        RunnableLambda(_to_graph_input)
        | build_budget_graph(user)
        | RunnableLambda(_graph_to_result)
    )


def run(user_input: str, user=None, history=None, confirm=None, task_input=None) -> dict:
    chain = _build_chain(user)
    return chain.invoke(
        {
            "input": user_input or "",
            "history": history or [],
            "user": user,
            "confirm": confirm,
            "task_input": task_input or {},
        },
        config={"recursion_limit": max(AGENT_MAX_ITERATIONS * 2 + 10, 16)},
    )
