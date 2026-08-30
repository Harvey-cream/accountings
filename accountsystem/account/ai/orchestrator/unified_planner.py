"""Unified top-level planner for single, multi, and open tasks."""

from __future__ import annotations

from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field, model_validator

from account.ai.llm.llm import llm
from account.ai.llm.llm_utils import log_agent_exc, nested_structured_output

from .task_schema import WorkflowTask, WorkflowPlan, topo_sort


_MAX_SCHEMA_RETRIES = 1


class RoutePlan(BaseModel):
    tasks: list[WorkflowTask] = Field(min_length=1)
    reason: str = ""

    @model_validator(mode="after")
    def validate_tasks(self) -> "RoutePlan":
        workflow_plan = WorkflowPlan(tasks=self.tasks)
        if topo_sort(workflow_plan) is None:
            raise ValueError("route plan contains invalid dependencies")
        return self


_PLANNER_SYSTEM = """你是财务助手的统一顶层规划器。一次理解用户请求，并输出一个包含一个或多个 Task 的 Plan。

可用 Task 类型：
- bill：记账、收支、账单查询/修改/删除
- budget：预算设置、更新、查询、建议
- asset：资产账户、余额、净资产、负债
- invoice：发票抬头、税号、开票信息
- open_planning：消费统计、趋势、综合分析或开放式长期规划

规则：
1. 单域请求输出一个 Task，复合请求输出多个 Task；Task 数量决定执行规模。
2. 只有需要统计、趋势、综合推理或规划报告时才使用 open_planning Task。
3. 固定业务组合不要改成 open_planning；账单与预算同时出现时输出 bill 和 budget 两个 Task。
4. goal 只描述任务目标；input 必须放入从用户输入中明确得到的金额、描述、分类、周期等业务参数。
5. bill 的 input 使用 items 列表，每项可包含 amount、description、category、bill_type、date；budget 的 input 使用 amount、budget_type、period、category、is_total，其中月 period 必须是 YYYY-MM，年 period 必须是 YYYY，未明确时可以省略 period。
6. asset/invoice 也将用户明确提供的业务参数放入 input。input 不允许包含 user_id、数据库主键、created_at 或内部状态。
7. 只有真实存在数据依赖时才填写 depends_on；没有依赖就留空。
8. 只输出符合 schema 的结构化 Plan，不回答用户。"""


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
            messages.append(HumanMessage(content="请严格输出符合 Plan schema 的结果；tasks 至少包含一个 Task，开放分析也必须放入 open_planning Task。"))
    return None
