"""Supervisor Agent：仅做意图识别与路由，不执行业务、不访问数据。"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import log_agent_exc

from .supervisor_prompt import SUPERVISOR_SYSTEM
from .supervisor_schemas import RouteDecision

_router_llm = llm.with_structured_output(RouteDecision)


def route(user_input: str, context: str = "") -> RouteDecision:
    """把用户输入路由到 bill / analysis / budget。失败时兜底到 bill。"""
    try:
        human = user_input or ""
        if context:
            human = f"近期对话上下文：\n{context}\n\n当前用户说：{user_input or ''}"
        decision = _router_llm.invoke(
            [SystemMessage(content=SUPERVISOR_SYSTEM), HumanMessage(content=human)]
        )
        if isinstance(decision, RouteDecision):
            return decision
    except Exception as e:
        log_agent_exc("SUPERVISOR", e, input=(user_input or "")[:60])
    return RouteDecision(task_type="bill", reason="fallback")
