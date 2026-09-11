"""Convert standardized execution results to the public API response."""

from __future__ import annotations

import json

from .schemas import DEFAULT_CHAT_REPLY, chat_response


def _legacy_record(agent_result: dict) -> dict | None:
    for step in agent_result.get("intermediate_steps") or []:
        if not isinstance(step, (list, tuple)) or len(step) != 2:
            continue
        call, raw = step
        name = call.get("name") if isinstance(call, dict) else ""
        if name not in {"create_bill", "batch_create_bills"}:
            continue
        try:
            payload = json.loads(raw) if isinstance(raw, str) else raw
        except (TypeError, ValueError):
            continue
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            continue
        return {
            "money": float(data.get("amount") or 0),
            "category": data.get("category") or "其他",
            "record_id": data.get("id"),
        }
    return None


def _result_response(plan_result: dict) -> dict:
    task_results = plan_result.get("task_results") or []
    summaries = [
        item.get("summary") or item.get("message")
        for item in task_results
        if item.get("summary") or item.get("message")
    ]
    analysis_view = plan_result.get("analysis_view") or {}
    return {
        "reply": plan_result.get("summary") or "\n".join(summaries) or DEFAULT_CHAT_REPLY,
        "analysis_view": analysis_view,
        "plan_result": plan_result,
    }


def to_api_dict(agent_result: dict) -> dict:
    agent_result = agent_result or {}
    if agent_result.get("plan_result"):
        return _result_response(agent_result["plan_result"])
    legacy_record = _legacy_record(agent_result)
    if legacy_record is not None:
        out = chat_response(agent_result.get("output") or DEFAULT_CHAT_REPLY)
        out.update(legacy_record)
        return out
    if agent_result.get("step_result"):
        return _result_response(
            {
                "status": "success" if agent_result["step_result"].get("success") else "failed",
                "task_results": [agent_result["step_result"]],
                "summary": agent_result["step_result"].get("summary") or "",
                "analysis_view": agent_result.get("analysis_view") or {},
            }
        )

    # Legacy responses remain supported until all callers migrate to StepResult.
    if agent_result.get("confirm", {}).get("need_confirm"):
        out = chat_response(agent_result.get("output") or "确认一下这些操作吧～")
        out["need_confirm"] = True
        out["confirmations"] = agent_result["confirm"].get("confirmations") or []
        out["plan_tasks"] = agent_result.get("plan_tasks") or []
        out["trace_id"] = agent_result.get("trace_id") or ""
        out["plan_id"] = agent_result.get("plan_id") or ""
        return out

    return chat_response(agent_result.get("output") or DEFAULT_CHAT_REPLY)


def chat(reply: str) -> dict:
    return chat_response(reply)
