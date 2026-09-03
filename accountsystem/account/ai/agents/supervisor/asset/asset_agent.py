"""Asset Agent 外壳：LCEL 管道 → Asset Workflow(StateGraph) → 结果适配。

图与节点在 asset_graph / asset_nodes 里，本文件只负责入参整形与出参兼容。
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableLambda

from account.ai.llm.llm import AGENT_MAX_ITERATIONS
from account.ai.llm.llm_utils import extract_content

from .asset_graph import build_asset_graph

_CONFIRM_ACTIONS = {"create", "update", "delete", "adjust_balance"}
_TARGETLESS_ACTIONS = {"create"}


def _tool_call_id(tc) -> str:
    if isinstance(tc, dict):
        return str(tc.get("id") or "")
    return str(getattr(tc, "id", "") or "")


def _graph_to_result(graph_state: dict) -> dict:
    """Asset 结果适配：messages + result -> {output, intermediate_steps[, confirm]}。"""
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
            "entity": "asset",
            "action": data.get("action") or "",
            "candidates": data.get("candidates") or [],
        }
    return out


def _to_graph_input(payload: dict) -> dict:
    user = payload.get("user")
    task_input = payload.get("task_input") or {}
    state = {
        "input": payload.get("input") or "",
        "messages": list(payload.get("history") or []),
        "user_id": getattr(user, "id", None),
        "need_confirm": False,
        "confirmed": False,
        "loops": 0,
    }
    allowed = {"intent", "target_account", "candidates", "draft"}
    state.update({key: value for key, value in task_input.items() if key in allowed})
    if not state.get("intent") and task_input.get("action") in _CONFIRM_ACTIONS:
        state["intent"] = task_input["action"]
    if not state.get("target_account") and task_input.get("target_id") is not None:
        state["target_account"] = {"id": int(task_input["target_id"])}
    if state.get("intent") == "create" and not state.get("draft"):
        state["draft"] = {key: value for key, value in task_input.items() if key != "action"}
    confirm = payload.get("confirm") or {}
    action = str(confirm.get("action") or "").strip()
    if confirm.get("confirm") is not True or action not in _CONFIRM_ACTIONS:
        return state

    target_id = confirm.get("target_id")
    if action in _TARGETLESS_ACTIONS:
        state["intent"] = action
        state["confirmed"] = True
    elif target_id is not None:
        state["intent"] = action
        state["target_account"] = {"id": int(target_id)}
        state["confirmed"] = True
    return state


def _build_chain(user):
    """资产域专属管道：input -> asset workflow -> result。"""
    return (
        RunnableLambda(_to_graph_input)
        | build_asset_graph(user)
        | RunnableLambda(_graph_to_result)
    )


def run(user_input: str, user=None, history=None, confirm=None, task_input=None) -> dict:
    chain = _build_chain(user)
    return chain.invoke(
        {
            "input": user_input or "",
            "history": history or [],
            "user": user,
            "task_input": task_input or {},
            "confirm": confirm,
        },
        config={"recursion_limit": max(AGENT_MAX_ITERATIONS * 2 + 10, 16)},
    )
