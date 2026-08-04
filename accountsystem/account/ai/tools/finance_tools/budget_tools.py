"""预算 Tools → budget_service。每个 Tool 独立定义。"""

from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from account.services import budget_service

from .common import run_service


# ----- create_budget -----


class CreateBudgetInput(BaseModel):
    amount: float = Field(..., ge=0, description="预算金额")
    period: str = Field(..., description='预算周期，月如 "2026-03"，年如 "2026"')
    budget_type: str = Field(default="month", description="month 或 year")
    is_total: bool = Field(default=True, description="是否总预算；False 为分类预算")
    category: str | None = Field(
        default=None, description="分类预算时的分类名；总预算可不传"
    )


def create_budget_tool(user) -> StructuredTool:
    def create_budget(
        amount: float,
        period: str,
        budget_type: str = "month",
        is_total: bool = True,
        category: str | None = None,
    ) -> str:
        return run_service(
            lambda: budget_service.create_budget(
                user,
                amount=amount,
                budget_type=budget_type,
                period=period,
                is_total=is_total,
                category_name=category,
            ),
            ok_message="预算已保存",
        )

    return StructuredTool.from_function(
        func=create_budget,
        name="create_budget",
        description="创建或设置预算（总预算或分类预算）。需提供 period。",
        args_schema=CreateBudgetInput,
    )


# ----- update_budget -----


class UpdateBudgetInput(BaseModel):
    amount: float = Field(..., ge=0, description="预算金额")
    period: str = Field(..., description='预算周期，月如 "2026-03"，年如 "2026"')
    budget_type: str = Field(default="month", description="month 或 year")
    is_total: bool = Field(default=True, description="是否总预算")
    category: str | None = Field(default=None, description="分类预算时的分类名")


def update_budget_tool(user) -> StructuredTool:
    def update_budget(
        amount: float,
        period: str,
        budget_type: str = "month",
        is_total: bool = True,
        category: str | None = None,
    ) -> str:
        return run_service(
            lambda: budget_service.update_budget(
                user,
                amount=amount,
                budget_type=budget_type,
                period=period,
                is_total=is_total,
                category_name=category,
            ),
            ok_message="预算已更新",
        )

    return StructuredTool.from_function(
        func=update_budget,
        name="update_budget",
        description="更新预算金额或分类预算；与 create_budget 同为 upsert。",
        args_schema=UpdateBudgetInput,
    )


# ----- query_budget -----


class QueryBudgetInput(BaseModel):
    period: str = Field(..., description='预算周期，月如 "2026-03"，年如 "2026"')
    budget_type: str = Field(default="month", description="month 或 year")


def query_budget_tool(user) -> StructuredTool:
    def query_budget(period: str, budget_type: str = "month") -> str:
        return run_service(
            lambda: budget_service.query_budget(
                user, budget_type=budget_type, period=period
            ),
            ok_message="查询成功",
        )

    return StructuredTool.from_function(
        func=query_budget,
        name="query_budget",
        description="查询某周期预算总额、已花费与分类预算列表。",
        args_schema=QueryBudgetInput,
    )


def build_budget_tools(user) -> list[StructuredTool]:
    return [
        create_budget_tool(user),
        update_budget_tool(user),
        query_budget_tool(user),
    ]
