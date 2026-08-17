"""Invoice Workflow 各节点的 Pydantic 约束。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

InvoiceIntentType = Literal["create", "query", "update", "delete"]


class InvoiceIntent(BaseModel):
    """发票任务分类。"""

    intent: InvoiceIntentType = Field(
        description=(
            "create=保存新的发票抬头；query=查抬头/税号/开票信息；"
            "update=修改已保存的抬头信息；delete=删除某条抬头"
        )
    )


class InvoiceLocator(BaseModel):
    """改/删前，从用户原话里抽出的发票定位条件。"""

    invoice_id: int | None = Field(default=None, description="用户明确报了编号才填")
    keyword: str | None = Field(default=None, description="抬头名称或税号关键词")
