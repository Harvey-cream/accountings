"""跨 Workflow 任务计划的 Schema 与依赖校验。

WorkflowPlan 由 Task Planner（LLM）产出，executor.execute_plan 按依赖顺序执行。
类型用 Literal 锁死在四个固定业务域，未知 type 在 Pydantic 校验层直接拒绝。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

WorkflowType = Literal["bill", "budget", "asset", "invoice"]


class WorkflowTask(BaseModel):
    """计划中的一个业务 Workflow 子任务。"""

    id: str = Field(description="任务唯一标识，简短英文，如 bill / budget")
    type: WorkflowType = Field(description="业务域：bill / budget / asset / invoice")
    goal: str = Field(
        default="",
        description="该任务要达成的目标，须自包含（含金额、时间范围等必要信息）",
    )
    depends_on: list[str] = Field(
        default_factory=list, description="依赖的前序任务 id 列表"
    )


class WorkflowPlan(BaseModel):
    """按执行顺序排列的任务计划，至少一个任务。"""

    tasks: list[WorkflowTask] = Field(min_length=1)


def topo_sort(plan: WorkflowPlan) -> list[WorkflowTask] | None:
    """Kahn 拓扑排序。重复 id / 未知依赖 / 循环依赖返回 None。"""
    by_id = {t.id: t for t in plan.tasks}
    if len(by_id) != len(plan.tasks):
        return None
    for task in plan.tasks:
        if any(dep not in by_id or dep == task.id for dep in task.depends_on):
            return None

    remaining = {t.id: set(t.depends_on) for t in plan.tasks}
    ordered: list[WorkflowTask] = []
    while remaining:
        # 按计划原顺序取第一个无未满足依赖的任务，保持 LLM 给出的次序稳定
        ready = [t for t in plan.tasks if t.id in remaining and not remaining[t.id]]
        if not ready:
            return None  # 有环
        for task in ready:
            ordered.append(task)
            del remaining[task.id]
            for deps in remaining.values():
                deps.discard(task.id)
    return ordered
