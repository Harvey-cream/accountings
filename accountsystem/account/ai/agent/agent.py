"""View ???LCEL ? orchestrator ? to_api_dict / SSE?

??? orchestrator ??Supervisor ?????????? agents/*?
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from langchain_core.runnables import RunnableLambda

from account.ai.knowledge import kb
from account.ai.llm.llm_utils import log_agent_exc
from account.ai.llm.response import chat, to_api_dict
from account.ai.llm.schemas import AGENT_ERROR_REPLY
from account.ai.orchestrator import run_orchestrator

_STATUS = {
    "create_bill": "??????...",
    "update_bill": "???????...",
    "query_bills": "???????...",
    "search_bills": "???????...",
    "delete_bill": "???????...",
    "analyze_expense": "??????...",
    "compare_periods": "????????...",
    "create_budget": "???????...",
    "update_budget": "???????...",
    "query_budget": "???????...",
    "budget_advice": "?????????...",
}


def _tool_call_name(tc) -> str:
    if isinstance(tc, dict):
        return str(tc.get("name") or "")
    return str(getattr(tc, "name", "") or "")


def _prepare(payload: dict) -> dict:
    text = payload.get("text") or payload.get("input") or ""
    return {"input": text, "user": payload.get("user")}


def _run_orchestrator(state: dict) -> dict:
    return run_orchestrator(state.get("input") or "", user=state.get("user"))


_agent_chain = (
    RunnableLambda(_prepare)
    | RunnableLambda(_run_orchestrator)
    | RunnableLambda(to_api_dict)
)


async def _yield_text_events(text: str, steps: list) -> AsyncIterator[dict]:
    for tc, _ in steps:
        yield {"type": "status", "text": _STATUS.get(_tool_call_name(tc), "??????...")}
    for i in range(0, len(text), 2):
        part = text[i : i + 2]
        if part:
            yield {"type": "token", "text": part}
            await asyncio.sleep(0.02)
    yield {"type": "agent_result", "data": {"output": text, "intermediate_steps": steps}}


def extract_accounting_info(text, user=None):
    """Sync path for mini-program fallback."""
    try:
        return _agent_chain.invoke({"text": text, "user": user})
    except Exception as e:
        log_agent_exc("AGENT", e, input=(text or "")[:60])
        out = chat(AGENT_ERROR_REPLY)
        out["remark"] = text
        return out


async def astream_accounting(text, user=None) -> AsyncIterator[dict]:
    """SSE: status / token / agent_result / error (H5 main path)."""
    try:
        result = await asyncio.to_thread(run_orchestrator, text or "", user)
        async for event in _yield_text_events(result["output"], result["intermediate_steps"]):
            yield event
    except Exception as e:
        log_agent_exc("AGENT", e, input=(text or "")[:60])
        yield {"type": "error", "message": AGENT_ERROR_REPLY, "remark": text}


def prewarm_runtime():
    """Warm up knowledge base on app start."""
    kb.prewarm()
