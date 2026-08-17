"""按 Planner 产出的 TaskSpec 动态构建 CrewAI Task。

不再写死 Analyst -> Planner -> Advisor：任务数量与顺序都来自 TaskSpec[]。
每个任务的 context 是它之前的全部任务，收尾的 financial_advisor 用
output_pydantic=CrewResult 约束最终结构化产出。
"""

from __future__ import annotations

from . import prompts
from .schemas import CrewResult


def build_tasks(specs, agents: dict, user_input: str, history_text: str = "") -> list:
    from crewai import Task

    tasks: list = []
    for spec in specs:
        agent = agents.get(spec.role)
        if agent is None:
            continue
        kwargs = {
            "description": prompts.TASK_DESCRIPTION.format(
                user_input=user_input or "",
                history=history_text or "（无）",
                goal=spec.goal,
                role_hint=prompts.ROLE_HINTS[spec.role],
            ),
            "expected_output": spec.expected_output,
            "agent": agent,
        }
        if tasks:
            kwargs["context"] = list(tasks)
        if spec.role == "financial_advisor":
            kwargs["output_pydantic"] = CrewResult
        tasks.append(Task(**kwargs))
    return tasks
