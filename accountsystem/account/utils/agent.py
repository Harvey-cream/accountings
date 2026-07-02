from collections.abc import AsyncIterator

from langchain_core.runnables import RunnableBranch, RunnableLambda

from . import kb, prompt
from .func import get_last_month_summary, quick_agent_greeting_prompt
from .llm import llm
from .llm_utils import extract_content, log_agent_exc
from .react import ReactRunnable
from .response import chat, to_api_dict
from .schemas import AGENT_ERROR_REPLY, DEFAULT_CHAT_REPLY, TextReply
from .tools import ToolContext

_react = ReactRunnable()


def _try_greeting(text: str) -> str | None:
    g = quick_agent_greeting_prompt(text)
    if not g.is_greeting:
        return None
    raw = extract_content(llm.invoke(prompt.build_greeting_prompt(text, g.prompt)))
    return TextReply(reply=raw or DEFAULT_CHAT_REPLY).reply


def _prepare(payload: dict) -> dict:
    text = payload.get("text") or payload.get("input") or ""
    user = payload.get("user")
    return {
        "input": text,
        "greeting": _try_greeting(text),
        "ctx": ToolContext(
            user=user,
            llm=llm,
            retrieve_kb=kb.retrieve,
            get_summary=get_last_month_summary,
        ),
    }


def _greeting_agent_result(state: dict) -> dict:
    return {"output": state["greeting"], "intermediate_steps": []}


def _greeting_api_dict(state: dict) -> dict:
    return to_api_dict(_greeting_agent_result(state))


_agent_chain = (
    RunnableLambda(_prepare)
    | RunnableBranch(
        (lambda s: s.get("greeting") is not None, RunnableLambda(_greeting_api_dict)),
        _react | RunnableLambda(to_api_dict),
    )
)


async def _yield_greeting(greeting: str) -> AsyncIterator[dict]:
    import asyncio

    for i in range(0, len(greeting), 2):
        part = greeting[i : i + 2]
        if part:
            yield {"type": "token", "text": part}
            await asyncio.sleep(0.02)
    yield {
        "type": "agent_result",
        "data": {"output": greeting, "intermediate_steps": []},
    }


def extract_accounting_info(text, user=None):
    try:
        return _agent_chain.invoke({"text": text, "user": user})
    except Exception as e:
        log_agent_exc("AGENT", e, input=(text or "")[:60])
        out = chat(AGENT_ERROR_REPLY)
        out["remark"] = text
        return out


async def astream_accounting(text, user=None) -> AsyncIterator[dict]:
    """SSE 事件：status / token / agent_result / error。"""
    try:
        state = _prepare({"text": text, "user": user})
        if state["greeting"]:
            async for event in _yield_greeting(state["greeting"]):
                yield event
            return
        async for event in _react.astream(
            {"input": state["input"], "ctx": state["ctx"]}
        ):
            yield event
    except Exception as e:
        log_agent_exc("AGENT", e, input=(text or "")[:60])
        yield {"type": "error", "message": AGENT_ERROR_REPLY, "remark": text}


def prewarm_runtime():
    kb.prewarm()
