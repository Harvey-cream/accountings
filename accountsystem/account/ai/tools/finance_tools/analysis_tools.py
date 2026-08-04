"""分析 Tools → expense_service.analyze_expense。每个 Tool 独立定义。"""

from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from account.services import expense_service

from .common import run_service


# ----- analyze_expense -----


class AnalyzeExpenseInput(BaseModel):
    days: int = Field(default=30, ge=1, le=365, description="统计最近多少天，默认 30")


def analyze_expense_tool(user) -> StructuredTool:
    def analyze_expense(days: int = 30) -> str:
        return run_service(
            lambda: {"summary": expense_service.analyze_expense(user, days=days)},
            ok_message="分析完成",
        )

    return StructuredTool.from_function(
        func=analyze_expense,
        name="analyze_expense",
        description="汇总近 N 天收支：笔数、总额、算式与分类支出，用于回答花了多少等问题。",
        args_schema=AnalyzeExpenseInput,
    )


def build_analysis_tools(user) -> list[StructuredTool]:
    return [analyze_expense_tool(user)]
