"""Finance Planner Crew：三角色顺序协作产出财务规划报告。

对外只暴露 run_finance_planner（供 orchestrator.executor 调用）。
"""

from .crew import run_finance_planner
from .schemas import CrewResult

__all__ = ["run_finance_planner", "CrewResult"]
