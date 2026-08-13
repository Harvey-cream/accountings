"""Finance Planner Crew 的统一输出结构。

Crew 产出后由 crew.py 归一为 {output, intermediate_steps}，再交回 orchestrator。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CrewResult(BaseModel):
    """开放式规划任务的结构化结果。"""

    task_type: str = Field(default="open_planning", description="固定为 open_planning")
    summary: str = Field(default="", description="一句话总体结论")
    analysis: list[str] = Field(default_factory=list, description="消费/财务分析要点")
    suggestions: list[str] = Field(default_factory=list, description="可执行的规划建议")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="结论置信度 0~1")
