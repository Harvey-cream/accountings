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
    if data:
        out["data"] = data
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
    task_action = payload.get("task_action")
    task_confirmed = bool(payload.get("task_confirmed"))
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
    confirm = payload.get("confirm") or {}
    action = str(confirm.get("action") or "").strip()
    if confirm.get("confirm") is True:
        if action == "create":
            state["intent"] = action
            state["confirmed"] = True
            # 计划级确认回放：草稿来自持久化 task_input，否则 mutation_check 会判空
            if not state.get("draft"):
                state["draft"] = {
                    key: task_input[key]
                    for key in (
                        "name",
                        "asset_type",
                        "balance",
                        "account_type",
                        "is_included_in_total",
                        "remark",
                    )
                    if key in task_input
                }
        elif action in _CONFIRM_ACTIONS and confirm.get("target_id") is not None:
            state["intent"] = action
            state["target_account"] = {"id": int(confirm["target_id"])}
            state["confirmed"] = True
        return state

    # 计划任务显式给出 action；写操作在确认后由 confirm 分支接管，这里只注入 intent
    if task_action in _CONFIRM_ACTIONS:
        state["intent"] = task_action
        state["confirmed"] = task_confirmed
        if task_action == "create" and not state.get("draft"):
            state["draft"] = {
                key: task_input[key]
                for key in (
                    "name",
                    "asset_type",
                    "balance",
                    "account_type",
                    "is_included_in_total",
                    "remark",
                )
                if key in task_input
            }
        elif task_action == "update":
            state["draft"] = {
                key: task_input[key]
                for key in (
                    "name",
                    "asset_type",
                    "balance",
                    "account_type",
                    "is_included_in_total",
                    "remark",
                )
                if key in task_input
            }
        if task_input.get("account_id") is not None:
            state["target_account"] = {"id": int(task_input["account_id"])}
    elif task_action == "query":
        state["intent"] = "query"
    return state


def _build_chain(user):
    """资产域专属管道：input -> asset workflow -> result。"""
    return (
        RunnableLambda(_to_graph_input)
        | build_asset_graph(user)
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
) -> dict:
    chain = _build_chain(user)
    return chain.invoke(
        {
            "input": user_input or "",
            "history": history or [],
            "user": user,
            "task_input": task_input or {},
            "task_action": task_action,
            "task_confirmed": task_confirmed,
            "confirm": confirm,
        },
        config={"recursion_limit": max(AGENT_MAX_ITERATIONS * 2 + 10, 16)},
    )
