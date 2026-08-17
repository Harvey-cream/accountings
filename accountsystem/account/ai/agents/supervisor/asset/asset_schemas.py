"""Asset Workflow 各节点的 Pydantic 约束。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AssetIntentType = Literal["create", "query", "update", "delete", "adjust_balance"]


class AssetIntent(BaseModel):
    """资产任务分类。"""

    intent: AssetIntentType = Field(
        description=(
            "create=新建账户；query=查余额/账户列表/资产结构；update=改账户信息或覆盖余额；"
            "delete=删账户；adjust_balance=按增量加减余额"
        )
    )


class AssetLocator(BaseModel):
    """改/删/调余额前，从用户原话里抽出的账户定位条件。"""

    account_id: int | None = Field(default=None, description="用户明确报了账户编号才填")
    name: str | None = Field(default=None, description="账户名称关键词，如 招行、支付宝")


class AssetDraft(BaseModel):
    """新建账户前从用户原话里抽出的账户草稿，仅用于确认卡片展示。"""

    name: str = Field(default="", description="账户名称")
    asset_type: str = Field(default="", description="资产类型名称，如 储蓄卡、现金、信用卡")
    balance: float = Field(default=0, description="初始余额；负债账户填欠款正数")
    remark: str = Field(default="", description="备注")
