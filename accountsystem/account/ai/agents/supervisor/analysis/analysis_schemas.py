"""分析 Workflow 内部结构化输出约束。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AnalysisIntentType = Literal["summary", "category", "compare"]


class AnalysisIntent(BaseModel):
    intent: AnalysisIntentType = Field(
        description=(
            "summary=整体收支汇总；category=按分类统计；"
            "compare=两段时期对比（比上周/上月怎样）"
        ),
    )
    reason: str = Field(default="", description="一句话依据")


class AnalysisParams(BaseModel):
    """归一化后的分析参数。工具层只认 days/category，日期区间仅作展示标签。"""

    days: int = Field(default=30, ge=1, le=365, description="回溯天数，映射到现有 Tool")
    category: str | None = Field(default=None, description="分类名，如餐饮；无则留空")
    period_label: str = Field(default="", description="口语时段标签，如本月、近7天")
    start_date: str | None = Field(default=None, description="可选展示用 YYYY-MM-DD")
    end_date: str | None = Field(default=None, description="可选展示用 YYYY-MM-DD")
    need_input: bool = Field(default=False, description="参数不足需追问时为 True")
    ask_message: str = Field(default="", description="追问文案")
