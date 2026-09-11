"""Response Composer：把已完成的 PlanResult 转成用户可读的最终回复。

确定性处理，不调用 LLM，不是 Agent / Router / Planner。
职责：把已有 Task Result（StepResult.message/summary）按执行序组合成一句最终回复；
单任务直接返回其文案；多任务用顿号拼接去重。
"""

from __future__ import annotations

from .result_aggregator import PlanResult


def _step_text(step) -> str:
    """单个 StepResult → 一句话。优先已有 message/summary；空文案时做结构化兜底。"""
    text = (step.summary or step.message or "").strip()
    if text:
        return text
    data = step.data or {}
    if step.step_type == "bill" and data.get("count") is not None and data.get("total") is not None:
        return f"最近共 {data['count']} 笔账单，总支出 {data['total']} 元。"
    return ""


def compose_response(plan_result) -> str:
    """组合已完成 Task 的回复。单任务直接返回；多任务按执行序拼接去重。"""
    parts: list[str] = []
    for step in plan_result.task_results:
        text = _step_text(step)
        if text and text not in parts:
            parts.append(text)
    if len(parts) == 1:
        return parts[0]
    if parts:
        return "、".join(parts)
    return (plan_result.summary or "").strip()
