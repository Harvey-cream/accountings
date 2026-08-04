"""财务类 AI Tools：账单 / 预算 / 分析。统一经 Service 访问数据库。"""

from .analysis_tools import (
    analyze_expense_tool,
    build_analysis_tools,
    compare_periods_tool,
)
from .bill_tools import (
    build_bill_tools,
    create_bill_tool,
    delete_bill_tool,
    query_bills_tool,
    search_bills_tool,
    update_bill_tool,
)
from .budget_tools import (
    budget_advice_tool,
    build_budget_tools,
    create_budget_tool,
    query_budget_tool,
    update_budget_tool,
)


def build_finance_tools(user) -> list:
    """组装全部财务 Tools，user 由调用方注入（鉴权后的 Django User）。"""
    return [
        *build_bill_tools(user),
        *build_budget_tools(user),
        *build_analysis_tools(user),
    ]


__all__ = [
    "build_finance_tools",
    "build_bill_tools",
    "build_budget_tools",
    "build_analysis_tools",
    "create_bill_tool",
    "update_bill_tool",
    "query_bills_tool",
    "search_bills_tool",
    "delete_bill_tool",
    "create_budget_tool",
    "update_budget_tool",
    "query_budget_tool",
    "budget_advice_tool",
    "analyze_expense_tool",
    "compare_periods_tool",
]
