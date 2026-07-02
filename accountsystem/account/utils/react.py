import asyncio
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import Runnable

from . import prompt
from .llm import AGENT_MAX_ITERATIONS, llm
from .llm_utils import extract_content
from .tools import ToolContext, build_tools

_STATUS = {
    "record_transaction": "鸭鸭正在记账...",
    "query_bill_summary": "鸭鸭正在查账单...",
    "answer_app_help": "鸭鸭正在翻知识库...",
}


def _tool_call_fields(tc) -> tuple[str, dict, str]:
    if isinstance(tc, dict):
        return str(tc["name"]), dict(tc.get("args") or {}), str(tc["id"])
    return str(tc.name), dict(tc.args or {}), str(tc.id)


def _setup(user_input: str, ctx: ToolContext):
    tools = build_tools(ctx)
    tool_map = {t.name: t for t in tools}
    llm_tools = llm.bind_tools(tools)
    messages = [
        SystemMessage(content=prompt.REACT_SYSTEM),
        HumanMessage(content=user_input),
    ]
    return llm_tools, tool_map, messages


async def _process_tool_calls(
    ai_msg: AIMessage, tool_map, messages, steps: list, user_input: str
) -> list[str]:
    messages.append(ai_msg)
    names: list[str] = []
    for tc in ai_msg.tool_calls:
        name, args, tool_id = _tool_call_fields(tc)
        names.append(name)
        user_message = args.get("user_message") or user_input
        obs = await asyncio.to_thread(
            tool_map[name].invoke, {"user_message": user_message}
        )
        steps.append((tc, obs))
        messages.append(ToolMessage(content=obs, tool_call_id=tool_id))
    return names


async def _emit_text_reply(
    text: str, steps: list, *, emit_tokens: bool
) -> AsyncIterator[dict]:
    if emit_tokens:
        for i in range(0, len(text), 2):
            part = text[i : i + 2]
            if part:
                yield {"type": "token", "text": part}
                await asyncio.sleep(0.02)
    yield {
        "type": "agent_result",
        "data": {"output": text, "intermediate_steps": steps},
    }


async def _react_loop(
    user_input: str, ctx: ToolContext, *, emit_tokens: bool
) -> AsyncIterator[dict]:
    llm_tools, tool_map, messages = _setup(user_input, ctx)
    steps: list[tuple] = []

    for _ in range(AGENT_MAX_ITERATIONS):
        ai_msg = await llm_tools.ainvoke(messages)
        if not ai_msg.tool_calls:
            text = extract_content(ai_msg).strip()
            async for event in _emit_text_reply(text, steps, emit_tokens=emit_tokens):
                yield event
            return

        for name in await _process_tool_calls(ai_msg, tool_map, messages, steps, user_input):
            if emit_tokens:
                yield {"type": "status", "text": _STATUS.get(name, "鸭鸭正在思考...")}

    ai_msg = await llm_tools.ainvoke(messages)
    text = extract_content(ai_msg).strip()
    async for event in _emit_text_reply(text, steps, emit_tokens=emit_tokens):
        yield event


class ReactRunnable(Runnable[dict[str, Any], dict[str, Any]]):
    """LCEL Runnable：ReAct 循环（同步/流式共用一套逻辑）。"""

    def invoke(self, input: dict[str, Any], config=None) -> dict[str, Any]:
        async def _collect() -> dict[str, Any]:
            async for event in _react_loop(
                input["input"], input["ctx"], emit_tokens=False
            ):
                if event["type"] == "agent_result":
                    return event["data"]
            return {"output": "", "intermediate_steps": []}

        return asyncio.run(_collect())

    async def ainvoke(self, input: dict[str, Any], config=None) -> dict[str, Any]:
        async for event in _react_loop(input["input"], input["ctx"], emit_tokens=False):
            if event["type"] == "agent_result":
                return event["data"]
        return {"output": "", "intermediate_steps": []}

    async def astream(
        self, input: dict[str, Any], config=None
    ) -> AsyncIterator[dict[str, Any]]:
        async for event in _react_loop(input["input"], input["ctx"], emit_tokens=True):
            yield event
