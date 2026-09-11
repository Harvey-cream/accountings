"""Chat Agent 外壳：LCEL 管道 → Chat Workflow → 结果适配。

图与节点在 chat_graph / chat_nodes 里，本文件只负责入参整形与出参兼容。
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableLambda

from account.ai.llm.llm import AGENT_MAX_ITERATIONS
from account.ai.llm.llm_utils import extract_content

from .chat_graph import build_chat_graph


def _tool_call_id(tc) -> str:
    if isinstance(tc, dict):
        return str(tc.get("id") or "")
    return str(getattr(tc, "id", "") or "")


def _graph_to_result(graph_state: dict) -> dict:
    """Chat 结果适配：messages + result -> {output, intermediate_steps}。"""
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
    return {"output": output, "intermediate_steps": steps}


def _to_graph_input(payload: dict) -> dict:
    user = payload.get("user")
    task_input = payload.get("task_input") or {}
    # 优先用 Planner 结构化入参里的 message，缺失时回落原始输入
    message = str(task_input.get("message") or "").strip()
    return {
        "input": message or (payload.get("input") or ""),
        "messages": list(payload.get("history") or []),
        "user_id": getattr(user, "id", None),
        "loops": 0,
        "task_input": task_input,
    }


def _build_chain(user):
    """聊天域专属管道：input -> chat workflow -> result。"""
    return (
        RunnableLambda(_to_graph_input)
        | build_chat_graph(user)
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
            "confirm": confirm,
            "task_action": task_action,
            "task_input": task_input or {},
            "task_confirmed": task_confirmed,
        },
        config={"recursion_limit": max(AGENT_MAX_ITERATIONS * 2 + 10, 16)},
    )
