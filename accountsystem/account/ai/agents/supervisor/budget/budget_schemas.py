"""预算 Workflow 内部结构化输出约束。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

BudgetIntentType = Literal["set_budget", "query_budget", "budget_advice"]


class BudgetIntent(BaseModel):
    intent: BudgetIntentType = Field(
        description=(
            "set_budget=设置/修改预算；query_budget=查询预算与花费；"
            "budget_advice=预算够不够/还剩多少建议"
        ),
    )
    reason: str = Field(default="", description="一句话依据")


class BudgetParams(BaseModel):
    """从用户话抽出的预算参数（尚未做规则校验）。"""

    amount: float | None = Field(default=None, description="预算金额；查询/建议可留空")
    period: str | None = Field(
        default=None,
        description='周期：月 "YYYY-MM"，年 "YYYY"；本月/今年需换成具体值',
    )
    budget_type: str | None = Field(
        default=None, description="month 或 year；本月→month，今年→year"
    )
    is_total: bool = Field(
        default=True,
        description="True=总预算；False=分类预算（须有 category）",
    )
    category: str | None = Field(default=None, description="分类预算时的分类名")
