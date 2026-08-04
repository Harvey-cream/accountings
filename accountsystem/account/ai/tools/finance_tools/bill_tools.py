"""账单 Tools → expense_service。每个 Tool 独立定义。"""

from __future__ import annotations

from datetime import date, datetime

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from account.services import expense_service

from .common import run_service


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


# ----- create_bill -----


class CreateBillInput(BaseModel):
    amount: float = Field(..., gt=0, description="金额，必须大于 0")
    category: str = Field(default="其他", description="分类名称，如餐饮、交通")
    date: str | None = Field(default=None, description="日期 YYYY-MM-DD，缺省为今天")
    description: str = Field(default="", description="备注说明")
    bill_type: str = Field(
        default="expense",
        description="类型：expense/income 或 支出/收入，默认支出",
    )


def create_bill_tool(user) -> StructuredTool:
    def create_bill(
        amount: float,
        category: str = "其他",
        date: str | None = None,
        description: str = "",
        bill_type: str = "expense",
    ) -> str:
        return run_service(
            lambda: expense_service.create_expense(
                user,
                amount=amount,
                bill_type=bill_type,
                category_name=category,
                remark=description or "",
                obs_date=_parse_date(date),
            ),
            ok_message="账单已创建",
        )

    return StructuredTool.from_function(
        func=create_bill,
        name="create_bill",
        description="创建一笔收支账单。用户明确金额与消费/收入时使用。",
        args_schema=CreateBillInput,
    )


# ----- update_bill -----


class UpdateBillInput(BaseModel):
    bill_id: int = Field(..., description="要修改的账单 ID")
    amount: float | None = Field(default=None, gt=0, description="新金额，可选")
    category: str | None = Field(default=None, description="新分类名称，可选")
    date: str | None = Field(default=None, description="新日期 YYYY-MM-DD，可选")
    description: str | None = Field(default=None, description="新备注，可选")
    bill_type: str | None = Field(
        default=None, description="expense/income 或 支出/收入，可选"
    )


def update_bill_tool(user) -> StructuredTool:
    def update_bill(
        bill_id: int,
        amount: float | None = None,
        category: str | None = None,
        date: str | None = None,
        description: str | None = None,
        bill_type: str | None = None,
    ) -> str:
        return run_service(
            lambda: expense_service.update_expense(
                user,
                bill_id,
                amount=amount,
                bill_type=bill_type,
                category_name=category,
                remark=description,
                obs_date=_parse_date(date),
            ),
            ok_message="账单已更新",
        )

    return StructuredTool.from_function(
        func=update_bill,
        name="update_bill",
        description="按账单 ID 修改已有账单的金额、分类、日期或备注。",
        args_schema=UpdateBillInput,
    )


# ----- query_bills -----


class QueryBillInput(BaseModel):
    days: int = Field(default=30, ge=1, le=365, description="查询最近多少天，默认 30")
    bill_type: str | None = Field(
        default=None, description="可选过滤：expense/income；不传则全部"
    )
    limit: int = Field(default=50, ge=1, le=200, description="最多返回条数")


def query_bills_tool(user) -> StructuredTool:
    def query_bills(
        days: int = 30,
        bill_type: str | None = None,
        limit: int = 50,
    ) -> str:
        return run_service(
            lambda: expense_service.query_expense(
                user, days=days, bill_type=bill_type, limit=limit
            ),
            ok_message="查询成功",
        )

    return StructuredTool.from_function(
        func=query_bills,
        name="query_bills",
        description="查询用户最近若干天的账单明细列表。",
        args_schema=QueryBillInput,
    )


def build_bill_tools(user) -> list[StructuredTool]:
    return [
        create_bill_tool(user),
        update_bill_tool(user),
        query_bills_tool(user),
    ]
