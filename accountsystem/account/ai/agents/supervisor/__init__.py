"""业务 Workflow 包（历史目录名 supervisor，实际为各领域 Workflow）。

结构：
  supervisor/
    bill/       # 账单 Workflow
    budget/     # 预算 Workflow
    asset/      # 资产 Workflow
    invoice/    # 发票 Workflow
    chat/       # 闲聊 Workflow

路由已统一由顶层 Unified Planner 承担，此包不再包含 Supervisor Router。
分析能力不再作为独立 Workflow：analysis_tools 由 CrewAI 的 Financial Analyst 使用。
"""

from . import asset, bill, budget, chat, invoice

__all__ = [
    "bill",
    "budget",
    "asset",
    "invoice",
    "chat",
]
