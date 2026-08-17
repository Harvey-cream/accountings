"""Supervisor 路由决策的 Pydantic 约束。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

TaskType = Literal["bill", "budget", "asset", "invoice"]


class RouteDecision(BaseModel):
    """把用户请求路由到某个业务 Agent。"""

    task_type: TaskType = Field(
        description=(
            "业务域：bill=记账/查账单/改账单；budget=预算管理；"
            "asset=资产账户与余额；invoice=发票抬头信息"
        ),
    )
    reason: str = Field(default="", description="一句话说明分类依据，便于排查")
