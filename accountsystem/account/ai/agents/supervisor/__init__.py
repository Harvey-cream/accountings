"""调度 Agent（Supervisor）包：自身负责路由；子 Agent 位于本目录下。

结构：
  supervisor/
    supervisor_agent.py / supervisor_prompt.py / supervisor_schemas.py
    bill/       # 账单子 Agent
    budget/     # 预算子 Agent
    asset/      # 资产子 Agent
    invoice/    # 发票子 Agent

分析能力不再作为独立 Workflow：analysis_tools 由 CrewAI 的 Financial Analyst 使用。
"""

from . import asset, bill, budget, invoice
from .supervisor_agent import route
from .supervisor_schemas import RouteDecision, TaskType

__all__ = [
    "route",
    "RouteDecision",
    "TaskType",
    "bill",
    "budget",
    "asset",
    "invoice",
]
