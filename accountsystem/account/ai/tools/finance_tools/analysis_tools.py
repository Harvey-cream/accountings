"""分析 Tools → expense_service。每个 Tool 独立定义。"""

from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from account.services import expense_service

from .common import run_service


# ----- analyze_expense -----


class AnalyzeExpenseInput(BaseModel):
    days: int = Field(default=30, ge=1, le=365, description="统计最近多少天，默认 30")
    category: str | None = Field(
        default=None, description="可选分类名，如餐饮；传入则只统计该分类"
    )


def analyze_expense_tool(user) -> StructuredTool:
    def analyze_expense(days: int = 30, category: str | None = None) -> str:
        return run_service(
            lambda: {
                "summary": expense_service.analyze_expense(
                    user, days=days, category_name=category
                )
            },
            ok_message="分析完成",
        )

    return StructuredTool.from_function(
        func=analyze_expense,
        name="analyze_expense",
        description="汇总近 N 天收支：笔数、总额、算式与分类支出；可按分类筛选。",
        args_schema=AnalyzeExpenseInput,
    )


# ----- compare_periods -----


class ComparePeriodsInput(BaseModel):
    days: int = Field(
        default=30, ge=1, le=365, description="对比窗口天数：近 N 天 vs 上一段 N 天"
    )


def compare_periods_tool(user) -> StructuredTool:
    def compare_periods(days: int = 30) -> str:
        return run_service(
            lambda: expense_service.compare_expense(user, days=days),
            ok_message="对比完成",
        )

    return StructuredTool.from_function(
        func=compare_periods,
        name="compare_periods",
        description="对比近 N 天与上一段同等天数的收支，用于回答比上月/上周怎样。",
        args_schema=ComparePeriodsInput,
    )


def build_analysis_tools(user) -> list[StructuredTool]:
    return [analyze_expense_tool(user), compare_periods_tool(user)]
