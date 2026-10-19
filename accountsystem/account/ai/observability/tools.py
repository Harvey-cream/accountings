"""Thin StructuredTool instrumentation shared by ToolNode and direct invoke paths."""

from __future__ import annotations

import json
from contextlib import contextmanager
from functools import wraps

from account.ai.tools.tool_policy import tool_is_read_only

from .context import ToolContext, get_workflow_context, use_tool_context
from .telemetry import (
    mark_span_ok,
    record_exception,
    set_span_attribute,
    start_span,
)


@contextmanager
def _use_captured_otel_context(captured):
    if captured is None:
        yield
        return
    token = None
    try:
        from opentelemetry import context as otel_context
        from opentelemetry import trace

        # LangGraph may already propagate context into its worker. Only restore the
        # build-time workflow context when the execution thread has no active span.
        if not trace.get_current_span().get_span_context().is_valid:
            token = otel_context.attach(captured)
    except Exception:
        token = None
    try:
        yield
    finally:
        if token is not None:
            try:
                otel_context.detach(token)
            except Exception:
                pass


def _operation(name: str) -> str:
    for prefix in (
        "batch_create",
        "adjust",
        "create",
        "update",
        "delete",
        "query",
        "search",
        "get",
        "list",
    ):
        if name == prefix or name.startswith(f"{prefix}_"):
            return prefix
    return name.split("_", 1)[0]


def _tool_status(result) -> str:
    value = result
    if isinstance(result, str):
        try:
            value = json.loads(result)
        except (TypeError, ValueError):
            return "completed"
    if isinstance(value, dict):
        confirm = value.get("confirm")
        if isinstance(confirm, dict) and confirm.get("need_confirm"):
            return "waiting_confirmation"
        data = value.get("data") or {}
        if value.get("needs_input") or (isinstance(data, dict) and data.get("needs_input")):
            return "waiting_input"
        if value.get("success") is False or value.get("error"):
            return "failed"
    return "completed"


def instrument_tool(tool, *, domain: str, service_name: str = ""):
    """Wrap the StructuredTool body once while preserving its public Tool contract."""
    original = tool.func
    if getattr(original, "_finpilot_otel_instrumented", False):
        return tool
    captured_workflow = get_workflow_context()
    captured_otel_context = None
    if captured_workflow is not None:
        try:
            from opentelemetry import context as otel_context

            captured_otel_context = otel_context.get_current()
        except Exception:
            captured_otel_context = None
    name = str(tool.name)
    operation = _operation(name)
    read_only = tool_is_read_only(name)

    @wraps(original)
    def traced(*args, **kwargs):
        workflow = get_workflow_context() or captured_workflow
        context = ToolContext(
            name=name,
            domain=(workflow.domain if workflow is not None else domain),
            operation=operation,
            read_only=read_only,
            confirmed=(workflow.confirmed if workflow is not None else False),
            service_name=service_name,
        )
        with _use_captured_otel_context(captured_otel_context):
            with start_span(
                "tool.execute",
                {
                    "tool.name": context.name,
                    "tool.domain": context.domain,
                    "tool.operation": context.operation,
                    "tool.read_only": context.read_only,
                    "tool.confirmed": context.confirmed,
                },
            ) as span:
                with use_tool_context(context):
                    try:
                        result = original(*args, **kwargs)
                    except Exception as exc:
                        set_span_attribute(span, "tool.status", "failed")
                        record_exception(span, exc)
                        raise
                set_span_attribute(span, "tool.status", _tool_status(result))
                mark_span_ok(span)
                return result

    traced._finpilot_otel_instrumented = True
    tool.func = traced
    return tool


def instrument_tools(tools: list, *, domain: str, service_name: str = "") -> list:
    return [instrument_tool(tool, domain=domain, service_name=service_name) for tool in tools]
