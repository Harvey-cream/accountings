"""账单 Workflow 内部的结构化输出约束（意图分类、改删前定位）。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

BillIntentType = Literal["create", "batch_create", "query", "update", "delete"]


class BillIntent(BaseModel):
    """账单任务类型。"""

    intent: BillIntentType = Field(
        description=(
            "create=记一笔新账；batch_create=一句话里要记多笔新账；"
            "query=查明细/汇总列表；update=改已有账单；delete=删已有账单"
        ),
    )
    reason: str = Field(default="", description="一句话依据，便于排查")


class BillDraft(BaseModel):
    """批量记账里的单笔草稿（不访问数据库）。"""

    amount: float = Field(description="金额，必须大于 0")
    category: str = Field(default="其他", description="分类名称，如 餐饮、交通")
    date: str | None = Field(default=None, description="日期 YYYY-MM-DD，用户没说就留空")
    description: str = Field(default="", description="备注，如 早饭、午饭")
    bill_type: str = Field(default="expense", description="expense/income，默认 expense")


class BillBatch(BaseModel):
    """从一句话里拆出的多笔账单草稿。"""

    items: list[BillDraft] = Field(default_factory=list, description="按用户原话顺序排列")


class BillLocator(BaseModel):
    """从用户口语里抽出定位账单的检索条件（不访问数据库）。"""

    bill_id: int | None = Field(default=None, description="用户明确说出的账单编号，没有就留空")
    keyword: str | None = Field(default=None, description="备注关键词，如 星巴克、打车")
    category: str | None = Field(default=None, description="分类名称，如 餐饮、交通")
    days: int = Field(default=30, ge=1, le=365, description="回溯天数，默认 30")
    bill_type: str | None = Field(default=None, description="expense/income，不确定就留空")
