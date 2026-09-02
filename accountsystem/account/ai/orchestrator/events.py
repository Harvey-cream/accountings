"""第一版 Agent Trace 事件协议与发布器。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Literal

from django.utils import timezone as django_timezone
from pydantic import BaseModel, Field

from account.models import AgentTrace, AgentTraceEvent


AgentEventType = Literal[
    "plan.started",
    "plan.completed",
    "plan.failed",
    "task.started",
    "task.completed",
    "task.failed",
    "agent.started",
    "agent.completed",
    "agent.failed",
]


class AgentEvent(BaseModel):
    trace_id: str = Field(min_length=1)
    plan_id: str = ""
    task_id: str = ""
    agent: str = ""
    event_type: AgentEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message: str = ""
    data: dict = Field(default_factory=dict)


class EventEmitter:
    """发布事件到 Trace 存储和可选的实时消费端。"""

    def __init__(self, publish: Callable[[dict], None] | None = None):
        self._publish = publish

    def start_trace(
        self,
        *,
        trace_id: str,
        plan_id: str = "",
        user_id=None,
        status: str = "running",
    ) -> AgentTrace:
        trace, _ = AgentTrace.objects.get_or_create(
            trace_id=trace_id,
            defaults={
                "plan_id": plan_id,
                "user_id": "" if user_id is None else str(user_id),
                "status": status,
                "started_at": django_timezone.now(),
            },
        )
        if not trace.plan_id and plan_id:
            trace.plan_id = plan_id
            trace.save(update_fields=["plan_id"])
        if status == "running" and trace.finished_at is not None:
            trace.status = "running"
            trace.finished_at = None
            trace.duration_ms = None
            trace.save(update_fields=["status", "finished_at", "duration_ms"])
        return trace

    def finish_trace(self, trace_id: str, status: str) -> AgentTrace | None:
        trace = AgentTrace.objects.filter(trace_id=trace_id).first()
        if trace is None:
            return None
        if trace.finished_at is not None:
            return trace
        finished_at = django_timezone.now()
        trace.status = status
        trace.finished_at = finished_at
        trace.duration_ms = max(
            0, int((finished_at - trace.started_at).total_seconds() * 1000)
        )
        trace.save(update_fields=["status", "finished_at", "duration_ms"])
        return trace

    def emit(
        self,
        event_type: AgentEventType,
        *,
        trace_id: str,
        plan_id: str = "",
        task_id: str = "",
        agent: str = "",
        message: str = "",
        data: dict | None = None,
    ) -> AgentEvent:
        event = AgentEvent(
            trace_id=trace_id,
            plan_id=plan_id,
            task_id=task_id,
            agent=agent,
            event_type=event_type,
            message=message,
            data=data or {},
        )
        AgentTraceEvent.objects.create(
            trace_id=event.trace_id,
            plan_id=event.plan_id,
            task_id=event.task_id,
            event_type=event.event_type,
            agent=event.agent,
            message=event.message,
            data=event.data,
            created_at=event.timestamp,
        )
        if self._publish is not None:
            self._publish(event.model_dump(mode="json"))
        return event
