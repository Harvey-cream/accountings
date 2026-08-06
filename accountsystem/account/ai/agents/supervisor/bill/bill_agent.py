"""Bill Agent 外壳：LCEL 管道 → Bill Workflow(StateGraph) → 结果适配。

图与节点在 bill_graph / bill_nodes 里，本文件只负责入参整形与出参兼容。
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableLambda

from account.ai.llm.llm import AGENT_MAX_ITERATIONS
from account.ai.llm.llm_utils import extract_content

from .bill_graph import build_bill_graph

_CONFIRM_ACTIONS = {"update", "delete"}


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
    if data.get("need_confirm"):
        out["confirm"] = {
            "need_confirm": True,
            "action": data.get("action") or "",
            "candidates": data.get("candidates") or [],
        }
    return out


def _to_graph_input(payload: dict) -> dict:
    user = payload.get("user")
    state = {
        "input": payload.get("input") or "",
        "messages": list(payload.get("history") or []),
        "user_id": getattr(user, "id", None),
        "need_confirm": False,
        "confirmed": False,
        "loops": 0,
    }
    confirm = payload.get("confirm") or {}
    action = str(confirm.get("action") or "").strip()
    bill_id = confirm.get("bill_id")
    if confirm.get("confirm") is True and bill_id is not None and action in _CONFIRM_ACTIONS:
        state["intent"] = action
        state["target_bill"] = {"id": int(bill_id)}
        state["confirmed"] = True
    return state


def _build_chain(user):
    """账单域专属管道：input -> bill workflow -> result。"""
    return (
        RunnableLambda(_to_graph_input)
        | build_bill_graph(user)
        | RunnableLambda(_graph_to_result)
    )


def run(user_input: str, user=None, history=None, confirm=None) -> dict:
    chain = _build_chain(user)
    return chain.invoke(
        {
            "input": user_input or "",
            "history": history or [],
            "user": user,
            "confirm": confirm,
        },
        config={"recursion_limit": max(AGENT_MAX_ITERATIONS * 2 + 10, 16)},
    )
