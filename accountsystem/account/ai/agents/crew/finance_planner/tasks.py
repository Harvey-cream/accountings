"""Finance Planner 的顺序任务链：Analyst -> Planner -> Advisor。

任务通过 context 传递前序产出：Planner 依赖 Analyst，Advisor 依赖两者。
最后一个任务用 output_pydantic=CrewResult 约束结构化输出。
"""

from __future__ import annotations

from . import prompts
from .schemas import CrewResult


def build_finance_planner_tasks(analyst, planner, advisor, user_input, history_text=""):
    from crewai import Task

    analyze = Task(
        description=prompts.ANALYST_TASK.format(
            user_input=user_input or "", history=history_text or "（无）"
        ),
        expected_output=prompts.ANALYST_OUTPUT,
        agent=analyst,
    )
    plan = Task(
        description=prompts.PLANNER_TASK,
        expected_output=prompts.PLANNER_OUTPUT,
        agent=planner,
        context=[analyze],
    )
    advise = Task(
        description=prompts.ADVISOR_TASK,
        expected_output=prompts.ADVISOR_OUTPUT,
        agent=advisor,
        context=[analyze, plan],
        output_pydantic=CrewResult,
    )
    return [analyze, plan, advise]
