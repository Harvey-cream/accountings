"""任务规划器的输出约束：Planner 只能在固定角色池里选人并给出本次目标。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CrewRole = Literal[
    "financial_analyst",
    "budget_planner",
    "knowledge_researcher",
    "financial_advisor",
]

ROLE_KEYS: tuple[str, ...] = (
    "financial_analyst",
    "budget_planner",
    "knowledge_researcher",
    "financial_advisor",
)


class TaskSpec(BaseModel):
    """一个角色本次要完成的子任务。"""

    role: CrewRole = Field(description="必须是角色池中已存在的角色")
    goal: str = Field(description="这个角色本次要达成的具体目标")
    expected_output: str = Field(default="", description="期望产出；留空时用角色默认值")


class TaskPlan(BaseModel):
    """Planner 产出的任务计划，按执行先后排列。"""

    tasks: list[TaskSpec] = Field(default_factory=list, description="按执行顺序排列的子任务")
