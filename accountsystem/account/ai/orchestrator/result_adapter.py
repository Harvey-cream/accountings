"""Adapters from legacy Workflow dictionaries to the shared result protocol."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .protocol import (
    ConfirmationRequest,
    JsonObject,
    StepError,
    StepResult,
    StepStatus,
    StepType,
)


def _json_safe(value: Any, seen: set[int] | None = None) -> Any:
    """Convert legacy values into the JSON-compatible protocol value set."""
    seen = seen or set()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")

    value_id = id(value)
    if value_id in seen:
        return "<recursive>"
    seen.add(value_id)
    try:
        if hasattr(value, "model_dump"):
            return _json_safe(value.model_dump(mode="json"), seen)
        if isinstance(value, Mapping):
            return {str(key): _json_safe(item, seen) for key, item in value.items()}
        if isinstance(value, (list, tuple, set, frozenset)):
            return [_json_safe(item, seen) for item in value]
        return repr(value)
    finally:
        seen.remove(value_id)


def _json_object(value: Any) -> JsonObject:
    value = _json_safe(value)
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return {"raw": value}
        safe = _json_safe(parsed)
        return safe if isinstance(safe, dict) else {"raw": safe}
    return {"raw": value}


def _needs_input(result: dict) -> bool:
    """Workflow 缺参数/目标时停在询问态，不是失败。标记可放在顶层或 data 内。"""
    if result.get("needs_input"):
        return True
    data = result.get("data")
    return isinstance(data, dict) and bool(data.get("needs_input"))


def _status(result: dict) -> StepStatus:
    confirm = result.get("confirm") or {}
    if confirm.get("need_confirm"):
        return StepStatus.WAITING_CONFIRMATION
    if _needs_input(result):
        return StepStatus.WAITING_INPUT
    if result.get("success") is False or result.get("error"):
        return StepStatus.FAILED
    return StepStatus.COMPLETED


def _data(result: dict) -> JsonObject:
    data: dict[str, Any] = {}
    raw_data = _json_safe(result.get("data"))
    if isinstance(raw_data, dict):
        data.update(raw_data)
    if result.get("crew_result") is not None:
        data["crew_result"] = _json_safe(result["crew_result"])
    if result.get("analysis_view") is not None:
        data["analysis_view"] = _json_object(result["analysis_view"])
    return data


def adapt_workflow_result(
    result: dict,
    *,
    plan_id: str,
    step_id: str,
    step_type: StepType,
    action: str,
) -> StepResult:
    result = result or {}
    status = _status(result)
    confirm = result.get("confirm") or {}
    confirmation = None
    if status == StepStatus.WAITING_CONFIRMATION:
        confirmation = ConfirmationRequest(
            prompt=str(result.get("output") or "请确认此操作"),
            payload=_json_object(confirm),
        )
    error = None
    if status == StepStatus.FAILED:
        raw_error = result.get("error")
        if isinstance(raw_error, dict):
            code = str(raw_error.get("code") or "workflow_failed")
            message = str(raw_error.get("message") or result.get("output") or "Workflow 执行失败")
        else:
            code = "workflow_failed"
            message = str(raw_error or result.get("output") or "Workflow 执行失败")
        error = StepError(code=code, message=message)
    message = str(result.get("output") or result.get("message") or "").strip()
    return StepResult(
        plan_id=plan_id,
        step_id=step_id,
        step_type=step_type,
        action=action,
        status=status,
        success=status == StepStatus.COMPLETED,
        data=_data(result),
        error=error,
        confirmation=confirmation,
        message=message,
        summary=message,
        intermediate_steps=_json_safe(result.get("intermediate_steps") or []),
    )
