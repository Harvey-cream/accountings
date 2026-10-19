"""Tool 统一响应与异常包装（返回 JSON 字符串，供 LLM 阅读）。"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from account.ai.observability import (
    mark_span_ok,
    record_exception,
    set_span_attribute,
    start_span,
)
from account.ai.observability.context import get_tool_context
from account.services.errors import ServiceError


def tool_result(*, success: bool, data: Any = None, message: str = "") -> str:
    return json.dumps(
        {"success": success, "data": data if data is not None else {}, "message": message},
        ensure_ascii=False,
        default=str,
    )


def run_service(fn: Callable[[], Any], *, ok_message: str = "ok") -> str:
    context = get_tool_context()
    if context is None:
        return _run_service(fn, ok_message=ok_message)

    with start_span(
        "service.call",
        {
            "service.name": context.service_name or f"{context.domain}_service",
            "service.operation": context.name,
            "service.domain": context.domain,
        },
    ) as span:
        try:
            data = fn()
        except ServiceError as exc:
            set_span_attribute(span, "service.status", "business_error")
            mark_span_ok(span)
            return tool_result(success=False, data={}, message=exc.message)
        except Exception as exc:
            set_span_attribute(span, "service.status", "failed")
            record_exception(span, exc)
            return tool_result(
                success=False,
                data={},
                message=f"操作失败，请稍后重试或换种说法。详情: {exc}",
            )
        set_span_attribute(span, "service.status", "completed")
        mark_span_ok(span)
        return tool_result(success=True, data=data, message=ok_message)


def _run_service(fn: Callable[[], Any], *, ok_message: str) -> str:
    """Original no-tracing behavior for callers outside an instrumented AI Tool."""
    try:
        data = fn()
        return tool_result(success=True, data=data, message=ok_message)
    except ServiceError as e:
        return tool_result(success=False, data={}, message=e.message)
    except Exception as e:
        return tool_result(success=False, data={}, message=f"操作失败，请稍后重试或换种说法。详情: {e}")
