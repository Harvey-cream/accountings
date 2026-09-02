"""Aggregate standardized task results into a plan result."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .protocol import PlanStatus, StepResult, StepStatus


class PlanResult(BaseModel):
    plan_id: str | None = None
    status: Literal["success", "partial", "failed"]
    task_results: list[StepResult] = Field(default_factory=list)
    summary: str = ""
    analysis_view: dict = Field(default_factory=dict)
    intermediate_steps: list = Field(default_factory=list)


def aggregate_plan_results(
    task_results: list[StepResult], *, plan_id: str | None = None
) -> PlanResult:
    completed = [item for item in task_results if item.status == StepStatus.COMPLETED]
    failed = [item for item in task_results if item.status == StepStatus.FAILED]
    waiting = [
        item
        for item in task_results
        if item.status in {StepStatus.WAITING_CONFIRMATION, StepStatus.WAITING_INPUT}
    ]
    if failed and completed:
        status = "partial"
    elif failed and not completed:
        status = "failed"
    elif waiting:
        status = "partial"
    else:
        status = "success"
    summary = "\n".join(
        item.summary or item.message for item in task_results if item.summary or item.message
    )
    intermediate_steps = [
        step for item in task_results for step in item.intermediate_steps
    ]
    analysis_view = next(
        (
            item.data.get("analysis_view")
            for item in task_results
            if isinstance(item.data.get("analysis_view"), dict)
            and item.data.get("analysis_view")
        ),
        {},
    )
    return PlanResult(
        plan_id=plan_id,
        status=status,
        task_results=task_results,
        summary=summary,
        analysis_view=analysis_view,
        intermediate_steps=intermediate_steps,
    )
