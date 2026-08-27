"""Unified top-level planner for single, multi, and open tasks."""

from __future__ import annotations

from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field, model_validator

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import log_agent_exc, nested_structured_output

from .task_schema import WorkflowTask, WorkflowPlan, topo_sort

RouteMode = Literal["single", "multi", "open_planning"]
_MAX_SCHEMA_RETRIES = 1


class RoutePlan(BaseModel):
    mode: RouteMode
    tasks: list[WorkflowTask] = Field(default_factory=list)
    reason: str = ""

    @model_validator(mode="after")
    def validate_mode(self) -> "RoutePlan":
        if self.mode == "single" and len(self.tasks) != 1:
            raise ValueError("single route plans require exactly one task")
        if self.mode == "multi" and len(self.tasks) < 2:
            raise ValueError("multi route plans require at least two tasks")
        if self.mode == "open_planning" and self.tasks:
            raise ValueError("open planning route plans cannot contain workflow tasks")
        if self.mode != "open_planning":
            plan = WorkflowPlan(tasks=self.tasks)
            if topo_sort(plan) is None:
                raise ValueError("route plan contains invalid dependencies")
        return self


_PLANNER_SYSTEM = """你是财务助手的统一顶层规划器。一次理解用户请求，并输出 RoutePlan。

可用固定业务 Workflow：
- bill：记账、收支、账单查询/修改/删除
- budget：预算设置、更新、查询、建议
- asset：资产账户、余额、净资产、负债
- invoice：发票抬头、税号、开票信息

输出模式：
- single：只涉及一个固定业务任务，tasks 必须有且只有一个任务
- multi：同时涉及两个或以上固定业务任务，tasks 至少两个任务
- open_planning：消费统计、趋势、综合分析或开放式长期规划，tasks 必须为空

规则：
1. 一次记多笔账仍是一个 bill task；账单与预算同时出现必须是 multi。
2. 固定业务组合优先输出 multi，不要误判为 open_planning。
3. 只有需要统计、趋势、综合推理或规划报告时才输出 open_planning。
4. 每个 task.goal 必须自包含，包含金额、分类、时间等必要信息。
5. 只有真实存在数据依赖时才填写 depends_on；没有依赖就留空。
6. 只输出符合 schema 的结构化结果，不回答用户。"""


def build_route_plan(user_input: str, context: str = "") -> RoutePlan | None:
    human = f"用户请求：{user_input or ''}"
    if context:
        human = f"近期对话上下文：\n{context}\n\n{human}"
    planner = nested_structured_output(llm, RoutePlan)
    messages = [SystemMessage(content=_PLANNER_SYSTEM), HumanMessage(content=human)]
    for attempt in range(_MAX_SCHEMA_RETRIES + 1):
        try:
            result = planner.invoke(messages)
            if isinstance(result, RoutePlan):
                return result
            if hasattr(result, "model_dump"):
                return RoutePlan.model_validate(result.model_dump())
        except Exception as exc:
            log_agent_exc("UNIFIED_PLANNER", exc, input=(user_input or "")[:60], attempt=attempt)
        if attempt < _MAX_SCHEMA_RETRIES:
            messages.append(HumanMessage(content="请严格输出符合 RoutePlan schema 的结果；open_planning 的 tasks 必须为空。"))
    return None
