"""Tool 统一响应与异常包装（返回 JSON 字符串，供 LLM 阅读）。"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from account.services.errors import ServiceError


def tool_result(*, success: bool, data: Any = None, message: str = "") -> str:
    return json.dumps(
        {"success": success, "data": data if data is not None else {}, "message": message},
        ensure_ascii=False,
        default=str,
    )


def run_service(fn: Callable[[], Any], *, ok_message: str = "ok") -> str:
    try:
        data = fn()
        return tool_result(success=True, data=data, message=ok_message)
    except ServiceError as e:
        return tool_result(success=False, data={}, message=e.message)
    except Exception as e:
        return tool_result(success=False, data={}, message=f"操作失败，请稍后重试或换种说法。详情: {e}")
