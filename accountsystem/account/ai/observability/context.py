"""Small runtime context used to attach safe workflow/tool metadata to spans."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class WorkflowContext:
    domain: str
    action: str
    task_id: str
    confirmed: bool


@dataclass(frozen=True)
class ToolContext:
    name: str
    domain: str
    operation: str
    read_only: bool
    confirmed: bool
    service_name: str


_WORKFLOW_CONTEXT: ContextVar[WorkflowContext | None] = ContextVar(
    "finpilot_workflow_context", default=None
)
_TOOL_CONTEXT: ContextVar[ToolContext | None] = ContextVar(
    "finpilot_tool_context", default=None
)


def confirmation_granted(task_confirmed: bool, confirm: dict | None) -> bool:
    confirm = confirm or {}
    return bool(
        task_confirmed
        or confirm.get("confirmed_plan")
        or confirm.get("confirm") is True
    )


def workflow_status(result: dict) -> str:
    result = result if isinstance(result, dict) else {}
    confirm = result.get("confirm")
    if isinstance(confirm, dict) and confirm.get("need_confirm"):
        return "waiting_confirmation"
    data = result.get("data") or {}
    if result.get("needs_input") or (isinstance(data, dict) and data.get("needs_input")):
        return "waiting_input"
    if result.get("needs_selection"):
        return "waiting_selection"
    if result.get("success") is False or result.get("error"):
        return "failed"
    return "completed"


@contextmanager
def use_workflow_context(context: WorkflowContext) -> Iterator[None]:
    token = _WORKFLOW_CONTEXT.set(context)
    try:
        yield
    finally:
        _WORKFLOW_CONTEXT.reset(token)


def get_workflow_context() -> WorkflowContext | None:
    return _WORKFLOW_CONTEXT.get()


@contextmanager
def use_tool_context(context: ToolContext) -> Iterator[None]:
    token = _TOOL_CONTEXT.set(context)
    try:
        yield
    finally:
        _TOOL_CONTEXT.reset(token)


def get_tool_context() -> ToolContext | None:
    return _TOOL_CONTEXT.get()
