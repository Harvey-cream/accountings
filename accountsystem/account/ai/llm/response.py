"""Convert standardized execution results to the public API response."""

from __future__ import annotations

from .schemas import DEFAULT_CHAT_REPLY, chat_response


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
