"""Bill Agent：账单域独立管道（本文件自有 LCEL + LangGraph，不与其他 Agent 共用）。"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import create_react_agent

from account.ai.llm.llm import AGENT_MAX_ITERATIONS, llm
from account.ai.llm.llm_utils import extract_content
from account.ai.tools.finance_tools import build_bill_tools

from .bill_prompt import BILL_SYSTEM


def _tool_call_id(tc) -> str:
    if isinstance(tc, dict):
        return str(tc.get("id") or "")
    return str(getattr(tc, "id", "") or "")


def _graph_to_result(graph_state: dict) -> dict:
    """Bill 结果适配：messages -> {output, intermediate_steps}。"""
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
    output = extract_content(messages[-1]).strip() if messages else ""
    return {"output": output, "intermediate_steps": steps}


def _build_chain(user):
    """账单域专属管道：input -> bill graph(create/update/query) -> result。"""
    bill_graph = create_react_agent(
        llm,
        build_bill_tools(user),
        prompt=BILL_SYSTEM,
    )
    return (
        RunnableLambda(
            lambda s: {
                "messages": list(s.get("history") or [])
                + [HumanMessage(content=s.get("input") or "")]
            }
        )
        | bill_graph
        | RunnableLambda(_graph_to_result)
    )


def run(user_input: str, user=None, history=None) -> dict:
    chain = _build_chain(user)
    return chain.invoke(
        {"input": user_input or "", "history": history or []},
        config={"recursion_limit": max(AGENT_MAX_ITERATIONS * 2 + 2, 10)},
    )
