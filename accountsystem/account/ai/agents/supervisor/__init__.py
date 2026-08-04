"""调度 Agent（Supervisor）包：自身负责路由；子 Agent 位于本目录下。

结构：
  supervisor/
    supervisor_agent.py / supervisor_prompt.py / supervisor_schemas.py
    bill/       # 账单子 Agent
    analysis/   # 分析子 Agent
    budget/     # 预算子 Agent
"""

from . import analysis, bill, budget
from .supervisor_agent import route
from .supervisor_schemas import RouteDecision, TaskType

__all__ = [
    "route",
    "RouteDecision",
    "TaskType",
    "bill",
    "analysis",
    "budget",
]
