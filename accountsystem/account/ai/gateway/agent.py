"""View → orchestrator → to_api_dict / SSE

负责最外层 Agent 入口与 SSE 流式输出；业务 Agent 在 agents/* 下。
"""

from __future__ import annotations

import asyncio
import queue
from collections.abc import AsyncIterator
from uuid import uuid4

from account.ai.knowledge import prewarm_knowledge
from account.ai.llm.llm_utils import log_agent_exc
from account.ai.llm.schemas import AGENT_ERROR_REPLY
from account.ai.observability import (
    init_telemetry,
    record_exception,
    set_span_outcome,
    start_span,
)
from account.ai.orchestrator import run_orchestrator
from account.ai.orchestrator.events import EventEmitter


async def _yield_text_events(result: dict) -> AsyncIterator[dict]:
    text = result.get("output") or ""
    # 需要确认时直接透出完整结果，不再分帧输出
    if result.get("confirm", {}).get("need_confirm"):
        yield {"type": "agent_result", "data": result}
        return
    for i in range(0, len(text), 2):
        part = text[i : i + 2]
        if part:
            yield {"type": "token", "text": part}
            await asyncio.sleep(0.02)
    yield {"type": "agent_result", "data": result}


def _run_outcome(result: dict, confirm: dict | None) -> str:
    if isinstance(confirm, dict) and confirm.get("confirm") is False:
        return "cancelled"
    if (result.get("confirm") or {}).get("need_confirm"):
        return "waiting_confirmation"

    plan_result = result.get("plan_result") or {}
    task_statuses = {
        str(item.get("status") or "")
        for item in (plan_result.get("task_results") or [])
        if isinstance(item, dict)
    }
    for waiting in ("waiting_confirmation", "waiting_input", "waiting_selection"):
        if waiting in task_statuses:
            return waiting
    status = str(plan_result.get("status") or "")
    return {
        "success": "completed",
        "partial": "partial",
        "failed": "failed",
        "cancelled": "cancelled",
    }.get(status, "completed")


async def astream_accounting(text, user=None, confirm=None) -> AsyncIterator[dict]:
    """SSE: status / token / agent_event / agent_result / error。"""
    events = queue.Queue()
    finished = object()
    confirm_extra = (confirm or {}).get("confirm_extra") or {}
    trace_id = confirm_extra.get("trace_id") or str(uuid4())
    plan_id = confirm_extra.get("plan_id") or trace_id
    def publish(event):
        events.put(event)

    emitter = EventEmitter(publish=publish)

    def run():
        init_telemetry()
        run_id = str(uuid4())
        with start_span(
            "agent.run",
            {
                "agent.run_id": run_id,
                "agent.logical_trace_id": trace_id,
                "agent.plan_id": plan_id,
            },
        ) as span:
            try:
                emitter.start_trace(
                    trace_id=trace_id,
                    plan_id=plan_id,
                    user_id=getattr(user, "id", None),
                )
                result = run_orchestrator(
                    text or "",
                    user,
                    None,
                    confirm,
                    trace_id=trace_id,
                    event_emitter=emitter,
                    plan_id=plan_id,
                    run_id=run_id,
                )
                outcome = _run_outcome(result, confirm)
                if result.get("confirm", {}).get("need_confirm"):
                    emitter.finish_trace(trace_id, "waiting_confirmation")
                else:
                    result_status = (result.get("plan_result") or {}).get("status")
                    trace_status = {
                        "success": "completed",
                        "partial": "partial",
                        "failed": "failed",
                    }.get(result_status, "completed")
                    emitter.finish_trace(trace_id, trace_status)
                set_span_outcome(span, outcome)
                events.put({"type": "agent_result", "data": result})
            except Exception as exc:
                record_exception(span, exc)
                set_span_outcome(span, "failed", error=True)
                emitter.finish_trace(trace_id, "failed")
                log_agent_exc("AGENT", exc, input=(text or "")[:60])
                events.put({"type": "error", "message": AGENT_ERROR_REPLY, "remark": text})
            finally:
                events.put(finished)

    task = asyncio.create_task(asyncio.to_thread(run))
    try:
        while True:
            item = await asyncio.to_thread(events.get)
            if item is finished:
                break
            if isinstance(item, dict) and item.get("type") == "agent_result":
                async for result_event in _yield_text_events(item["data"]):
                    yield result_event
            elif isinstance(item, dict) and item.get("event_type"):
                yield {"type": "agent_event", "event": item}
            else:
                yield item
    finally:
        await task


def prewarm_runtime():
    """Warm up knowledge base on app start."""
    prewarm_knowledge()
