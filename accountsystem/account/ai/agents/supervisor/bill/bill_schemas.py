"""账单 Workflow 内部的结构化输出约束（意图分类、改删前定位）。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

BillIntentType = Literal["create", "query", "update", "delete"]


class BillIntent(BaseModel):
    """账单任务类型。"""

    intent: BillIntentType = Field(
        description="create=记一笔新账；query=查明细/汇总列表；update=改已有账单；delete=删已有账单",
    )
    reason: str = Field(default="", description="一句话依据，便于排查")


class BillLocator(BaseModel):
    """从用户口语里抽出定位账单的检索条件（不访问数据库）。"""

    bill_id: int | None = Field(default=None, description="用户明确说出的账单编号，没有就留空")
    keyword: str | None = Field(default=None, description="备注关键词，如 星巴克、打车")
    category: str | None = Field(default=None, description="分类名称，如 餐饮、交通")
    days: int = Field(default=30, ge=1, le=365, description="回溯天数，默认 30")
    bill_type: str | None = Field(default=None, description="expense/income，不确定就留空")
